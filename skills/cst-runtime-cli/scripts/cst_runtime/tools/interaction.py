"""Agent 与 MCP 交互日志查询及显式工作笔记 (AgentWorkNote) 工具定义与 Handler。"""
from __future__ import annotations

from typing import Any
from . import _register_tool_defs

TOOL_DEFS = {
    "list-interaction-log": {
        "category": "interaction",
        "risk": "read",
        "description": (
            "Use this to filter the persisted lifecycle log of MCP tool calls by workspace, "
            "project, task, run, tool, or interaction ID. Use inspect-interaction-history for "
            "one call's linked History changes."
        ),
        "handler": "tool_list_interaction_log",
        "json_schema": {
            "type": "object",
            "properties": {
                "workspace": {
                    "type": "string",
                    "description": "Runtime workspace that owns the interaction log; omit it to use the configured workspace.",
                },
                "project_path": {
                    "type": "string",
                    "description": "Filter by the associated CST project path.",
                },
                "task_id": {
                    "type": "string",
                    "examples": ["task_001"],
                },
                "run_id": {
                    "type": "string",
                    "examples": ["run_001"],
                },
                "tool_name": {
                    "type": "string",
                    "examples": ["define-brick"],
                },
                "interaction_id": {
                    "type": "string",
                    "examples": ["int_12345"],
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "examples": [50],
                },
            },
            "required": [],
        },
    },
    "inspect-interaction-history": {
        "category": "interaction",
        "risk": "read",
        "description": (
            "Use this with a known interaction_id to inspect its linked History snapshots and "
            "detailed operation changes. Use list-interaction-log first only when the ID is "
            "unknown."
        ),
        "handler": "tool_inspect_interaction_history",
        "json_schema": {
            "type": "object",
            "properties": {
                "interaction_id": {
                    "type": "string",
                    "examples": ["int_12345"],
                },
                "workspace": {
                    "type": "string",
                    "description": "Runtime workspace that owns the interaction log; omit it to use the configured workspace.",
                },
                "project_path": {
                    "type": "string",
                    "description": "Associated CST project path; provide it explicitly when the log record has no path.",
                },
            },
            "required": ["interaction_id"],
        },
    },
    "record-agent-note": {
        "category": "interaction",
        "risk": "filesystem-write",
        "description": (
            "Use this to persist an explicit Agent or user note about a plan, design decision, "
            "confirmation, milestone, or manual reconciliation. It records context only and "
            "does not prove CST execution."
        ),
        "handler": "tool_record_agent_note",
        "json_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "examples": ["Change the antenna operating frequency from 5.8 GHz to 5.2 GHz."],
                },
                "category": {
                    "type": "string",
                    "default": "general",
                    "examples": ["plan", "decision", "user_confirmation", "milestone", "reconciliation"],
                },
                "task_id": {
                    "type": "string",
                    "examples": ["task_001"],
                },
                "run_id": {
                    "type": "string",
                    "examples": ["run_001"],
                },
                "project_path": {
                    "type": "string",
                    "description": "CST project path associated with the note.",
                },
                "user_confirmed": {
                    "type": "boolean",
                    "examples": [True],
                },
                "interaction_id": {
                    "type": "string",
                    "examples": ["int_12345"],
                },
                "operation_id": {
                    "type": "string",
                    "examples": ["op_12345"],
                },
                "snapshot_id": {
                    "type": "string",
                    "examples": ["snapshot_12345"],
                },
            },
            "required": ["content"],
        },
    },
    "list-agent-notes": {
        "category": "interaction",
        "risk": "read",
        "description": (
            "Use this to retrieve persisted Agent or user notes by task, run, project, or "
            "category. Unlike list-interaction-log, it returns explicit work notes rather than "
            "tool-call lifecycle events."
        ),
        "handler": "tool_list_agent_notes",
        "json_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "examples": ["task_001"],
                },
                "run_id": {
                    "type": "string",
                    "examples": ["run_001"],
                },
                "project_path": {
                    "type": "string",
                    "description": "Filter by the CST project path associated with the note.",
                },
                "category": {
                    "type": "string",
                    "examples": ["decision"],
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "examples": [50],
                },
            },
            "required": [],
        },
    },
}


# --- Handlers ---

from ..lib import interaction as _interaction_lib


def tool_list_interaction_log(args: dict) -> dict:
    records = _interaction_lib.list_interaction_log(
        workspace=args.get("workspace"),
        task_id=args.get("task_id"),
        run_id=args.get("run_id"),
        project_path=args.get("project_path"),
        tool_name=args.get("tool_name"),
        interaction_id=args.get("interaction_id"),
        limit=int(args.get("limit", 50)),
    )
    return {
        "status": "success",
        "count": len(records),
        "interactions": records,
    }


def tool_inspect_interaction_history(args: dict) -> dict:
    return _interaction_lib.inspect_interaction_history(
        interaction_id=str(args["interaction_id"]),
        project_path=args.get("project_path"),
        workspace=args.get("workspace"),
    )


def tool_record_agent_note(args: dict) -> dict:
    return _interaction_lib.add_agent_note(
        content=str(args["content"]),
        category=str(args.get("category", "general")),
        task_id=args.get("task_id"),
        run_id=args.get("run_id"),
        project_path=args.get("project_path"),
        interaction_id=args.get("interaction_id"),
        operation_id=args.get("operation_id"),
        snapshot_id=args.get("snapshot_id"),
        user_confirmed=args.get("user_confirmed"),
    )


def tool_list_agent_notes(args: dict) -> dict:
    records = _interaction_lib.list_agent_notes(
        task_id=args.get("task_id"),
        run_id=args.get("run_id"),
        project_path=args.get("project_path"),
        category=args.get("category"),
        limit=int(args.get("limit", 50)),
    )
    return {
        "status": "success",
        "count": len(records),
        "notes": records,
    }


_register_tool_defs(TOOL_DEFS)
