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


def test_close_project_closes_runtime_owned_design_environment(monkeypatch):
    """关闭工程时应同步关闭由 Runtime 创建的空白 CST 外壳。"""
    from cst_runtime.core import session

    class FakeProject:
        def close(self):
            return None

    class FakeDesignEnvironment:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    normalized = session._abs_project_path("C:/runtime-owned-test.cst")
    project = FakeProject()
    design_environment = FakeDesignEnvironment()
    monkeypatch.setattr(session, "_OPENED_PROJECTS", {normalized: project})
    monkeypatch.setattr(
        session,
        "_OPENED_DESIGN_ENVIRONMENTS",
        {normalized: design_environment},
    )
    monkeypatch.setattr(
        session.project_identity,
        "attach_expected_project",
        lambda _path: (project, {"status": "success"}),
    )
    monkeypatch.setattr(
        session.project_identity,
        "wait_project_unlocked",
        lambda **_kwargs: {"status": "success"},
    )
    monkeypatch.setattr(session, "inspect", lambda _path="": {"status": "success"})

    result = session.close_project("C:/runtime-owned-test.cst", save=False)

    assert result["status"] == "success"
    assert result["close_result"]["environment_closed"] is True
    assert design_environment.closed is True


def test_open_project_failure_closes_new_design_environment(monkeypatch, tmp_path):
    """工程打开失败时不应遗留新启动的空白 CST 窗口。"""
    from cst_runtime.core import session

    project_path = tmp_path / "broken.cst"
    project_path.write_bytes(b"")

    class FakeDesignEnvironment:
        def __init__(self):
            self.closed = False

        def open_project(self, _path):
            raise RuntimeError("模拟打开失败")

        def close(self):
            self.closed = True

    design_environment = FakeDesignEnvironment()
    monkeypatch.setattr(
        session.project_identity,
        "attach_expected_project",
        lambda _path: (None, {"status": "error"}),
    )
    monkeypatch.setattr(
        session,
        "_connect_new_design_environment",
        lambda: design_environment,
    )

    result = session.open_project(str(project_path))

    assert result["status"] == "error"
    assert design_environment.closed is True
