"""cst_runtime.interaction — Agent 与 MCP 交互日志、内容寻址存储与显式工作笔记。"""
from __future__ import annotations

from .journal import (
    append_interaction_event,
    get_session_storage_root,
    list_interactions,
    read_payload_reference,
    store_payload_if_large,
)
from .models import AgentWorkNote, MCPInteractionRecord, PayloadReference
from .notes import list_work_notes, record_work_note

__all__ = [
    "MCPInteractionRecord",
    "AgentWorkNote",
    "PayloadReference",
    "append_interaction_event",
    "get_session_storage_root",
    "list_interactions",
    "read_payload_reference",
    "store_payload_if_large",
    "record_work_note",
    "list_work_notes",
]
