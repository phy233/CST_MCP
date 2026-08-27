from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from ...lib.contracts import error_result as error_response
from ...lib._pipeline_support import compute_objective
from ...lib._pipeline_support import infer_category as _infer_category
from ...lib.experiments import run_experiment as pipeline_run_experiment


# ── inspect-project (file-based, no COM/DE) ──

def _read_parameters_from_file(project_path: str) -> tuple[dict[str, Any], int]:
    """Read parameters from Model/Parameters.json on disk."""
    import json
    import re
    from pathlib import Path
    from ...lib._pipeline_support import abs_project_path

    def _is_plain_number(expr: str) -> bool:
        stripped = expr.strip()
        if not stripped:
            return False
        return bool(re.fullmatch(r'-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?', stripped))

    normalized = abs_project_path(project_path)
    pdir = Path(normalized).with_suffix("")
    params_json = pdir / "Model" / "Parameters.json"
    params: dict[str, Any] = {}
    if not params_json.is_file():
        return params, 0

    try:
        pdata = json.loads(params_json.read_text(encoding="utf-8"))
        for entry in pdata.get("parameters", []):
            name = entry.get("name", "")
            if not name:
                continue
            expr = entry.get("expr", "")
            raw_val = entry.get("value", "")
            desc = entry.get("descr", "")
            try:
                value = float(raw_val) if raw_val else None
            except (ValueError, TypeError):
                value = None
            is_derived = not _is_plain_number(expr) if expr else False
            params[name] = {
                "value": value,
                "description": desc,
                "category": _infer_category(name),
                "expression": expr,
                "is_derived": is_derived,
            }
        derived_count = sum(1 for p in params.values() if p["is_derived"])
        return params, derived_count
    except Exception:
        return params, 0


def _read_entities_from_pir(project_path: str) -> tuple[list[dict[str, str]], int, dict[str, Any]]:
    """Read entities via core.project_info (offline). Returns (entities, count, extra_info)."""
    from ...lib._pipeline_support import read_project_info
    result = read_project_info(project_path)
    if result.get("status") == "error":
        return [], 0, {"pir_error": result.get("message", "unknown error")}
    extra: dict[str, Any] = {
        "solver_name": result.get("solver_name", ""),
        "min_frequency": result.get("min_frequency"),
        "max_frequency": result.get("max_frequency"),
        "frequency_unit": result.get("frequency_unit", ""),
        "cst_version": result.get("cst_version", ""),
    }
    return result.get("entities", []), result.get("entities_count", 0), extra


def _read_solver_from_ads(project_path: str) -> dict[str, Any]:
    """Read solver type and port count from Model/3D/Model.ads on disk."""
    from pathlib import Path
    from ...lib._pipeline_support import abs_project_path

    normalized = abs_project_path(project_path)
    ads_path = Path(normalized).with_suffix("") / "Model" / "3D" / "Model.ads"
    if not ads_path.is_file():
        return {}
    try:
        text = ads_path.read_text(encoding="utf-8")
        info: dict[str, Any] = {}
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("[") and "]" in stripped:
                key = stripped[1:stripped.index("]")]
                val = stripped[stripped.index("]") + 1:].strip()
                if key == "SOLVERTYPE":
                    info["solver_type"] = val
                elif key == "NUMBEROFPORTS":
                    try:
                        info["number_of_ports"] = int(val)
                    except (ValueError, TypeError):
                        pass
        return info
    except Exception:
        return {}


