"""面向 Python 开发者的 MCP 交互与工作笔记公共 API 门面。"""
from __future__ import annotations

from typing import Any

from ..interaction.journal import (
    list_interactions,
    read_payload_reference,
)
from ..interaction.notes import (
    list_work_notes,
    record_work_note,
)


def list_interaction_log(
    *,
    task_id: str | None = None,
    run_id: str | None = None,
    project_path: str | None = None,
    tool_name: str | None = None,
    interaction_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查询 MCP 交互日志。"""
    return list_interactions(
        task_id=task_id,
        run_id=run_id,
        project_path=project_path,
        tool_name=tool_name,
        interaction_id=interaction_id,
        limit=limit,
    )


def inspect_interaction_history(
    interaction_id: str,
) -> dict[str, Any]:
    """查询单次 interaction 关联的 History 变更详情。"""
    items = list_interactions(interaction_id=interaction_id, limit=1)
    if not items:
        return {
            "status": "error",
            "message": f"未找到 interaction_id={interaction_id} 的记录",
        }
    item = items[0]
    return {
        "status": "success",
        "interaction": item,
    }


def add_agent_note(
    content: str,
    *,
    category: str = "general",
    task_id: str | None = None,
    run_id: str | None = None,
    project_path: str | None = None,
    interaction_id: str | None = None,
    operation_id: str | None = None,
    snapshot_id: str | None = None,
    user_confirmed: bool | None = None,
    author: str = "agent",
) -> dict[str, Any]:
    """显式提交工作说明或决策。"""
    return record_work_note(
        content,
        category=category,
        task_id=task_id,
        run_id=run_id,
        project_path=project_path,
        interaction_id=interaction_id,
        operation_id=operation_id,
        snapshot_id=snapshot_id,
        user_confirmed=user_confirmed,
        author=author,
    )


def list_agent_notes(
    *,
    task_id: str | None = None,
    run_id: str | None = None,
    project_path: str | None = None,
    category: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查询工作笔记列表。"""
    return list_work_notes(
        task_id=task_id,
        run_id=run_id,
        project_path=project_path,
        category=category,
        limit=limit,
    )
