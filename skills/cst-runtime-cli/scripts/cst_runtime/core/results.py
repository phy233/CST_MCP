from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path
from typing import Any

from .errors import UnsupportedFeatureError, error_response
from .identity import attach_expected_project
from .compatibility import result_item_exists as compatibility_result_item_exists


def result_item_exists(project_path: str, treepath: str) -> dict[str, Any]:
    """通过 core 兼容边界查询结果树节点是否存在。"""
    project, status = attach_expected_project(project_path)
    if project is None:
        return status
    try:
        exists = compatibility_result_item_exists(project, treepath)
        return {
            "status": "success",
            "project_path": project_path,
            "treepath": treepath,
            "exists": exists,
            "runtime_module": "cst_runtime.core.results",
        }
    except Exception as exc:
        return error_response(
            "result_tree_query_failed",
            str(exc),
            project_path=project_path,
            treepath=treepath,
            runtime_module="cst_runtime.core.results",
        )
from .utils import serialize_value as _serialize_value
from .compatibility import get_result2d_item, get_colormap_items, list_all_result_items


def _load_project(project_path: str, allow_interactive: bool = False, subproject_treepath: str = "") -> tuple[Any, dict[str, Any]]:
    import cst.results

    fullpath = str(Path(project_path).expanduser().resolve())
    project = cst.results.ProjectFile(fullpath, allow_interactive=allow_interactive)
    active_subproject = subproject_treepath or None
    if active_subproject:
        project = project.load_subproject(active_subproject)
    return project, {
        "fullpath": fullpath,
        "active_subproject": active_subproject,
        "allow_interactive": allow_interactive,
    }


def _get_result_module(project: Any, module_type: str) -> tuple[Any, str]:
    module_key = (module_type or "3d").lower()
    if module_key == "schematic":
        return project.get_schematic(), "schematic"
    return project.get_3d(), "3d"


def _canonical_run_ids(run_ids: Any) -> list[int]:
    """规范化 Run ID；仅在存在其他编号时把 0 视为最新结果别名。"""
    normalized = sorted({int(run_id) for run_id in run_ids})
    if not normalized:
        raise RuntimeError("结果节点没有可用的 Run ID")
    nonzero = [run_id for run_id in normalized if run_id != 0]
    return nonzero or [0]


def _latest_available_run_id(run_ids: Any) -> int:
    """选择最新可用结果；非参数化仿真的唯一真实 ID 可以是 0。"""
    return _canonical_run_ids(run_ids)[-1]


def _resolve_run_id(
    result_module: Any,
    requested_run_id: int,
    *,
    treepath: str = "",
) -> int:
    """解析 run_id=0；它既可能是别名，也可能是非参数化结果的真实 ID。"""
    requested = int(requested_run_id)
    if requested != 0:
        return requested
    if treepath:
        run_ids = result_module.get_run_ids(treepath, skip_nonparametric=False)
    else:
        run_ids = result_module.get_all_run_ids(max_mesh_passes_only=True)
    return _latest_available_run_id(run_ids)


def get_version_info() -> dict[str, Any]:
    try:
        import cst.results

        return {
            "status": "success",
            "version_info": _serialize_value(cst.results.get_version_info()),
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "get_version_info_failed",
            str(exc),
            runtime_module="cst_runtime.results",
        )


def open_project(project_path: str, allow_interactive: bool = False, subproject_treepath: str = "") -> dict[str, Any]:
    try:
        path = Path(project_path).expanduser().resolve()
        if not path.is_file():
            return error_response(
                "project_file_missing",
                "project_path does not exist",
                project_path=path.as_posix(),
                runtime_module="cst_runtime.results",
            )
        project, context = _load_project(path.as_posix(), allow_interactive, subproject_treepath)
        return {
            "status": "success",
            "fullpath": context["fullpath"],
            "filename": project.filename,
            "allow_interactive": allow_interactive,
            "active_subproject": context["active_subproject"],
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "open_results_project_failed",
            str(exc),
            project_path=str(project_path),
            runtime_module="cst_runtime.results",
        )