def _read_frequency_and_version_from_docstore(project_path: str) -> dict[str, Any]:
    """Read frequency range and CST version from simulationproperties.docstore."""
    from pathlib import Path
    from ...lib._pipeline_support import abs_project_path

    normalized = abs_project_path(project_path)
    doc_path = Path(normalized).with_suffix("") / "Model" / "simulationproperties.docstore"
    if not doc_path.is_file():
        return {}
    try:
        import sqlite3
        import cbor2

        db = sqlite3.connect(str(doc_path))
        blob = db.execute(
            "SELECT data FROM filestore_unchunked_data WHERE id=3"
        ).fetchone()
        db.close()
        if blob is None:
            return {}
        decoded = cbor2.loads(blob[0])

        # Navigate: !d → {!d} → root_project → {!d} → 3d_info → {!d} → value → {!d} → frequency → {!d}
        info: dict[str, Any] = {}
        payload = decoded.get("!d", {}).get("!d", {})
        try:
            freq = payload["root_project"]["!d"]["3d_info"]["!d"]["value"]["!d"]["frequency"]["!d"]
            fmin = freq.get("minimum", {}).get("!d")
            fmax = freq.get("maximum", {}).get("!d")
            if fmin is not None and fmax is not None:
                info["frequency_range_ghz"] = {"min": float(fmin), "max": float(fmax)}
        except (KeyError, TypeError):
            pass

        # CST version from common path
        try:
            ver = payload["root_project"]["!d"]["common"]["!d"]["cst_version"]["!d"]
            version_str = ver.get("full_version_string", {}).get("!d", "")
            if version_str:
                info["cst_version"] = version_str
        except (KeyError, TypeError):
            pass

        return info
    except Exception:
        return {}


def _read_entities_from_fct(project_path: str) -> tuple[list[dict[str, str]], int]:
    """Read solid entity names from Model/3D/Model.fct on disk."""
    import re
    from pathlib import Path
    from ...lib._pipeline_support import abs_project_path

    normalized = abs_project_path(project_path)
    fct_path = Path(normalized).with_suffix("") / "Model" / "3D" / "Model.fct"
    if not fct_path.is_file():
        return [], 0
    try:
        raw = fct_path.read_bytes()
        entities: list[dict[str, str]] = []
        seen: set[str] = set()
        # Names are concatenated with "solid$" delimiter
        for part in raw.split(b"solid$"):
            if not part:
                continue
            # Remove trailing null bytes / binary noise
            clean = part.rstrip(b"\x00").decode("ascii", errors="replace")
            if ":" not in clean:
                continue
            idx = clean.index(":")
            component = clean[:idx]
            name = clean[idx + 1:]
            if not name or not component:
                continue
            key = f"{component}:{name}"
            if key not in seen:
                seen.add(key)
                entities.append({"component": component, "name": name})
        return entities, len(entities)
    except Exception:
        return [], 0


def _read_farfield_monitors_from_dsn(project_path: str) -> tuple[list[str], int]:
    """Read farfield monitors from Model/3D/Model.dsn on disk."""
    import re
    from pathlib import Path
    from ...lib._pipeline_support import abs_project_path

    normalized = abs_project_path(project_path)
    dsn_path = Path(normalized).with_suffix("") / "Model" / "3D" / "Model.dsn"
    if not dsn_path.is_file():
        return [], 0
    try:
        text = dsn_path.read_text(encoding="utf-8")
        monitors: list[str] = []
        in_monitor = False
        montype = None
        monname = ""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("*** newmonitor"):
                in_monitor = True
                montype = None
                monname = ""
            elif stripped.startswith("*** endmonitor") and in_monitor:
                in_monitor = False
                if montype == 18 and monname:
                    monitors.append(monname)
            elif in_monitor:
                m = re.match(r'montype:\s*(\d+)', stripped)
                if m:
                    montype = int(m.group(1))
                m = re.match(r'monname:\s*"(.+)"', stripped)
                if m:
                    monname = m.group(1)
        return monitors, len(monitors)
    except Exception:
        return [], 0


