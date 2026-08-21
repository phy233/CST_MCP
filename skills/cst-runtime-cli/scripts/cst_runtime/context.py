"""cst_runtime 运行时执行上下文管理。

使用 contextvars 在同一执行流中透明传递 interaction_id、task_id、run_id 与 project_path，
避免在底层组件与日志系统之间产生不必要的耦合。
"""
from __future__ import annotations

import contextvars
from typing import Any

_INTERACTION_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_interaction_id", default=None
)
_TASK_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_task_id", default=None
)
_RUN_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_run_id", default=None
)
_PROJECT_PATH: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_project_path", default=None
)


def get_current_interaction_id() -> str | None:
    """获取当前协程/线程关联的 MCP interaction_id。"""
    return _INTERACTION_ID.get()


def set_current_interaction_id(interaction_id: str | None) -> contextvars.Token[str | None]:
    """设置当前协程/线程关联的 MCP interaction_id。"""
    return _INTERACTION_ID.set(interaction_id)


def reset_current_interaction_id(token: contextvars.Token[str | None]) -> None:
    """重置 interaction_id 上下文。"""
    _INTERACTION_ID.reset(token)


def get_current_task_id() -> str | None:
    return _TASK_ID.get()


def set_current_task_id(task_id: str | None) -> contextvars.Token[str | None]:
    return _TASK_ID.set(task_id)


def reset_current_task_id(token: contextvars.Token[str | None]) -> None:
    _TASK_ID.reset(token)


def get_current_run_id() -> str | None:
    return _RUN_ID.get()


def set_current_run_id(run_id: str | None) -> contextvars.Token[str | None]:
    return _RUN_ID.set(run_id)


def reset_current_run_id(token: contextvars.Token[str | None]) -> None:
    _RUN_ID.reset(token)


def get_current_project_path() -> str | None:
    return _PROJECT_PATH.get()


def set_current_project_path(project_path: str | None) -> contextvars.Token[str | None]:
    return _PROJECT_PATH.set(project_path)


def reset_current_project_path(token: contextvars.Token[str | None]) -> None:
    _PROJECT_PATH.reset(token)


def get_current_execution_context() -> dict[str, Any]:
    """返回当前执行上下文的完整字典快照。"""
    return {
        "interaction_id": _INTERACTION_ID.get(),
        "task_id": _TASK_ID.get(),
        "run_id": _RUN_ID.get(),
        "project_path": _PROJECT_PATH.get(),
    }


def set_current_execution_context(
    *,
    interaction_id: str | None = None,
    task_id: str | None = None,
    run_id: str | None = None,
    project_path: str | None = None,
) -> list[contextvars.Token[Any]]:
    """批量设置当前执行上下文，并返回 tokens 列表供后续重置。"""
    tokens: list[contextvars.Token[Any]] = []
    if interaction_id is not None:
        tokens.append(_INTERACTION_ID.set(interaction_id))
    if task_id is not None:
        tokens.append(_TASK_ID.set(task_id))
    if run_id is not None:
        tokens.append(_RUN_ID.set(run_id))
    if project_path is not None:
        tokens.append(_PROJECT_PATH.set(project_path))
    return tokens
