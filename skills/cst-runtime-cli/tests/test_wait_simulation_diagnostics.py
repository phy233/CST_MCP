"""wait-simulation 与 lib.solver.wait 的求解错误检测行为测试。"""
from __future__ import annotations

from types import SimpleNamespace

from cst_runtime.lib.contracts import error_result, success_result


def _fake_wait_context(monkeypatch, running_values, diagnostics):
    from cst_runtime.tools import project as project_module

    monkeypatch.setattr(
        project_module,
        "_sim",
        SimpleNamespace(
            is_simulation_running=lambda path: success_result(
                project_path=path,
                running=running_values[0],
            )
        ),
    )
    monkeypatch.setattr(
        project_module,
        "_sv",
        SimpleNamespace(
            capture_log_baseline=lambda path: success_result(baseline={"x": 0}),
            read_solver_errors=lambda path, baseline=None, since=None: diagnostics,
        ),
    )


def test_wait_simulation_returns_solver_error_with_raw_text(monkeypatch):
    _fake_wait_context(
        monkeypatch,
        running_values=[False],
        diagnostics=success_result(
            errors=[
                "13/Aug/2026 23:08:30  *** Error ***\nFarfield monitors are not supported"
            ],
            error_lines=["Farfield monitors are not supported"],
            log_files=["Model.log"],
        ),
    )

    from cst_runtime.tools.project import tool_wait_simulation

    result = tool_wait_simulation(
        {
            "project_path": "C:/work/working.cst",
            "timeout_seconds": 10,
            "poll_interval_seconds": 0,
        }
    )

    assert result["status"] == "error"
    assert result["error_type"] == "solver_stopped_with_error"
    assert result["running"] is False
    assert result["cst_errors"][0].startswith("13/Aug/2026")
    assert "Farfield monitors are not supported" in result["cst_error_lines"][0]
    assert result["log_files"] == ["Model.log"]


def test_wait_simulation_success_does_not_claim_solver_success(monkeypatch):
    _fake_wait_context(
        monkeypatch,
        running_values=[False],
        diagnostics=success_result(errors=[], error_lines=[], log_files=[]),
    )

    from cst_runtime.tools.project import tool_wait_simulation

    result = tool_wait_simulation(
        {
            "project_path": "C:/work/working.cst",
            "timeout_seconds": 10,
            "poll_interval_seconds": 0,
        }
    )

    assert result["status"] == "success"
    assert result["running"] is False
    assert result["solver_completed"] == "unknown"
    assert result["cst_errors"] == []


def test_wait_simulation_timeout_unchanged(monkeypatch):
    _fake_wait_context(
        monkeypatch,
        running_values=[True],
        diagnostics=success_result(errors=[], error_lines=[], log_files=[]),
    )

    from cst_runtime.tools.project import tool_wait_simulation

    result = tool_wait_simulation(
        {
            "project_path": "C:/work/working.cst",
            "timeout_seconds": 0,
            "poll_interval_seconds": 0,
        }
    )

    assert result["status"] == "error"
    assert result["error_type"] == "simulation_wait_timeout"
    assert result["running"] is True


def test_lib_solver_wait_reports_stopped_with_error(monkeypatch):
    from cst_runtime.lib import solver

    monkeypatch.setattr(
        solver,
        "is_running",
        lambda path: success_result(project_path=path, running=False),
    )
    monkeypatch.setattr(
        solver,
        "capture_log_baseline",
        lambda path: success_result(baseline={}),
    )
    monkeypatch.setattr(
        solver,
        "read_solver_errors",
        lambda path, baseline=None, since=None: success_result(
            errors=["*** Error ***\nnot supported"],
            error_lines=["not supported"],
            log_files=["Model.log"],
        ),
    )

    result = solver.wait("C:/work/working.cst", timeout=1, interval=0)

    assert result["status"] == "error"
    assert result["error_type"] == "solver_stopped_with_error"
    assert result["cst_errors"] == ["*** Error ***\nnot supported"]


def test_lib_solver_wait_unknown_completion_without_errors(monkeypatch):
    from cst_runtime.lib import solver

    monkeypatch.setattr(
        solver,
        "is_running",
        lambda path: success_result(project_path=path, running=False),
    )
    monkeypatch.setattr(
        solver,
        "capture_log_baseline",
        lambda path: success_result(baseline={}),
    )
    monkeypatch.setattr(
        solver,
        "read_solver_errors",
        lambda path, baseline=None, since=None: success_result(
            errors=[], error_lines=[], log_files=[]
        ),
    )

    result = solver.wait("C:/work/working.cst", timeout=1, interval=0)

    assert result["status"] == "success"
    assert result["solver_completed"] == "unknown"
    assert result["completed"] is True


def test_lib_solver_wait_timeout(monkeypatch):
    from cst_runtime.lib import solver

    monkeypatch.setattr(
        solver,
        "is_running",
        lambda path: success_result(project_path=path, running=True),
    )

    result = solver.wait("C:/work/working.cst", timeout=0, interval=0)

    assert result["status"] == "error"
    assert result["error_type"] == "simulation_wait_timeout"