def pipeline_inspect_project(project_path: str) -> dict[str, Any]:
    from ...lib._pipeline_support import abs_project_path

    normalized = abs_project_path(project_path)
    from pathlib import Path
    if not Path(normalized).is_file():
        return error_response(
            "project_file_missing",
            f"project_path does not exist: {normalized}",
            step="inspect-project:validate",
        )

    # Read parameters from file
    params, derived_count = _read_parameters_from_file(normalized)
    parameters_count = len(params)

    # Read entities via cst_project_info_reader (primary), fallback to file
    entities, entities_count, pir_extra = _read_entities_from_pir(normalized)
    pir_failed = bool(pir_extra.get("pir_error"))
    if pir_failed or not entities:
        file_entities, file_count = _read_entities_from_fct(normalized)
        if file_entities:
            entities = file_entities
            entities_count = file_count

    # Read solver info — PIR primary, fallback to Model.ads
    solver_info: dict[str, Any] = {}
    if pir_extra.get("solver_name"):
        solver_info["solver_name"] = pir_extra["solver_name"]
    else:
        ads_info = _read_solver_from_ads(normalized)
        if ads_info.get("solver_type"):
            solver_info["solver_type"] = ads_info["solver_type"]
        if ads_info.get("number_of_ports") is not None:
            solver_info["number_of_ports"] = ads_info["number_of_ports"]

    # Read frequency/version — PIR primary, fallback to docstore
    if pir_extra.get("min_frequency") is not None:
        solver_info["frequency_range_ghz"] = {
            "min": pir_extra["min_frequency"],
            "max": pir_extra["max_frequency"],
        }
    if pir_extra.get("cst_version"):
        solver_info["cst_version"] = pir_extra["cst_version"]
    if "frequency_range_ghz" not in solver_info or "cst_version" not in solver_info:
        doc_info = _read_frequency_and_version_from_docstore(normalized)
        if "frequency_range_ghz" not in solver_info and "frequency_range_ghz" in doc_info:
            solver_info["frequency_range_ghz"] = doc_info["frequency_range_ghz"]
        if "cst_version" not in solver_info and "cst_version" in doc_info:
            solver_info["cst_version"] = doc_info["cst_version"]

    # Read farfield monitors from Model.dsn
    ff_names, ff_count = _read_farfield_monitors_from_dsn(normalized)

    result: dict[str, Any] = {
        "status": "success",
        "pipeline": "inspect-project",
        "project_path": normalized,
        "method": "file_based",
        "parameters": params,
        "parameters_count": parameters_count,
        "entities": entities,
        "entities_count": entities_count,
        "farfield_monitors": ff_names,
        "farfield_monitors_count": ff_count,
    }
    if parameters_count > 0:
        result["derived_parameters_count"] = derived_count
    if solver_info:
        result["solver_info"] = solver_info
    if pir_failed:
        result["pir_note"] = (f"cst_project_info_reader unavailable: {pir_extra['pir_error']}"
                              " — some data from file fallback")

    return result


# ── prepare-experiment ──

def pipeline_prepare_experiment(
    project_path: str,
    param_name: str = "",
    param_value: float = 0,
    names: list[str] | None = None,
    values: list[float] | None = None,
) -> dict[str, Any]:
    from ...lib.session import open_project as sm_open, close_project as sm_close
    from ...lib.project import change_parameter, save_project

    resolved_names: list[str] = []
    resolved_values: list[float] = []
    if names and values:
        resolved_names = names
        resolved_values = values
    elif param_name:
        resolved_names = [param_name]
        resolved_values = [param_value]
    else:
        return error_response(
            "pipeline_param_missing",
            "provide param_name+param_value or names+values",
            step="prepare-experiment:validate",
        )

    if len(resolved_names) != len(resolved_values):
        return error_response(
            "pipeline_param_count_mismatch",
            f"names ({len(resolved_names)}) != values ({len(resolved_values)})",
            step="prepare-experiment:validate",
        )

    open_result = sm_open(project_path)
    if open_result.get("status") != "success":
        return open_result

    # 信任 CST：参数写入 VBA 已提交且未报错即视为已实施，不再做写后
    # 枚举回读验证（额外查询不改变成功结论，只会增加 CST 往返与历史噪声）。
    all_changed: dict[str, Any] = {}
    for n, v in zip(resolved_names, resolved_values):
        cr = change_parameter(project_path=project_path, name=n, value=v)
        if cr.get("status") != "success":
            sm_close(project_path, save=False)
            return error_response(
                "pipeline_change_param_failed",
                cr.get("message", f"failed to change {n}={v}"),
                step="prepare-experiment:change-param",
                change_result=cr,
            )
        all_changed.update(cr.get("changed", {}))

    save_result = save_project(project_path)
    if save_result.get("status") != "success":
        sm_close(project_path, save=False)
        return error_response(
            "pipeline_save_failed",
            save_result.get("message", "failed to save project"),
            step="prepare-experiment:save",
        )

    sm_close(project_path, save=False)
    return {
        "status": "success",
        "pipeline": "prepare-experiment",
        "project_path": open_result.get("project_path", project_path),
        "changed": all_changed,
        "param_names": resolved_names,
        "param_values": resolved_values,
    }


