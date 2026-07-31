"""Test session management functions (via subprocess CLI)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_session_inspect_no_project(run_cli):
    """cst-session-inspect returns valid JSON without project."""
    result = run_cli("cst-session-inspect")
    assert result["status"] == "success"
    assert "force_kill_allowlist" in result
    assert "process_count" in result
    assert "readiness" in result


def test_session_quit_dry_run(run_cli):
    """cst-session-quit --dry-run does not kill processes."""
    result = run_cli("cst-session-quit", "--dry-run", "true")
    assert result["status"] == "success"
    assert "dry_run" in result


def test_close_project_reports_process_stop_failure(monkeypatch):
    from cst_runtime.core import session

    class FakeProject:
        def close(self):
            return None

    monkeypatch.setattr(
        session.project_identity,
        "attach_expected_project",
        lambda _path: (
            FakeProject(),
            {"status": "success", "design_environment_pid": 12345},
        ),
    )
    monkeypatch.setattr(
        session.project_identity,
        "wait_project_unlocked",
        lambda **_kwargs: {"status": "success"},
    )
    monkeypatch.setattr(
        session.process_cleanup,
        "stop_process",
        lambda *_args: {"status": "error", "message": "拒绝访问"},
    )
    monkeypatch.setattr(session, "inspect", lambda _path="": {"status": "success"})

    result = session.close_project(
        "C:/temporary-test.cst",
        save=False,
        kill_processes=True,
    )

    assert result["status"] == "error"
    assert result["error_type"] == "session_close_failed"
    assert result["kill_result"]["status"] == "error"
