"""Sweep、CrossProcess 与统一 API 的测试。"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_sweep_restores_parameters_and_serializes(monkeypatch, tmp_path) -> None:
    from cst_runtime.workflows import sweep

    restored: list[tuple[str, float]] = []
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
        return {"params": params, "sparams": {}}

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
        lambda project_path, result_path: {
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


def test_cross_process_reuses_sweep(monkeypatch, tmp_path) -> None:
    from cst_runtime.workflows import cross_process
    from cst_runtime.workflows.sweep import SweepResult

    class FakeSweep:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def run(self, output_dir=None):
            csv_path = Path(output_dir) / "lut.csv"
            npz_path = Path(output_dir) / "lut.npz"
            return SweepResult(
                lut=pd.DataFrame(
                    [{"SZmax(1),Zmax(1)_mag_db": -1.0, "lx": 3.0, "ly1": 4.0}]
                ),
                output_dir=Path(output_dir),
                sweep_time=0.1,
                total_steps=1,
                successful_steps=1,
                failed_steps=0,
                exported_files=[csv_path, npz_path],
            )

    monkeypatch.setattr(cross_process, "ParameterSweep", FakeSweep)
    result = cross_process.quick_cross_sweep(
        "model.cst",
        lx_range=[3.0],
        ly1_range=[4.0],
        target_freq_ghz=8.0,
        output_dir=tmp_path,
    )
    assert "Y_pol_mag_db" in result.lut.columns
    assert "Y_pol_mag_db" in pd.read_csv(tmp_path / "lut.csv").columns


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
    assert payload["verification"] == "not_run"
    for key, value in expected.to_dict().items():
        assert payload[key] == value


def test_api_manifest_contains_workflows() -> None:
    from cst_runtime.api import describe_operations, describe_tools

    names = {operation["name"] for operation in describe_operations()}
    assert {"array.build", "sweep.run", "cross_process.run"} <= names
    tool_names = {tool["name"] for tool in describe_tools()}
    assert {"build-array", "quick-sweep", "cross-process-sweep"} <= tool_names