def list_subprojects(project_path: str, allow_interactive: bool = False) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive)
        subprojects = project.list_subprojects()
        return {
            "status": "success",
            "project_path": context["fullpath"],
            "count": len(subprojects),
            "subprojects": _serialize_value(subprojects),
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "list_subprojects_failed",
            str(exc),
            project_path=str(project_path),
            runtime_module="cst_runtime.results",
        )


def list_result_items(
    project_path: str,
    module_type: str = "3d",
    filter_type: str = "0D/1D",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive, subproject_treepath)
        result_module, normalized_module = _get_result_module(project, module_type)
        normalized_filter = (filter_type or "0D/1D").strip()
        if normalized_filter.lower() == "all":
            items = list_all_result_items(result_module)
        else:
            items = [str(item) for item in result_module.get_tree_items(filter=normalized_filter)]
        return {
            "status": "success",
            "project_path": context["fullpath"],
            "module_type": normalized_module,
            "filter_type": normalized_filter,
            "active_subproject": context["active_subproject"],
            "count": len(items),
            "items": items,
            "runtime_module": "cst_runtime.results",
        }
    except UnsupportedFeatureError as exc:
        return exc.to_response(project_path=str(project_path))
    except Exception as exc:
        return error_response(
            "list_result_items_failed",
            str(exc),
            project_path=str(project_path),
            runtime_module="cst_runtime.results",
        )


def list_run_ids(
    project_path: str,
    treepath: str = "",
    module_type: str = "3d",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
    skip_nonparametric: bool = False,
    max_mesh_passes_only: bool = True,
) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive, subproject_treepath)
        result_module, normalized_module = _get_result_module(project, module_type)
        if treepath:
            run_ids = result_module.get_run_ids(treepath, skip_nonparametric=skip_nonparametric)
        else:
            run_ids = result_module.get_all_run_ids(max_mesh_passes_only=max_mesh_passes_only)
        return {
            "status": "success",
            "project_path": context["fullpath"],
            "module_type": normalized_module,
            "active_subproject": context["active_subproject"],
            "treepath": treepath or None,
            "count": len(run_ids),
            "run_ids": _serialize_value(run_ids),
            "runtime_module": "cst_runtime.results",
        }
    except UnsupportedFeatureError as exc:
        return exc.to_response(project_path=str(project_path), treepath=treepath)
    except Exception as exc:
        return error_response(
            "list_run_ids_failed",
            str(exc),
            project_path=str(project_path),
            runtime_module="cst_runtime.results",
        )


def get_parameter_combination(
    project_path: str,
    run_id: int,
    module_type: str = "3d",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive, subproject_treepath)
        result_module, normalized_module = _get_result_module(project, module_type)
        resolved_run_id = _resolve_run_id(result_module, run_id)
        params = result_module.get_parameter_combination(resolved_run_id)
        return {
            "status": "success",
            "project_path": context["fullpath"],
            "requested_run_id": int(run_id),
            "run_id": resolved_run_id,
            "module_type": normalized_module,
            "active_subproject": context["active_subproject"],
            "parameters": _serialize_value(params),
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "get_parameter_combination_failed",
            str(exc),
            project_path=str(project_path),
            run_id=run_id,
            runtime_module="cst_runtime.results",
        )


def get_1d_result(
    project_path: str,
    treepath: str,
    module_type: str = "3d",
    run_id: int = 0,
    load_impedances: bool = True,
    export_path: str = "",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive, subproject_treepath)
        result_module, normalized_module = _get_result_module(project, module_type)
        return _get_1d_result_from_module(
            result_module=result_module,
            context=context,
            normalized_module=normalized_module,
            treepath=treepath,
            run_id=run_id,
            load_impedances=load_impedances,
            export_path=export_path,
        )
    except Exception as exc:
        return error_response(
            "get_1d_result_failed",
            str(exc),
            project_path=str(project_path),
            treepath=treepath,
            run_id=run_id,
            runtime_module="cst_runtime.results",
        )


