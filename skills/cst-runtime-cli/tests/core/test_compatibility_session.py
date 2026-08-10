from __future__ import annotations

from types import SimpleNamespace

from cst_runtime.core.compatibility import session


def test_connect_prefers_connect_to_any(monkeypatch):
    expected = object()

    class DesignEnvironment:
        @staticmethod
        def connect_to_any():
            return expected

    monkeypatch.setattr(session, "_interface", lambda: SimpleNamespace(DesignEnvironment=DesignEnvironment))

    assert session.connect_to_any_design_environment() is expected


def test_connect_falls_back_to_pid(monkeypatch):
    expected = object()

    class DesignEnvironment:
        @staticmethod
        def connect_to_any():
            raise RuntimeError("新版连接不可用")

        @staticmethod
        def connect(pid):
            assert pid == 42
            return expected

    interface = SimpleNamespace(
        DesignEnvironment=DesignEnvironment,
        running_design_environments=lambda: [42],
    )
    monkeypatch.setattr(session, "_interface", lambda: interface)

    assert session.connect_to_any_design_environment() is expected


def test_connect_never_creates_environment_during_read_only_lookup(monkeypatch):
    class DesignEnvironment:
        @staticmethod
        def connect_to_any():
            raise RuntimeError("没有现有环境")

        @staticmethod
        def connect_to_any_or_new():
            raise AssertionError("只读连接不得新建环境")

        def __new__(cls):
            raise AssertionError("只读连接不得调用构造器")

    monkeypatch.setattr(session, "_interface", lambda: SimpleNamespace(DesignEnvironment=DesignEnvironment))

    try:
        session.connect_to_any_design_environment()
    except RuntimeError as exc:
        assert "无法连接现有 CST DesignEnvironment" in str(exc)
    else:
        raise AssertionError("没有现有环境时应明确失败")


def test_active_project_supports_property_and_method_forms():
    project = SimpleNamespace(filename=lambda: "demo.cst")

    assert session.active_project(SimpleNamespace(active_project=project)) is project
    assert session.active_project(SimpleNamespace(active_project=lambda: project)) is project


def test_list_open_projects_falls_back_to_active_project():
    project = SimpleNamespace(filename=lambda: "D:/work/demo.cst")
    environment = SimpleNamespace(active_project=lambda: project)

    assert session.list_open_project_paths(environment) == ["D:/work/demo.cst"]


def test_activate_project_prefers_official_project_method():
    calls: list[str] = []
    project = SimpleNamespace(activate=lambda: calls.append("project.activate"))
    environment = SimpleNamespace(
        set_active_project=lambda _project: calls.append("environment.set_active_project")
    )

    session.activate_project(environment, project)

    assert calls == ["project.activate"]