# ── run-experiment ──

# CLI pipeline 与工具共用同一个 lib 业务实现，避免形成两套可调用行为。
from ...lib.experiments import run_experiment as pipeline_run_experiment


# ── run-probe-phase ──

def pipeline_run_probe_phase(
    project_path: str,
    completion_result_paths: list[str],
    parameters: dict,
    study_storage: str,
    study_name: str,
    max_probes: int = 12,
    include_center: bool = True,
    objective: dict | None = None,
) -> dict[str, Any]:
    import shutil
    from pathlib import Path
    from ...lib import doe as _doe
    from ...lib import optimization as _opt

    p = Path(project_path).expanduser().resolve()
    if not p.is_file():
        return error_response("project_not_found", f"project not found: {p}", step="probe-phase:validate")

    probe_project = p.parent / "working_probe.cst"
    probe_companion = probe_project.with_suffix("")
    source_companion = p.with_suffix("")

    # 1a. 源工程锁拒绝：companion 目录存在 .lok 锁文件时说明工程正在被 CST 占用。
    lock_files = (
        [item for item in source_companion.rglob("*.lok") if item.is_file()]
        if source_companion.is_dir()
        else []
    )
    if lock_files:
        return error_response(
            "probe_source_locked",
            "源工程存在 .lok 锁文件；请先在 CST 中关闭该工程再运行 probe",
            step="probe-phase:validate",
            lok_files=[item.name for item in lock_files[:5]],
        )

    # 1b. 参数快速失败：基于源工程的 Parameters.json 校验 DOE 参数名，
    #     避免复制之后逐个 probe 失败才发现名字写错。
    source_parameters, _derived_count = _read_parameters_from_file(str(p))
    parameter_check = "verified"
    if source_parameters:
        absent = sorted(name for name in parameters if name not in source_parameters)
        if absent:
            return error_response(
                "probe_parameters_missing",
                f"DOE 参数不在工程参数表中: {', '.join(absent)}",
                step="probe-phase:validate",
                missing_parameters=absent,
                known_parameters=sorted(source_parameters),
            )
    else:
        parameter_check = "skipped_source_companion_missing"

    # 1c. 清理上一轮固定名残留（旧主文件与旧解包目录同名配对会遮蔽新副本）；
    #     删除范围严格限定在探针专属工件，不触碰源工程与历史 run。
    cleaned_previous: list[str] = []
    for stale_artifact in (probe_project, probe_companion):
        if stale_artifact.is_dir() and not stale_artifact.suffix:
            try:
                shutil.rmtree(str(stale_artifact))
                cleaned_previous.append(stale_artifact.name)
            except OSError as exc:
                return error_response(
                    "probe_cleanup_failed",
                    f"无法删除旧的探针 companion 目录 {stale_artifact}: {exc}",
                    step="probe-phase:cleanup",
                )
        elif stale_artifact.is_file():
            try:
                stale_artifact.unlink()
                cleaned_previous.append(stale_artifact.name)
            except OSError as exc:
                return error_response(
                    "probe_cleanup_failed",
                    f"无法删除旧的探针主文件 {stale_artifact}: {exc}",
                    step="probe-phase:cleanup",
                )

    # 1d. Copy working.cst → working_probe.cst (main-file-only isolation;
    #     CST 在首次打开裸 .cst 时自动创建 companion 工作目录).
    shutil.copy2(str(p), str(probe_project))
    probe_path = str(probe_project)

    # 2. Design probes via DOE
    design = _doe.design_probes(parameters, max_probes=max_probes, include_center=include_center)
    if design.get("status") != "success":
        return error_response("probe_design_failed",
            design.get("message", "failed to design probes"), step="probe-phase:design")

    probes = design["probes"]
    param_names = design["parameters"]

    # 3. Simulate each probe（信任 CST：求解失败即为失败，
    # 绝不从失败结果计算目标函数，原始报错文本完整保留在 failed_probes 中）
    simulated: list[dict] = []
    failed: list[dict] = []
    for probe in probes:
        names = list(probe.keys())
        values = [probe[n] for n in names]
        prep = pipeline_prepare_experiment(probe_path, names=names, values=values)
        if prep.get("status") != "success":
            failed.append({"params": probe, "error": "prepare_failed"})
            continue
        sim = pipeline_run_experiment(probe_path, completion_result_paths)
        if sim.get("status") != "success":
            failed.append(
                {
                    "params": probe,
                    "error": sim.get("error_type", "sim_failed"),
                    "message": sim.get("message", ""),
                    "cst_errors": sim.get("cst_errors", []),
                    "cst_error_lines": sim.get("cst_error_lines", []),
                    "log_files": sim.get("log_files", []),
                }
            )
            continue
        obj = compute_objective(objective or {}, sim)
        if not obj.get("error"):
            simulated.append({"params": probe, "value": obj["value"]})
        else:
            failed.append({"params": probe, "error": obj.get("error", "objective_failed")})

    # 4. Move exported files to exports/probe/
    exports_dir = p.parent.parent / "exports"
    probe_exports = exports_dir / "probe"
    probe_exports.mkdir(parents=True, exist_ok=True)

    if not simulated:
        return error_response("all_probes_failed",
            "no probe simulations produced valid results", step="probe-phase:simulate",
            n_total=len(probes), n_failed=len(failed))

    # 5. Analyze probe results
    analysis = _doe.analyze_probes(param_names, simulated)

    # 6. Inject probe results into study
    trials = [{"params": s["params"], "values": [s["value"]]} for s in simulated]
    inject = _opt.add_trials(study_storage, study_name, trials)
    trials_injected = inject.get("trials_added", 0)

    # Edge hit detection
    edge_hit: dict[str, bool] = {}
    for name, ranges in parameters.items():
        pmin = ranges.get("min", 0)
        pmax = ranges.get("max", 0)
        hits = [s for s in simulated if abs(s["params"].get(name, 0) - pmin) < 1e-9 or abs(s["params"].get(name, 0) - pmax) < 1e-9]
        edge_hit[name] = len(hits) > 0

    # Algorithm suggestion
    n_important = len(analysis.get("top_params", []))
    interactions = analysis.get("interactions", {})
    has_strong_interaction = any(v > 0.3 for v in interactions.values()) if interactions else False
    if n_important > 3 or has_strong_interaction:
        suggested_algorithm = "CMA-ES"
    else:
        suggested_algorithm = "TPE"

    return {
        "status": "success" if len(simulated) >= len(probes) / 2 else "warning",
        "pipeline": "run-probe-phase",
        "probe_copy_mode": "main_file_only",
        "parameter_check": parameter_check,
        "cleaned_previous_artifacts": cleaned_previous,
        "n_probes": len(probes),
        "n_simulated": len(simulated),
        "n_failed": len(failed),
        "failed_probes": failed,
        "mean_value": analysis.get("mean_value"),
        "main_effects": analysis.get("main_effects", {}),
        "main_effects_normalized": analysis.get("main_effects_normalized", {}),
        "interactions": analysis.get("interactions", {}),
        "top_params": analysis.get("top_params", []),
        "trials_injected": trials_injected,
        "probe_project": str(probe_project),
        "exports_dir": str(probe_exports),
        "edge_hit": edge_hit,
        "suggested_algorithm": suggested_algorithm,
    }