def _get_1d_result_from_module(
    *,
    result_module: Any,
    context: dict[str, Any],
    normalized_module: str,
    treepath: str,
    run_id: int,
    load_impedances: bool,
    export_path: str = "",
) -> dict[str, Any]:
    """使用已加载的结果模块读取并导出 1D 结果，避免重复打开结果工程。"""
    if export_path:
        export_file = Path(export_path).expanduser()
        if export_file.suffix.lower() != ".json":
            return error_response(
                "invalid_export_extension",
                "get_1d_result export_path only supports .json",
                export_path=str(export_file),
                runtime_module="cst_runtime.results",
            )

    requested_run_id = int(run_id)
    resolved_run_id = _resolve_run_id(
        result_module,
        requested_run_id,
        treepath=treepath,
    )
    result_item = result_module.get_result_item(
        treepath,
        run_id=resolved_run_id,
        load_impedances=load_impedances,
    )
    xdata = result_item.get_xdata()
    ydata = result_item.get_ydata()

    # 参数组合只是辅助元数据。CST 2022 对非参数化 Run 0 会在这里误报
    # “run id does not exist: 0”，但曲线数据本身已经成功读取。
    parameter_combination: Any = {}
    parameter_combination_warning: str | None = None
    try:
        parameter_combination = _serialize_value(result_item.get_parameter_combination())
    except Exception as exc:
        parameter_combination_warning = str(exc)

    if export_path:
        export_file.parent.mkdir(parents=True, exist_ok=True)
        export_file = export_file.resolve()
    else:
        export_file = (
            Path(context["fullpath"]).parent.parent
            / "exports"
            / f"s11_run{resolved_run_id}.json"
        ).resolve()
        export_file.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "treepath": result_item.treepath,
        "title": result_item.title,
        "xlabel": result_item.xlabel,
        "ylabel": result_item.ylabel,
        "length": result_item.length,
        "requested_run_id": requested_run_id,
        "run_id": result_item.run_id,
        "parameter_combination": parameter_combination,
        "parameter_combination_available": parameter_combination_warning is None,
        "xdata": _serialize_value(xdata),
        "ydata": _serialize_value(ydata),
    }
    if parameter_combination_warning:
        payload["parameter_combination_warning"] = parameter_combination_warning
    export_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "status": "success",
        "mode": "local_export_only",
        "project_path": context["fullpath"],
        "module_type": normalized_module,
        "active_subproject": context.get("active_subproject"),
        "treepath": result_item.treepath,
        "requested_run_id": requested_run_id,
        "run_id": result_item.run_id,
        "point_count": len(xdata),
        "export_path": str(export_file),
        "runtime_module": "cst_runtime.results",
    }
    if parameter_combination_warning:
        result["parameter_combination_warning"] = parameter_combination_warning
    return result


def get_2d_result(
    project_path: str,
    treepath: str,
    module_type: str = "3d",
    export_path: str = "",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
    include_data: bool = False,
) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive, subproject_treepath)
        result_module, normalized_module = _get_result_module(project, module_type)
        result_2d = get_result2d_item(result_module, treepath)
        if export_path:
            export_file = Path(export_path).expanduser()
            if export_file.suffix.lower() != ".json":
                return error_response(
                    "invalid_export_extension",
                    "get_2d_result export_path only supports .json",
                    export_path=str(export_file),
                    runtime_module="cst_runtime.results",
                )
            export_file.parent.mkdir(parents=True, exist_ok=True)
            export_file = export_file.resolve()
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            export_file = (
                Path(context["fullpath"]).parent.parent
                / "exports"
                / f"result_2d_{result_2d.ny}x{result_2d.nx}_{timestamp}.json"
            ).resolve()
            export_file.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "treepath": treepath,
            "title": result_2d.title,
            "xlabel": result_2d.xlabel,
            "ylabel": result_2d.ylabel,
            "xunit": result_2d.xunit,
            "yunit": result_2d.yunit,
            "dataunit": result_2d.dataunit,
            "xmin": result_2d.xmin,
            "xmax": result_2d.xmax,
            "ymin": result_2d.ymin,
            "ymax": result_2d.ymax,
            "nx": result_2d.nx,
            "ny": result_2d.ny,
            "xpositions": _serialize_value(result_2d.get_xpositions()),
            "ypositions": _serialize_value(result_2d.get_ypositions()),
            "data": _serialize_value(result_2d.get_data()),
        }
        export_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "status": "success",
            "mode": "local_export_only",
            "project_path": context["fullpath"],
            "module_type": normalized_module,
            "active_subproject": context["active_subproject"],
            "treepath": treepath,
            "nx": result_2d.nx,
            "ny": result_2d.ny,
            "export_path": str(export_file),
            "include_data_ignored": bool(include_data),
            "runtime_module": "cst_runtime.results",
        }
    except UnsupportedFeatureError as exc:
        return exc.to_response(project_path=str(project_path), treepath=treepath)
    except Exception as exc:
        return error_response(
            "get_2d_result_failed",
            str(exc),
            project_path=str(project_path),
            treepath=treepath,
            runtime_module="cst_runtime.results",
        )


