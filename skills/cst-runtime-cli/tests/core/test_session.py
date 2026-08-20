"""Test session management functions (pure unit, no CST)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_open_project_falls_back_when_constructor_pid_handoff_fails(monkeypatch, tmp_path):
    """构造器 PID 交接时只连接启动后唯一新增的 DE。"""
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
    pid_snapshots = iter(([41], [41], [41, 11308], [41, 11308]))
    connected_pids = []
    monkeypatch.setattr(
        session.project_identity,
        "discover_expected_project_pids",
        lambda _path, _pids: ([], {"status": "success"}),
    )
    monkeypatch.setattr(
        session,
        "running_design_environment_pids",
        lambda: next(pid_snapshots),
    )
    monkeypatch.setattr(
        session,
        "_connect_new_design_environment",
        lambda: (_ for _ in ()).throw(TimeoutError("Could not connect to a DE with pid: 11308")),
    )
    def connect(pid):
        connected_pids.append(pid)
        return live

    monkeypatch.setattr(session, "connect_design_environment", connect)
    monkeypatch.setattr(session, "inspect", lambda _path="": {"status": "success"})

    result = session.open_project(str(project_path))

    assert result["status"] == "success", result
    assert live.opened_path == str(project_path)
    registered = session._OPENED_DESIGN_ENVIRONMENTS[
        session._abs_project_path(str(project_path))
    ]
    assert connected_pids == [11308]
    assert registered.environment is live
    assert registered.runtime_owned is True


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
    pid_snapshots = iter(([41], [41], [41, 8920], [41, 8930]))
    connected_pids = []
    monkeypatch.setattr(
        session.project_identity,
        "discover_expected_project_pids",
        lambda _path, _pids: ([], {"status": "success"}),
    )
    monkeypatch.setattr(
        session,
        "running_design_environment_pids",
        lambda: next(pid_snapshots),
    )
    monkeypatch.setattr(session, "_connect_new_design_environment", lambda: StaleDE())
    def connect(pid):
        connected_pids.append(pid)
        return live

    monkeypatch.setattr(session, "connect_design_environment", connect)
    monkeypatch.setattr(session, "inspect", lambda _path="": {"status": "success"})

    result = session.open_project(str(project_path))

    assert result["status"] == "success", result
    assert live.opened_path == str(project_path)
    assert connected_pids == [8930]


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
        "discover_expected_project_pids",
        lambda _path, _pids: ([], {"status": "success"}),
    )
    monkeypatch.setattr(session, "running_design_environment_pids", lambda: [])
    monkeypatch.setattr(session, "_connect_new_design_environment", lambda: broken)

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
        "discover_expected_project_pids",
        lambda _path, _pids: ([], {"status": "success"}),
    )
    monkeypatch.setattr(session, "running_design_environment_pids", lambda: [])
    monkeypatch.setattr(
        session,
        "_connect_new_design_environment",
        lambda: (_ for _ in ()).throw(RuntimeError("license server unavailable")),
    )
    result = session.open_project(str(project_path))

    assert result["status"] == "error"
    assert result["error_type"] == "open_project_failed"


def test_open_project_requires_confirmation_before_existing_session(monkeypatch, tmp_path):
    """首次发现目标工程已打开时，只返回精确候选 PID。"""
    from cst_runtime.core import session

    project_path = tmp_path / "working.cst"
    project_path.write_bytes(b"")
    monkeypatch.setattr(session, "running_design_environment_pids", lambda: [41])
    monkeypatch.setattr(
        session.project_identity,
        "discover_expected_project_pids",
        lambda _path, pids: ([41], {"status": "success"}) if pids == {41} else ([], {}),
    )
    monkeypatch.setattr(
        session.project_identity,
        "attach_expected_project_at_pid",
        lambda *_args: (_ for _ in ()).throw(AssertionError("确认前不得附着")),
    )
    monkeypatch.setattr(
        session,
        "_connect_new_design_environment",
        lambda: (_ for _ in ()).throw(AssertionError("确认前不得新建会话")),
    )

    result = session.open_project(str(project_path))
    reattach_result = session.reattach_project(str(project_path))

    assert result["status"] == "error"
    assert result["error_type"] == "existing_session_confirmation_required"
    assert result["requires_user_confirmation"] is True
    assert result["candidate_design_environment_pids"] == [41]
    assert reattach_result["error_type"] == "existing_session_confirmation_required"


def test_confirmed_existing_session_is_not_closed_as_owned(monkeypatch, tmp_path):
    """确认附着的外部 DE 只关闭工程，不关闭或终止整个会话。"""
    from cst_runtime.core import session

    project_path = tmp_path / "working.cst"
    project_path.write_bytes(b"")

    class FakeProject:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    class FakeDesignEnvironment:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    project = FakeProject()
    de = FakeDesignEnvironment()
    attached_pids = []

    def attach_at_pid(_path, pid):
        attached_pids.append(pid)
        return project, de, {"status": "success", "design_environment_pid": pid}

    monkeypatch.setattr(
        session.project_identity,
        "attach_expected_project_at_pid",
        attach_at_pid,
    )
    monkeypatch.setattr(
        session.project_identity,
        "discover_expected_project_pids",
        lambda *_args: (_ for _ in ()).throw(AssertionError("确认后不得全局发现")),
    )
    monkeypatch.setattr(
        session.project_identity,
        "attach_expected_project",
        lambda *_args: (_ for _ in ()).throw(AssertionError("已有缓存时不得重新扫描")),
    )
    monkeypatch.setattr(
        session.project_identity,
        "wait_project_unlocked",
        lambda **_kwargs: {"status": "success"},
    )
    monkeypatch.setattr(
        session.process_cleanup,
        "stop_process",
        lambda *_args: (_ for _ in ()).throw(AssertionError("外部 DE 不得被终止")),
    )
    monkeypatch.setattr(session, "inspect", lambda _path="": {"status": "success"})

    opened = session.open_project(
        str(project_path),
        confirm_existing_session_takeover=True,
        existing_session_pid=41,
    )
    quit_result = session.quit_cst(str(project_path))
    closed = session.close_project(str(project_path), save=False, kill_processes=True)

    assert opened["status"] == "success"
    assert opened["design_environment_ownership"] == "user_confirmed"
    assert attached_pids == [41]
    assert project.closed is True
    assert de.closed is False
    assert quit_result["cleanup_result"]["error_type"] == "design_environment_not_owned"
    assert closed["kill_result"]["error_type"] == "design_environment_not_owned"


def test_close_project_reports_process_stop_failure(monkeypatch):
    from cst_runtime.core import session

    class FakeProject:
        def close(self):
            return None

    normalized = session._abs_project_path("C:/temporary-test.cst")
    project = FakeProject()
    monkeypatch.setattr(session, "_OPENED_PROJECTS", {normalized: project})
    monkeypatch.setattr(
        session,
        "_OPENED_DESIGN_ENVIRONMENTS",
        {
            normalized: session._DesignEnvironmentLease(
                environment=None,
                design_environment_pid=12345,
                runtime_owned=True,
            )
        },
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
        {
            normalized: session._DesignEnvironmentLease(
                environment=design_environment,
                design_environment_pid=12345,
                runtime_owned=True,
            )
        },
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
        "discover_expected_project_pids",
        lambda _path, _pids: ([], {"status": "success"}),
    )
    monkeypatch.setattr(session, "running_design_environment_pids", lambda: [])
    monkeypatch.setattr(
        session,
        "_connect_new_design_environment",
        lambda: design_environment,
    )

    result = session.open_project(str(project_path))

    assert result["status"] == "error"
    assert design_environment.closed is True


def test_session_open_tool_forwards_confirmation_without_coercion(monkeypatch):
    """工具层原样转发确认参数，类型校验统一留给 Core。"""
    from cst_runtime.tools import session as session_tools

    captured = {}

    def open_project(project_path, **kwargs):
        captured.update(project_path=project_path, **kwargs)
        return {"status": "success"}

    monkeypatch.setattr(session_tools._sm, "open_project", open_project)
    result = session_tools.tool_cst_session_open({
        "project_path": "C:/confirmed.cst",
        "confirm_existing_session_takeover": True,
        "existing_session_pid": 41,
    })

    assert result["status"] == "success"
    assert captured == {
        "project_path": "C:/confirmed.cst",
        "confirm_existing_session_takeover": True,
        "existing_session_pid": 41,
    }
