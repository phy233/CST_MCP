"""Test core/simulation.py: guard integration."""
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers import assert_json_error


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


def test_rebuild_warns_that_results_are_deleted_and_checks_return(monkeypatch):
    from cst_runtime.core import simulation

    captured: dict[str, str] = {}

    def fake_single(project_path, history_name, vba_line):
        captured["vba_line"] = vba_line
        return {"status": "success", "project_path": project_path}

    monkeypatch.setattr(simulation, "_single_vba_pops", fake_single)

    result = simulation.rebuild_structure("D:/work/model.cst")

    assert result["status"] == "success"
    assert result["results_deleted"] is True
    assert "删除" in result["warning"]
    assert captured["vba_line"] == "\n".join(
        [
            "If Not Rebuild Then",
            '    ReportError "Rebuild returned False"',
            "End If",
        ]
    )
