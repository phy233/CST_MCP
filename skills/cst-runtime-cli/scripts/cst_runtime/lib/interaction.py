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
    *,
    project_path: str | None = None,
) -> dict[str, Any]:
    """查询单次 interaction 关联的 History 变更详情，包括关联的 Operation、前后快照及 Diff。"""
    from ..history.journal import get_operation, list_operations, load_snapshot
    from ..history.diff import diff_snapshots
    from ..history.models import HistoryOperationRecord

    items = list_interactions(interaction_id=interaction_id, limit=1)
    if not items:
        return {
            "status": "error",
            "message": f"未找到 interaction_id={interaction_id} 的记录",
        }
    item = items[0]
    p_path = project_path or item.get("project_path")

    # 查找关联的 Operation
    op_id = item.get("operation_id")
    matched_op: HistoryOperationRecord | None = None
    if op_id:
        matched_op = get_operation(op_id, project_path=p_path)
    if matched_op is None:
        ops = list_operations(project_path=p_path, limit=200)
        for o in ops:
            if o.get("interaction_id") == interaction_id:
                matched_op = HistoryOperationRecord.from_dict(o)
                break

    # 查找关联快照
    before_snap_id = (
        (matched_op.before_snapshot_id if matched_op else None)
        or item.get("before_snapshot_id")
    )
    after_snap_id = (
        (matched_op.after_snapshot_id if matched_op else None)
        or item.get("after_snapshot_id")
    )

    before_snap = load_snapshot(before_snap_id, project_path=p_path) if before_snap_id else None
    after_snap = load_snapshot(after_snap_id, project_path=p_path) if after_snap_id else None

    diff_res = None
    if before_snap and after_snap:
        diff_res = diff_snapshots(before_snap, after_snap)

    return {
        "status": "success",
        "interaction": item,
        "operation": matched_op.to_dict() if matched_op else None,
        "before_snapshot": before_snap.to_dict() if before_snap else None,
        "after_snapshot": after_snap.to_dict() if after_snap else None,
        "diff": diff_res,
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
