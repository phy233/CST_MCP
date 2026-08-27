"""run-probe-phase 副本护栏的离线单测（全部打桩，不触 CST）。

覆盖 P0-2 行为：
- main-file-only 复制语义与 probe_copy_mode 留痕；
- 固定名残留（旧主文件 + 旧解包目录）复制前清理；
- 源工程 companion 存在 .lok 时拒绝执行；
- DOE 参数名在源工程参数表中缺失时的快速失败。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cst_runtime.cli.pipelines import impl as probe_impl


SOURCE_PARAMS = {
    "parameters": [
        {"name": "R", "expr": "0.3", "value": "0.3", "descr": ""},
        {"name": "g", "expr": "20", "value": "20", "descr": ""},
    ]
}


def _make_source_project(tmp_path: Path) -> Path:
    """伪造 working.cst 主文件 + companion Model/Parameters.json。"""
    projects = tmp_path / "projects"
    projects.mkdir(parents=True, exist_ok=True)
    source = projects / "working.cst"
    source.write_bytes(b"fake-cst-archive")
    model_dir = projects / "working" / "Model"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "Parameters.json").write_text(
        json.dumps(SOURCE_PARAMS), encoding="utf-8"
    )
    return source


@pytest.fixture()
def stubbed_pipeline(monkeypatch):
    """打桩 DOE、仿真链路与 study 注入；记录调用轨迹。"""
    calls: dict[str, list] = {"prepare": [], "simulate": [], "add_trials": []}

    def fake_design_probes(parameters, max_probes=12, include_center=True):
        names = sorted(parameters)
        first = next(iter(parameters))
        probe = {name: float(parameters[name]["min"]) for name in names}
        return {
            "status": "success",
            "probes": [probe],
            "parameters": names,
        }

    def fake_analyze_probes(param_names, simulated):
        return {
            "mean_value": simulated and sum(s["value"] for s in simulated) / len(simulated),
            "main_effects": {},
            "main_effects_normalized": {},
            "interactions": {},
            "top_params": [],
        }

    def fake_prepare(project_path, param_name="", param_value=0, names=None, values=None):
        calls["prepare"].append({"path": project_path, "names": names})
        return {
            "status": "success",
            "pipeline": "prepare-experiment",
            "changed": {},
            "param_names": names,
            "param_values": values,
        }

    def fake_simulate(project_path, completion_result_paths):
        calls["simulate"].append({"path": project_path})
        return {
            "status": "success",
            "run_id": 11,
            "completion_result_paths": list(completion_result_paths),
            "s11_metric": None,
            "result_metrics": [
                {
                    "result_path": completion_result_paths[0],
                    "run_id": 11,
                    "point_count": 1,
                    "xdata": [10.0],
                    "ydata": [{"real": 0.0, "imag": 1.0}],
                }
            ],
        }

    def fake_add_trials(storage_path, study_name, trials):
        calls["add_trials"].append({"storage": storage_path, "trials": trials})
        return {"status": "success", "trials_added": len(trials)}

    from cst_runtime.lib import doe as doe_mod
    from cst_runtime.lib import optimization as opt_mod

    monkeypatch.setattr(doe_mod, "design_probes", fake_design_probes)
    monkeypatch.setattr(doe_mod, "analyze_probes", fake_analyze_probes)
    monkeypatch.setattr(probe_impl, "pipeline_prepare_experiment", fake_prepare)
    monkeypatch.setattr(probe_impl, "pipeline_run_experiment", fake_simulate)
    monkeypatch.setattr(opt_mod, "add_trials", fake_add_trials)
    return calls


PHASE_OBJECTIVE = {
    "type": "phase_at_freq",
    "result_path": "SZmin(1),Zmax(1)",
    "freq": 10.0,
    "target_deg": 90.0,
}


class TestProbePhaseGuards:

    def test_happy_path_main_file_copy_and_fields(self, tmp_path, stubbed_pipeline):
        source = _make_source_project(tmp_path)
        result = probe_impl.pipeline_run_probe_phase(
            project_path=str(source),
            completion_result_paths=["1D Results\\S-Parameters\\SZmin(1),Zmax(1)"],
            parameters={"R": {"min": 0.2, "max": 0.4}, "g": {"min": 18, "max": 22}},
            study_storage=str(tmp_path / "studies" / "opt.db"),
            study_name="study_x",
            objective=PHASE_OBJECTIVE,
        )
        assert result["status"] == "success"
        assert result["probe_copy_mode"] == "main_file_only"
        assert result["parameter_check"] == "verified"
        assert result["cleaned_previous_artifacts"] == []
        probe_project = Path(result["probe_project"])
        assert probe_project.is_file()
        # 仅复制主文件：不主动创建 companion 目录
        assert not probe_project.with_suffix("").exists()
        # 目标值 = |wrap(90°-90°)| ≈ 0
        assert abs(result["mean_value"]) < 1e-6
        assert stubbed_pipeline["add_trials"][0]["trials"][0]["params"]["R"] == 0.2

    def test_stale_artifacts_cleaned_before_copy(self, tmp_path, stubbed_pipeline):
        source = _make_source_project(tmp_path)
        stale_file = source.parent / "working_probe.cst"
        stale_file.write_bytes(b"stale")
        stale_companion = source.parent / "working_probe"
        (stale_companion / "Model").mkdir(parents=True)
        (stale_companion / "Model" / "old.bin").write_bytes(b"old")

        result = probe_impl.pipeline_run_probe_phase(
            project_path=str(source),
            completion_result_paths=["1D Results\\S-Parameters\\SZmin(1),Zmax(1)"],
            parameters={"R": {"min": 0.2, "max": 0.4}, "g": {"min": 18, "max": 22}},
            study_storage=str(tmp_path / "opt.db"),
            study_name="study_x",
            objective=PHASE_OBJECTIVE,
        )
        assert sorted(result["cleaned_previous_artifacts"]) == [
            "working_probe",
            "working_probe.cst",
        ]
        assert not stale_companion.exists()

    def test_locked_source_refused(self, tmp_path, stubbed_pipeline):
        source = _make_source_project(tmp_path)
        lock_dir = source.parent / "working"
        (lock_dir / ".lok").mkdir(parents=True, exist_ok=True)
        (lock_dir / ".lok" / "busy.lok").write_bytes(b"")

        result = probe_impl.pipeline_run_probe_phase(
            project_path=str(source),
            completion_result_paths=["p"],
            parameters={"R": {"min": 0.2, "max": 0.4}, "g": {"min": 18, "max": 22}},
            study_storage=str(tmp_path / "opt.db"),
            study_name="study_x",
            objective=PHASE_OBJECTIVE,
        )
        assert result["status"] == "error"
        assert result["error_type"] == "probe_source_locked"
        assert result["lok_files"] == ["busy.lok"]
        assert (source.parent / "working_probe.cst").exists() is False

    def test_missing_doe_parameters_fail_fast(self, tmp_path, stubbed_pipeline):
        source = _make_source_project(tmp_path)
        result = probe_impl.pipeline_run_probe_phase(
            project_path=str(source),
            completion_result_paths=["p"],
            parameters={
                "R": {"min": 0.2, "max": 0.4},
                "q_missing": {"min": 1, "max": 2},
            },
            study_storage=str(tmp_path / "opt.db"),
            study_name="study_x",
            objective=PHASE_OBJECTIVE,
        )
        assert result["status"] == "error"
        assert result["error_type"] == "probe_parameters_missing"
        assert result["missing_parameters"] == ["q_missing"]
        assert "R" in result["known_parameters"]
        # 快速失败不应留下探针副本
        assert not (source.parent / "working_probe.cst").exists()

    def test_parameter_check_skipped_without_companion(self, tmp_path, stubbed_pipeline):
        projects = tmp_path / "solo"
        projects.mkdir()
        bare = projects / "bare.cst"
        bare.write_bytes(b"x")

        result = probe_impl.pipeline_run_probe_phase(
            project_path=str(bare),
            completion_result_paths=["p"],
            parameters={"anything": {"min": 0, "max": 1}, "g": {"min": 1, "max": 2}},
            study_storage=str(tmp_path / "opt.db"),
            study_name="study_x",
            objective={"type": "amp_at_freq", "freq": 10},
        )
        # 无 companion 无法校验：流程继续但显式声明跳过
        assert result["parameter_check"] == "skipped_source_companion_missing"
