"""DesignEnvironment 与活动工程的跨版本适配。"""
from __future__ import annotations

from typing import Any


def _interface() -> Any:
    import cst.interface

    return cst.interface


def running_design_environment_pids() -> list[int]:
    interface = _interface()
    for owner in (interface, getattr(interface, "DesignEnvironment", None)):
        getter = getattr(owner, "running_design_environments", None)
        if callable(getter):
            try:
                return [int(pid) for pid in getter()]
            except Exception:
                continue
    return []


def connect_design_environment(pid: int) -> Any:
    design_environment = _interface().DesignEnvironment
    connector = getattr(design_environment, "connect", None)
    if not callable(connector):
        raise RuntimeError("当前 CST Python API 不支持按 PID 连接 DesignEnvironment")
    return connector(pid)


def connect_to_any_design_environment() -> Any:
    """只连接现有 Design Environment，绝不在只读检查中隐式新建。"""
    design_environment = _interface().DesignEnvironment
    failures: list[str] = []
    connector = getattr(design_environment, "connect_to_any", None)
    if callable(connector):
        try:
            return connector()
        except Exception as exc:
            failures.append(f"connect_to_any: {exc}")
    for pid in running_design_environment_pids():
        try:
            return connect_design_environment(pid)
        except Exception as exc:
            failures.append(f"connect({pid}): {exc}")
    detail = "；".join(failures) if failures else "没有发现运行中的 Design Environment"
    raise RuntimeError("无法连接现有 CST DesignEnvironment；" + detail)


def create_design_environment() -> Any:
    """按 CST 2022 Python 手册优先直接构造，失败后兼容静态 new。"""
    design_environment = _interface().DesignEnvironment
    try:
        return design_environment()
    except Exception as constructor_error:
        creator = getattr(design_environment, "new", None)
        if callable(creator):
            return creator()
        raise constructor_error


def design_environment_pid(environment: Any) -> int | None:
    value = getattr(environment, "pid", None)
    try:
        value = value() if callable(value) else value
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def active_project(environment: Any) -> Any | None:
    value = getattr(environment, "active_project", None)
    return value() if callable(value) else value


def has_active_project(environment: Any) -> bool:
    checker = getattr(environment, "has_active_project", None)
    if checker is not None:
        try:
            return bool(checker() if callable(checker) else checker)
        except Exception:
            pass
    try:
        return active_project(environment) is not None
    except Exception:
        return False


def list_open_project_paths(environment: Any) -> list[str]:
    """列出工程；旧版无枚举 API 时至少返回当前活动工程。"""
    getter = getattr(environment, "list_open_projects", None)
    if callable(getter):
        try:
            return [str(path) for path in (getter() or [])]
        except Exception:
            pass
    project = active_project(environment)
    if project is None:
        return []
    filename = getattr(project, "filename", None)
    try:
        value = filename() if callable(filename) else filename
        return [str(value)] if value else []
    except Exception:
        return []


def get_open_project(environment: Any, project_path: str) -> Any:
    getter = getattr(environment, "get_open_project", None)
    if callable(getter):
        return getter(project_path)
    current = active_project(environment)
    if current is not None:
        filename = getattr(current, "filename", None)
        value = filename() if callable(filename) else filename
        if value and str(value) == str(project_path):
            return current
    raise RuntimeError("当前 CST API 无法按路径取得已打开工程")


def activate_project(environment: Any, project: Any) -> None:
    """激活工程；优先使用 CST 2022/2026 都公开的 Project.activate。"""
    activator = getattr(project, "activate", None)
    if callable(activator):
        activator()
        return
    setter = getattr(environment, "set_active_project", None)
    if callable(setter):
        setter(project)
        return
    try:
        setattr(environment, "active_project", project)
    except Exception as exc:
        current = active_project(environment)
        if current is project:
            return
        raise RuntimeError(f"当前 CST API 无法切换活动工程：{exc}") from exc


__all__ = [
    "activate_project",
    "active_project",
    "connect_design_environment",
    "connect_to_any_design_environment",
    "create_design_environment",
    "design_environment_pid",
    "get_open_project",
    "has_active_project",
    "list_open_project_paths",
    "running_design_environment_pids",
]
