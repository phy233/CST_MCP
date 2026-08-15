"""Test session management functions (pure unit, no CST)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_open_project_falls_back_when_constructor_pid_handoff_fails(monkeypatch, tmp_path):
    """构造器冷启动报 PID 错误时，必须用官方连接路径接管真实 DE。"""
    from cst_runtime.core import session

    project_path = tmp_path / "working.cst"
    project_path.write_bytes(b"")

    class LiveDE:
        def __init__(self):
            self.opened_path = None

        def open_project(self, path):
            self.opened_path = path
            return object()

    live = LiveDE()
    monkeypatch.setattr(
        session.project_identity,
        "attach_expected_project",
        lambda _path: (None, {"status": "error"}),
    )
    monkeypatch.setattr(
        session,
        "_connect_new_design_environment",
        lambda: (_ for _ in ()).throw(TimeoutError("Could not connect to a DE with pid: 11308")),
    )
    monkeypatch.setattr(session, "connect_to_any_design_environment", lambda: live)
    monkeypatch.setattr(session, "inspect", lambda _path="": {"status": "success"})

    result = session.open_project(str(project_path))

    assert result["status"] == "success", result
    assert live.opened_path == str(project_path)
    registered = session._OPENED_DESIGN_ENVIRONMENTS[
        session._abs_project_path(str(project_path))
    ]
    assert registered is live


def test_open_project_falls_back_on_open_pid_handoff(monkeypatch, tmp_path):
    """构造成功但 open_project 报 PID 错误时，换新句柄重试打开。"""
    from cst_runtime.core import session

    project_path = tmp_path / "working.cst"
    project_path.write_bytes(b"")

    class StaleDE:
        def open_project(self, _path):
            raise RuntimeError("Could not connect to a DE with pid: 8920")

        def close(self):
            pass

    class LiveDE:
        def __init__(self):
            self.opened_path = None

        def open_project(self, path):
            self.opened_path = path
            return object()

    live = LiveDE()
    monkeypatch.setattr(
        session.project_identity,
        "attach_expected_project",
        lambda _path: (None, {"status": "error"}),
    )
    monkeypatch.setattr(session, "_connect_new_design_environment", lambda: StaleDE())
    monkeypatch.setattr(session, "connect_to_any_design_environment", lambda: live)
    monkeypatch.setattr(session, "inspect", lambda _path="": {"status": "success"})

    result = session.open_project(str(project_path))

    assert result["status"] == "success", result
    assert live.opened_path == str(project_path)


def test_open_project_keeps_non_pid_failure(monkeypatch, tmp_path):
    """非 PID 交接错误不得触发回退，且必须关闭本次新建的空白 DE。"""
    from cst_runtime.core import session

    project_path = tmp_path / "working.cst"
    project_path.write_bytes(b"")

    class BrokenDE:
        def __init__(self):
            self.closed = False

        def open_project(self, _path):
            raise RuntimeError("license server unavailable")

        def close(self):
            self.closed = True

    broken = BrokenDE()
    monkeypatch.setattr(
        session.project_identity,
        "attach_expected_project",
        lambda _path: (None, {"status": "error"}),
    )
    monkeypatch.setattr(session, "_connect_new_design_environment", lambda: broken)
    monkeypatch.setattr(
        session,
        "connect_to_any_design_environment",
        lambda: (_ for _ in ()).throw(AssertionError("非 PID 错误不得回退")),
    )

    result = session.open_project(str(project_path))

    assert result["status"] == "error"
    assert result["error_type"] == "open_project_failed"
    assert broken.closed is True


def test_open_project_keeps_non_pid_constructor_failure(monkeypatch, tmp_path):
    """构造器抛非 PID 错误时不得回退，直接返回 open_project_failed。"""
    from cst_runtime.core import session

    project_path = tmp_path / "working.cst"
    project_path.write_bytes(b"")

    monkeypatch.setattr(
        session.project_identity,
        "attach_expected_project",
        lambda _path: (None, {"status": "error"}),
    )
    monkeypatch.setattr(
        session,
        "_connect_new_design_environment",
        lambda: (_ for _ in ()).throw(RuntimeError("license server unavailable")),
    )
    monkeypatch.setattr(
        session,
        "connect_to_any_design_environment",
        lambda: (_ for _ in ()).throw(AssertionError("非 PID 错误不得回退")),
    )

    result = session.open_project(str(project_path))

    assert result["status"] == "error"
    assert result["error_type"] == "open_project_failed"


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