def plot_project_result(
    project_path: str,
    treepath: str,
    module_type: str = "3d",
    run_id: int = 0,
    load_impedances: bool = True,
    output_html: str = "",
    page_title: str = "",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
    result_kind: str = "auto",
    intermediate_json: str = "",
) -> dict[str, Any]:
    try:
        if not treepath:
            return error_response("treepath_missing", "treepath is required")
        output_target = Path(output_html).expanduser().resolve() if output_html else None
        if intermediate_json:
            export_path = Path(intermediate_json).expanduser().resolve()
        elif output_target is not None:
            export_path = output_target.with_suffix(".json")
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            export_path = Path(project_path).expanduser().resolve().parent.parent / "exports" / f"project_result_{timestamp}.json"
        export_path.parent.mkdir(parents=True, exist_ok=True)

        normalized_kind = (result_kind or "auto").strip().lower()
        attempts: list[tuple[str, dict[str, Any]]] = []
        if normalized_kind in {"auto", "1d", "0d/1d", "0d1d"}:
            attempts.append(
                (
                    "1d",
                    get_1d_result(
                        project_path=project_path,
                        treepath=treepath,
                        module_type=module_type,
                        run_id=run_id,
                        load_impedances=load_impedances,
                        export_path=str(export_path),
                        allow_interactive=allow_interactive,
                        subproject_treepath=subproject_treepath,
                    ),
                )
            )
        if normalized_kind in {"auto", "2d"} and (not attempts or attempts[-1][1].get("status") != "success"):
            attempts.append(
                (
                    "2d",
                    get_2d_result(
                        project_path=project_path,
                        treepath=treepath,
                        module_type=module_type,
                        export_path=str(export_path),
                        allow_interactive=allow_interactive,
                        subproject_treepath=subproject_treepath,
                    ),
                )
            )
        success = next(((kind, result) for kind, result in attempts if result.get("status") == "success"), None)
        if success is None:
            return error_response(
                "plot_project_result_export_failed",
                "could not export project result as 1D or 2D JSON",
                attempts=attempts,
                runtime_module="cst_runtime.results",
            )
        detected_kind, export_result = success
        from ..render.dashboard import plot_exported_file as _plot_exported
        plot_result = _plot_exported(
            file_path=str(export_path),
            output_html=str(output_target or ""),
            page_title=page_title or f"CST Result Preview - {treepath}",
        )
        if plot_result.get("status") != "success":
            return plot_result
        return {
            **plot_result,
            "source": "project_result",
            "detected_kind": detected_kind,
            "project_path": str(Path(project_path).expanduser().resolve()),
            "treepath": treepath,
            "run_id": run_id,
            "module_type": module_type,
            "intermediate_json": str(export_path),
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "plot_project_result_failed",
            str(exc),
            project_path=str(project_path),
            treepath=treepath,
            runtime_module="cst_runtime.results",
        )


