"""Test core/simulation.py: guard integration."""
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers import assert_json_error


def test_prepare_experiment_rebuilds_before_saving(monkeypatch):
    """准备试验必须包含重建，不依赖保存重开自动更新几何。"""
    from cst_runtime.lib import project, session, solver
    from cst_runtime.cli.pipelines.impl import pipeline_prepare_experiment
    events = []
    monkeypatch.setattr(session, "open_project", lambda path: {"status": "success"})
    monkeypatch.setattr(project, "change_parameter", lambda **kw: events.append("change") or {"status": "success"})
    monkeypatch.setattr(solver, "rebuild", lambda path, **kw: events.append(("rebuild", kw)) or {"status": "success"})
    monkeypatch.setattr(project, "save_project", lambda path: events.append("save") or {"status": "success"})
    monkeypatch.setattr(session, "close_project", lambda path, **kw: events.append("close") or {"status": "success"})
    result = pipeline_prepare_experiment("model.cst", param_name="w", param_value=3)
    assert result["status"] == "success"
    assert events == ["change", ("rebuild", {"full_rebuild": False}), "save", "close"]


def test_start_sim_async_rejects_dirty_project(tmp_path):
    """T2: start_simulation_async refuses dirty project without reopen."""
    from cst_runtime.core.simulation import start_simulation_async
    from cst_runtime.core import gateway
    from cst_runtime.core.utils import abs_project_path

    dummy = abs_project_path(str(tmp_path / "dirty.cst"))
    gateway.mark_params_dirty(dummy)
    result = start_simulation_async(dummy)
    assert_json_error(result, "params_not_rebuilt")


def test_start_sim_sync_also_rejects_dirty(tmp_path):
    """T2: synchronous start_simulation also checks dirty flag."""
    from cst_runtime.core.simulation import start_simulation
    from cst_runtime.core import gateway
    from cst_runtime.core.utils import abs_project_path

    dummy = abs_project_path(str(tmp_path / "dirty2.cst"))
    gateway.mark_params_dirty(dummy)
    result = start_simulation(dummy)
    assert_json_error(result, "params_not_rebuilt")


def test_is_simulation_running_no_project(mocker):
    """is_simulation_running when project not attached returns the status error."""
    from cst_runtime.core.simulation import is_simulation_running

    mocker.patch(
        "cst_runtime.core.simulation.attach_expected_project",
        return_value=(None, {"status": "error", "error_type": "project_not_open"}),
    )
    result = is_simulation_running("/nonexistent.cst")
    assert result["status"] == "error"


def test_start_simulation_reports_false_solver_result(monkeypatch):
    from cst_runtime.core import simulation

    project = SimpleNamespace(modeler=SimpleNamespace(run_solver=lambda: False))
    monkeypatch.setattr(simulation.gateway, "guard_before_simulation", lambda _path: None)
    monkeypatch.setattr(
        simulation,
        "attach_expected_project",
        lambda _path: (project, {}),
    )

    result = simulation.start_simulation("D:/work/model.cst")

    assert result["status"] == "error"
    assert result["error_type"] == "solver_run_failed"


def test_start_simulation_accepts_true_solver_result(monkeypatch):
    from cst_runtime.core import simulation

    project = SimpleNamespace(modeler=SimpleNamespace(run_solver=lambda: True))
    monkeypatch.setattr(simulation.gateway, "guard_before_simulation", lambda _path: None)
    monkeypatch.setattr(
        simulation,
        "attach_expected_project",
        lambda _path: (project, {}),
    )

    result = simulation.start_simulation("D:/work/model.cst")

    assert result["status"] == "success"
    assert result["message"] == "simulation completed"


def test_fdsolver_stimulation_matches_cst2022_manual() -> None:
    from cst_runtime.core.compatibility.base import CompatibilityProfile
    from cst_runtime.core.compatibility.modeling import fdsolver_stimulation_vba

    profile = CompatibilityProfile(major=2022, version="2022", source="test")
    generated = fdsolver_stimulation_vba(port="All", mode="All", profile=profile)

    assert generated.lines == ('FDSolver.Stimulation "All", "All"',)
    assert all("FDSolver.Reset" not in line for line in generated.lines)


def test_fdsolver_stimulation_supports_manual_plane_wave_rule() -> None:
    from cst_runtime.core.compatibility.base import CompatibilityProfile
    from cst_runtime.core.compatibility.modeling import fdsolver_stimulation_vba

    profile = CompatibilityProfile(major=2022, version="2022", source="test")
    generated = fdsolver_stimulation_vba(port="Plane Wave", mode=1, profile=profile)

    assert generated.lines[-1] == 'FDSolver.Stimulation "Plane Wave", 1'


@pytest.mark.parametrize(
    ("port", "mode"),
    [
        (0, 1),
        ("unknown", 1),
        ("Plane Wave", 2),
        ("List", 1),
        (1, "Plane Wave"),
        ('All"\nReportError "x', "All"),
    ],
)
def test_fdsolver_stimulation_rejects_invalid_manual_arguments(port, mode) -> None:
    from cst_runtime.core.compatibility.base import CompatibilityProfile
    from cst_runtime.core.compatibility.modeling import fdsolver_stimulation_vba
    from cst_runtime.core.errors import ValidationError

    profile = CompatibilityProfile(major=2022, version="2022", source="test")

    with pytest.raises(ValidationError):
        fdsolver_stimulation_vba(port=port, mode=mode, profile=profile)


@pytest.mark.parametrize("full_rebuild", [False, True])
@pytest.mark.parametrize("returned", ["True", "False"])
def test_rebuild_uses_immediate_return_and_clears_dirty_only_on_success(monkeypatch, tmp_path, full_rebuild, returned):
    """重建自身不得进入历史；失败时保留待重建状态。"""
    from cst_runtime.core import simulation
    from cst_runtime.core import gateway

    captured: dict[str, str] = {}

    def fake_query(project, lines):
        captured["vba_line"] = "\n".join(lines)
        return [returned]

    monkeypatch.setattr(simulation, "attach_expected_project", lambda path: (object(), {}))
    monkeypatch.setattr(simulation, "execute_text_query", fake_query)
    monkeypatch.setattr(simulation, "_single_vba", lambda *a, **k: pytest.fail("重建不得写入历史"))
    path = str(tmp_path / "model.cst")
    gateway.mark_params_dirty(path)

    result = simulation.rebuild_structure(path, full_rebuild=full_rebuild)

    assert result["status"] == ("success" if returned == "True" else "error")
    assert gateway._dirty_marker_path(path).exists() == (returned == "False")
    if returned == "True":
        assert result["model_rebuilt"] is True
        assert result["results_policy"] == ("delete_all" if full_rebuild else "delete_invalidated")
    command = "Rebuild" if full_rebuild else "RebuildOnParametricChange(False, False)"
    assert captured["vba_line"] == f"Print #cstRtQueryFile, CStr({command})"