# ── run-optimization-step ──

def pipeline_run_optimization_step(
    project_path: str,
    completion_result_paths: list[str],
    study_storage: str,
    study_name: str,
    objective: dict | None = None,
    sampler: str | None = None,
) -> dict[str, Any]:
    from ...lib import optimization as _opt

    # 0. Switch sampler if requested
    if sampler:
        from ...lib.optimization import switch_sampler as _switch_sampler
        switch_result = _switch_sampler(study_storage, study_name, sampler)
        if switch_result.get("status") != "success":
            return error_response("switch_sampler_failed",
                switch_result.get("message", "failed to switch sampler"), step="opt-step:switch-sampler")

    # 1. Ask study for next parameter suggestion
    ask = _opt.ask_study(study_storage, study_name)
    if ask.get("status") != "success":
        return error_response("ask_study_failed",
            ask.get("message", "study may be complete"), step="opt-step:ask",
            ask_result=ask)

    trial_number = ask["trial_number"]
    params = ask.get("params", {})
    names = list(params.keys())
    values = [params[n] for n in names]

    # 2. Prepare experiment (change params, save, close)
    prep = pipeline_prepare_experiment(project_path, names=names, values=values)
    if prep.get("status") != "success":
        _opt.tell_study(study_storage, study_name, trial_number, value=0.0, state="pruned")
        return error_response("prepare_failed",
            prep.get("message", "failed to prepare experiment"), step="opt-step:prepare")

    # 3. Run simulation and export
    sim = pipeline_run_experiment(project_path, completion_result_paths)
    if sim.get("status") != "success":
        # 信任 CST：求解未成功即为失败，绝不从失败结果计算目标函数；
        # 原始报错文本完整透传给调用方，避免错误只在 study 内部消失。
        _opt.tell_study(study_storage, study_name, trial_number, value=0.0, state="pruned")
        return error_response(
            "simulation_failed",
            sim.get("message", "simulation did not complete"),
            step="opt-step:simulate",
            sim_error_type=sim.get("error_type"),
            cst_errors=sim.get("cst_errors", []),
            cst_error_lines=sim.get("cst_error_lines", []),
            log_files=sim.get("log_files", []),
            solver_log_tails=sim.get("solver_log_tails", {}),
        )

    # 4. Compute objective
    obj = compute_objective(objective or {}, sim)
    if obj.get("error"):
        _opt.tell_study(study_storage, study_name, trial_number, value=0.0, state="pruned")
        return error_response("objective_failed",
            obj["error"], step="opt-step:objective", objective_result=obj)

    objective_value = obj["value"]

    # 5. Tell study the result
    _opt.tell_study(study_storage, study_name, trial_number, value=objective_value)

    # 6. Read current best
    best = _opt.best_study(study_storage, study_name)
    study_best = None
    if best.get("best_value") is not None:
        study_best = {"value": best["best_value"], "params": best.get("best_params")}

    # 7. Compute steps since improvement
    steps_since_improvement = 0
    trial_num = trial_number or 0
    best_trial_num = best.get("best_trial_number")
    if best_trial_num is not None:
        steps_since_improvement = trial_num - best_trial_num

    return {
        "status": "success",
        "pipeline": "run-optimization-step",
        "trial_id": trial_number,
        "params_used": params,
        "objective_value": objective_value,
        "s11_metric": sim.get("s11_metric"),
        "study_best": study_best,
        "steps_since_improvement": steps_since_improvement,
    }