def _extract_farfield_freq(name: str) -> str:
    m = re.search(r"f\s*[=\uff1d]\s*(\d+(?:\.\d+)?)", name)
    if m:
        return m.group(1)
    m = re.search(r"(\d+(?:\.\d+)?)\s*GHz", name, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


def _discover_farfield_names_from_result_module(result_module: Any) -> list[str]:
    """从已加载的离线结果树发现远场结果，避免为查询树节点启动 GUI。"""
    discovered: list[str] = []
    for item in list_all_result_items(result_module):
        tree_path = str(item)
        low = tree_path.lower()
        if "farfields" not in low or "\\farfield" not in low or "cut" in low:
            continue
        short_name = tree_path.rsplit("\\", 1)[-1]
        if short_name.strip() and short_name not in discovered:
            discovered.append(short_name)
    return discovered


def export_run_results(
    project_path: str,
    farfield_names: list[str] | None = None,
    farfield_plot_mode: str = "Realized Gain",
    farfield_theta_step: float = 2.0,
    farfield_phi_step: float = 2.0,
    run_id: int | None = None,
) -> dict[str, Any]:
    try:
        p = Path(project_path).expanduser().resolve()
        if not p.is_file():
            return error_response("project_not_found", "project_path is not a file", project_path=str(p))

        exports_dir = p.parent.parent / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        exported: list[str] = []

        # 工程关闭后采用离线结果读取，避免让交互模式重新关联或拉起 CST 界面。
        latest_run_id: int | None = None
        proj2, ctx2 = _load_project(str(p), allow_interactive=False)
        m3d2 = proj2.get_3d()
        all_rids = m3d2.get_all_run_ids(max_mesh_passes_only=True)
        if all_rids:
            latest_run_id = _latest_available_run_id(all_rids)

        # 直接复用离线结果树发现远场结果，不再为一次树查询启动 GUI 工程。
        if not farfield_names:
            try:
                discovered = _discover_farfield_names_from_result_module(m3d2)
                if discovered:
                    farfield_names = discovered
            except Exception:
                pass

        if farfield_names:
            from .farfield import export_farfield_grid

            for ff_name in farfield_names:
                result = export_farfield_grid(
                    project_path=str(p),
                    farfield_name=ff_name,
                    export_dir=str(exports_dir),
                    quantity=farfield_plot_mode,
                    theta_step_deg=farfield_theta_step,
                    phi_step_deg=farfield_phi_step,
                    run_id=latest_run_id,
                )
                if result.get("status") == "success":
                    exported.append(result["output_file"])

        try:
            if run_id is not None:
                rids = [run_id]
            else:
                # 非参数化结果可能只有真实 ID 0；存在其他编号时才排除别名 0。
                rids = _canonical_run_ids(all_rids)

            for rid in rids:
                r = _get_1d_result_from_module(
                    result_module=m3d2,
                    context=ctx2,
                    normalized_module="3d",
                    treepath="1D Results\\S-Parameters\\S1,1",
                    run_id=rid,
                    load_impedances=True,
                )
                if r.get("status") == "success":
                    exported.append(r["export_path"])

            tree_items = get_colormap_items(m3d2)
            for ti in tree_items:
                try:
                    r2 = get_2d_result(project_path=str(p), treepath=ti, allow_interactive=False)
                    if r2.get("status") == "success":
                        exported.append(r2["export_path"])
                except Exception:
                    pass

        except Exception as exc:
            return error_response("results_phase_failed", str(exc), project_path=str(p))

        return {
            "status": "success",
            "exported_count": len(exported),
            "exported": exported,
            "exports_dir": str(exports_dir),
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "export_run_results_failed",
            str(exc),
            project_path=str(project_path),
            runtime_module="cst_runtime.results",
        )


def generate_report(
    data_dir: str = "",
    output_html: str = "",
    page_title: str = "",
    modules: str = "",
    split: bool = False,
) -> dict[str, Any]:
    from ..render.dashboard import generate_report as _impl
    return _impl(
        data_dir=data_dir,
        output_html=output_html,
        page_title=page_title,
        modules=modules,
        split=split,
    )


def plot_exported_file(
    file_path: str = "",
    output_html: str = "",
    page_title: str = "",
) -> dict[str, Any]:
    from ..render.dashboard import plot_exported_file as _impl
    return _impl(
        file_path=file_path,
        output_html=output_html,
        page_title=page_title,
    )
