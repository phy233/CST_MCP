"""Sweep、CrossProcess 与统一 API 的测试。"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_sweep_restores_parameters_and_serializes(monkeypatch, tmp_path) -> None:
    from cst_runtime.workflows import sweep

    restored: list[tuple[str, float]] = []
    monkeypatch.setattr(sweep, "reattach_project", lambda project_path: {"status": "success"})
    monkeypatch.setattr(sweep, "param_exists", lambda project_path, name: True)
    monkeypatch.setattr(sweep, "get_param", lambda project_path, name: 9.0)
    monkeypatch.setattr(
        sweep,
        "set_param",
        lambda project_path, name, value: restored.append((name, value)),
    )
    monkeypatch.setattr(sweep, "rebuild", lambda project_path: None)
    runner = sweep.ParameterSweep(
        project_path="model.cst",
        parameters=["width"],
        ranges=[[1.0, 2.0]],
        target_freq_ghz=8.0,
    )
    monkeypatch.setattr(
        runner,
        "_run_single_step",
        lambda params, sparam_dir, step: {
            "params": params,
            "sparams": {
                runner.result_paths[0]: {
                    "magnitude": 1.0,
                    "magnitude_db": 0.0,
                    "phase_deg": 90.0,
                    "real": 0.0,
                    "imag": 1.0,
                }
            },
        },
    )

    result = runner.run(output_dir=tmp_path)
    payload = result.to_dict()
    assert result.successful_steps == 2
    assert restored[-1] == ("width", 9.0)
    assert payload["status"] == "success"
    assert len(payload["records"]) == 2
    assert {Path(path).name for path in payload["exported_files"]} == {
        "lut.csv",
        "lut.npz",
    }


def test_sweep_can_continue_after_failure(monkeypatch, tmp_path) -> None:
    from cst_runtime.workflows import sweep

    monkeypatch.setattr(sweep, "reattach_project", lambda project_path: {"status": "success"})
    monkeypatch.setattr(sweep, "param_exists", lambda project_path, name: True)
    monkeypatch.setattr(sweep, "get_param", lambda project_path, name: 0.0)
    monkeypatch.setattr(sweep, "set_param", lambda *args, **kwargs: None)
    monkeypatch.setattr(sweep, "rebuild", lambda project_path: None)
    runner = sweep.ParameterSweep(
        project_path="model.cst",
        parameters=["width"],
        ranges=[[1.0, 2.0]],
        target_freq_ghz=8.0,
    )

    def run_step(params, sparam_dir, step):
        if step == 1:
            raise RuntimeError("测试失败")
        return {
            "params": params,
            "sparams": {
                runner.result_paths[0]: {
                    "magnitude": 1.0,
                    "magnitude_db": 0.0,
                    "phase_deg": 0.0,
                    "real": 1.0,
                    "imag": 0.0,
                }
            },
        }

    monkeypatch.setattr(runner, "_run_single_step", run_step)
    result = runner.run(output_dir=tmp_path, save_lut=False, save_csv=False)
    assert result.successful_steps == 1
    assert result.failed_steps == 1
    payload = result.to_dict()
    assert payload["status"] == "partial"
    assert payload["records"][0][f"{runner.result_paths[0].split(chr(92))[-1]}_mag"] is None


def test_sweep_records_sparameter_export(monkeypatch, tmp_path) -> None:
    from cst_runtime.workflows import sweep

    monkeypatch.setattr(
        sweep,
        "get_sparam",
        lambda project_path, result_path, **kwargs: {
            "ydata": [{"frequency": 8.0, "real": 1.0, "imag": 0.0}]
        },
    )
    runner = sweep.ParameterSweep(
        project_path="model.cst",
        parameters=["width"],
        ranges=[[1.0]],
        target_freq_ghz=8.0,
    )
    exported = runner._save_sparam_data(
        runner.result_paths[0],
        {"width": 1.0},
        tmp_path,
    )
    assert exported is not None
    assert exported.is_file()
    assert list(pd.read_csv(exported).columns) == ["frequency", "real", "imag"]


def test_sweep_rejects_unopened_project_without_side_effects(monkeypatch, tmp_path) -> None:
    from cst_runtime.lib.contracts import CSTOperationError
    from cst_runtime.workflows import sweep

    output_dir = tmp_path / "should-not-exist"
    monkeypatch.setattr(
        sweep,
        "reattach_project",
        lambda project_path: {
            "status": "error",
            "error_type": "project_not_open",
            "message": "工程未打开",
        },
    )
    monkeypatch.setattr(
        sweep,
        "param_exists",
        lambda *args: (_ for _ in ()).throw(AssertionError("不得读取参数")),
    )
    runner = sweep.ParameterSweep(
        project_path="model.cst",
        parameters=["width"],
        ranges=[[1.0]],
        target_freq_ghz=8.0,
    )

    try:
        runner.run(output_dir=output_dir)
    except CSTOperationError as exc:
        assert exc.result["error_type"] == "project_not_open"
    else:
        raise AssertionError("工程未打开时必须拒绝扫描")
    assert not output_dir.exists()


def test_sweep_normalizes_missing_session_to_project_not_open(monkeypatch) -> None:
    from cst_runtime.lib.contracts import CSTOperationError
    from cst_runtime.workflows import sweep

    monkeypatch.setattr(
        sweep,
        "reattach_project",
        lambda project_path: {
            "status": "error",
            "error_type": "no_cst_session",
            "message": "没有 CST 会话",
        },
    )
    runner = sweep.ParameterSweep(
        project_path="model.cst",
        parameters=["width"],
        ranges=[[1.0]],
        target_freq_ghz=8.0,
    )

    try:
        runner._require_open_project()
    except CSTOperationError as exc:
        assert exc.result["error_type"] == "project_not_open"
        assert exc.result["cause_error_type"] == "no_cst_session"
    else:
        raise AssertionError("没有 CST 会话时必须报告工程未打开")


def test_sweep_result_failure_is_not_counted_as_success(monkeypatch, tmp_path) -> None:
    from cst_runtime.workflows import sweep

    callbacks: list[int] = []
    monkeypatch.setattr(sweep, "reattach_project", lambda project_path: {"status": "success"})
    monkeypatch.setattr(sweep, "param_exists", lambda project_path, name: True)
    monkeypatch.setattr(sweep, "get_param", lambda project_path, name: 9.0)
    monkeypatch.setattr(sweep, "set_param", lambda *args: None)
    monkeypatch.setattr(sweep, "rebuild", lambda project_path: None)
    runner = sweep.ParameterSweep(
        project_path="model.cst",
        parameters=["width"],
        ranges=[[1.0]],
        target_freq_ghz=8.0,
        callback=lambda step, params, results: callbacks.append(step),
    )
    monkeypatch.setattr(
        runner,
        "_run_single_step",
        lambda params, sparam_dir, step: {
            "params": params,
            "sparams": {
                runner.result_paths[0]: {
                    "status": "error",
                    "message": "结果缺失",
                }
            },
        },
    )

    result = runner.run(output_dir=tmp_path, save_lut=False, save_csv=False)

    assert result.successful_steps == 0
    assert result.failed_steps == 1
    assert callbacks == []
    assert pd.isna(result.lut.iloc[0]["S1,1_mag"])


def test_array_api_matches_python_result(monkeypatch) -> None:
    from cst_runtime.api import invoke
    from cst_runtime.workflows import array

    expected = array.ArrayBuildResult(
        status="success",
        project_path="model.cst",
        groups_built=1,
        instances_created=1,
    )
    monkeypatch.setattr(array, "build_array", lambda **kwargs: expected)
    payload = invoke(
        "array.build",
        {
            "project_path": "model.cst",
            "units": {"a": {"builder_id": "brick-v1"}},
            "elements": [{"code": "a", "x": 0, "y": 0, "z": 0}],
        },
    )
    assert payload["ok"] is True
    assert payload["submission"] == "not_applicable"
    assert payload["execution"] == "not_run"
    assert "verification" not in payload
    for key, value in expected.to_dict().items():
        assert payload[key] == value


def test_api_manifest_contains_workflows() -> None:
    from cst_runtime.api import describe_operations, describe_tools

    names = {operation["name"] for operation in describe_operations()}
    assert {"array.build", "sweep.run"} <= names
    tool_names = {tool["name"] for tool in describe_tools()}
    assert {"build-array", "quick-sweep"} <= tool_names
