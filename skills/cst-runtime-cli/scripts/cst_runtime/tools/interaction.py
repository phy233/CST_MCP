"""Agent 与 MCP 交互日志查询及显式工作笔记 (AgentWorkNote) 工具定义与 Handler。"""
from __future__ import annotations

from typing import Any
from . import _register_tool_defs

TOOL_DEFS = {
    "list-interaction-log": {
        "category": "interaction",
        "risk": "read",
        "description": "查询 MCP 工具调用的全生命周期交互日志流。",
        "handler": "tool_list_interaction_log",
        "json_schema": {
            "type": "object",
            "properties": {
                "workspace": {
                    "type": "string",
                    "description": "交互日志所属工作区；省略时使用当前配置工作区。",
                },
                "project_path": {
                    "type": "string",
                    "description": "按关联 CST 工程路径过滤。",
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
        "description": "查询单次 MCP 工具调用关联的 History 快照及 Operation 详细变更。",
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
                    "description": "交互日志所属工作区；省略时使用当前配置工作区。",
                },
                "project_path": {
                    "type": "string",
                    "description": "关联 CST 工程路径；日志未携带路径时可显式提供。",
                },
            },
            "required": ["interaction_id"],
        },
    },
    "record-agent-note": {
        "category": "interaction",
        "risk": "filesystem-write",
        "description": "显式记录 Agent 或用户的阶段工作说明、关键设计决策或人工处置结论。",
        "handler": "tool_record_agent_note",
        "json_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "examples": ["决定将天线工作频率从 5.8GHz 调整为 5.2GHz。"],
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
            },
            "required": ["content"],
        },
    },
    "list-agent-notes": {
        "category": "interaction",
        "risk": "read",
        "description": "查询已持久化的 Agent 显式工作说明与人工处置笔记列表。",
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
