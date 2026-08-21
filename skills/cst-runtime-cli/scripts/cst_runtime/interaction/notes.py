"""Agent 与用户显式工作说明 (AgentWorkNote) 的管理与查询。"""
from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path
from typing import Any

from .journal import get_session_storage_root
from .models import AgentWorkNote, _now_iso

_NOTES_LOCK = threading.RLock()


def get_notes_journal_path(storage_root: Path) -> Path:
    return storage_root / "agent_work_notes.jsonl"


def record_work_note(
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
    workspace: str | None = None,
    session_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """显式追加一条工作说明、设计决策或人工处置结论。"""
    if not content or not content.strip():
        raise ValueError("笔记内容 content 不能为空")

    note_id = uuid.uuid4().hex
    note = AgentWorkNote(
        note_id=note_id,
        content=content.strip(),
        category=category.strip(),
        timestamp=_now_iso(),
        task_id=task_id,
        run_id=run_id,
        project_path=project_path,
        interaction_id=interaction_id,
        operation_id=operation_id,
        snapshot_id=snapshot_id,
        user_confirmed=user_confirmed,
        author=author,
        extra=dict(extra or {}),
    )

    storage_root = get_session_storage_root(
        session_id=session_id,
        workspace=workspace,
    )
    notes_path = get_notes_journal_path(storage_root)
    line = json.dumps(note.to_dict(), ensure_ascii=False, default=str)

    with _NOTES_LOCK:
        with notes_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()

    return {
        "status": "success",
        "note_id": note_id,
        "notes_file": str(notes_path),
        "note": note.to_dict(),
    }


def list_work_notes(
    *,
    workspace: str | None = None,
    session_id: str | None = None,
    task_id: str | None = None,
    run_id: str | None = None,
    project_path: str | None = None,
    interaction_id: str | None = None,
    operation_id: str | None = None,
    category: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查询显式工作笔记（最新排在前面）。"""
    storage_root = get_session_storage_root(
        session_id=session_id,
        workspace=workspace,
    )
    notes_path = get_notes_journal_path(storage_root)
    if not notes_path.is_file():
        return []

    lines: list[str] = []
    with _NOTES_LOCK:
        raw_text = notes_path.read_text(encoding="utf-8")
        lines = raw_text.splitlines()

    items: list[dict[str, Any]] = []
    for idx, line in enumerate(reversed(lines)):
        line_str = line.strip()
        if not line_str:
            continue
        try:
            item = json.loads(line_str)
        except Exception:
            continue

        if task_id and item.get("task_id") != task_id:
            continue
        if run_id and item.get("run_id") != run_id:
            continue
        if category and item.get("category") != category:
            continue
        if interaction_id and item.get("interaction_id") != interaction_id:
            continue
        if operation_id and item.get("operation_id") != operation_id:
            continue
        if project_path:
            p1 = item.get("project_path")
            if p1 and Path(p1).resolve() != Path(project_path).resolve():
                continue

        items.append(item)
        if len(items) >= limit:
            break

    return items
