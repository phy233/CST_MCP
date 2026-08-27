"""History 版本管理、快照、检查点与恢复工具定义与 Handler。"""
from __future__ import annotations

from typing import Any
from . import _register_tool_defs

TOOL_DEFS = {
    "list-history-log": {
        "category": "history",
        "risk": "read",
        "description": (
            "Use this to filter persisted CST History operation records and snapshot-hash "
            "changes when diagnosing or auditing a run. It is read-only and should not be "
            "called after every successful CST write."
        ),
        "handler": "tool_list_history_log",
        "json_schema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\project.cst"],
                },
                "execution_state": {
                    "type": "string",
                    "examples": ["succeeded", "failed", "interrupted"],
                },
                "reconciliation_state": {
                    "type": "string",
                    "examples": ["applied", "not_applied", "ambiguous", "reconciled"],
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
    "diff-history-snapshots": {
        "category": "history",
        "risk": "read",
        "description": (
            "Use this to compare two saved History snapshots and return block-level changes "
            "plus a unified diff of raw VBA. It does not modify the project or prove later CST "
            "execution."
        ),
        "handler": "tool_diff_history_snapshots",
        "json_schema": {
            "type": "object",
            "properties": {
                "before_snapshot_id": {
                    "type": "string",
                    "examples": ["snap_001"],
                },
                "after_snapshot_id": {
                    "type": "string",
                    "examples": ["snap_002"],
                },
                "project_path": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\project.cst"],
                },
            },
            "required": ["before_snapshot_id", "after_snapshot_id"],
        },
    },
    "generate-restore-plan": {
        "category": "history",
        "risk": "read",
        "description": (
            "Use this to create a read-only replay plan when a target History snapshot is a "
            "strict prefix extension of a baseline project. It plans recovery only; actual "
            "replay is a separate CLI-only action."
        ),
        "handler": "tool_generate_restore_plan",
        "json_schema": {
            "type": "object",
            "properties": {
                "baseline_project_path": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\baseline.cst"],
                },
                "target_snapshot_id": {
                    "type": "string",
                    "examples": ["snap_target"],
                },
            },
            "required": ["baseline_project_path", "target_snapshot_id"],
        },
    },
    "inspect-history-capabilities": {
        "category": "history",
        "risk": "read",
        "description": "探测当前 CST 环境对 _GetHistory 等历史接口的支持状态。",
        "handler": "tool_inspect_history_capabilities",
        "json_schema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\project.cst"],
                },
            },
            "required": ["project_path"],
        },
    },
    "export-history-snapshot": {
        "category": "history",
        "risk": "read",
        "description": "从当前 CST 工程导出 History 原始快照并保存为 JSON 文件。",
        "handler": "tool_export_history_snapshot",
        "json_schema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\project.cst"],
                },
                "reason": {
                    "type": "string",
                    "default": "manual_export",
                    "examples": ["manual_export"],
                },
            },
            "required": ["project_path"],
        },
    },
    "inspect-history-status": {
        "category": "history",
        "risk": "read",
        "description": "检查当前工程是否存在未正常闭合或中断的 History 操作并给出恢复建议。",
        "handler": "tool_inspect_history_status",
        "json_schema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\project.cst"],
                },
            },
            "required": [],
        },
    },
    "create-history-checkpoint": {
        "category": "history",
        "risk": "filesystem-write",
        "description": "基于当前工程 History 状态创建一份轻量检查点记录。",
        "handler": "tool_create_history_checkpoint",
        "json_schema": {
            "type": "object",
            "properties": {
                "checkpoint_name": {
                    "type": "string",
                    "examples": ["before_mesh_opt"],
                },
                "description": {
                    "type": "string",
                    "examples": ["网格优化前的轻量快照"],
                },
                "project_path": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\project.cst"],
                },
            },
            "required": ["checkpoint_name", "project_path"],
        },
    },
    "create-project-checkpoint": {
        "category": "history",
        "risk": "filesystem-write",
        "description": "显式保存并关闭目标工程、验证锁释放后创建物理工程全量副本（.cst 与伴随目录）。",
        "handler": "tool_create_project_checkpoint",
        "json_schema": {
            "type": "object",
            "properties": {
                "checkpoint_dir": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\checkpoints\\chk_001"],
                },
                "project_path": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\project.cst"],
                },
                "description": {
                    "type": "string",
                    "examples": ["物理工程备份"],
                },
            },
            "required": ["checkpoint_dir", "project_path"],
        },
    },
    "checkout-replay-copy": {
        "category": "history",
        "risk": "write",
        "description": "保存并关闭基线工程后，在新的隔离副本中按严格前缀逐步重放业务 VBA。",
        "handler": "tool_checkout_replay_copy",
        "json_schema": {
            "type": "object",
            "properties": {
                "baseline_project_path": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\baseline.cst"],
                },
                "target_snapshot_id": {
                    "type": "string",
                    "examples": ["snap_target"],
                },
                "new_copy_path": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\replayed_copy.cst"],
                },
            },
            "required": ["baseline_project_path", "target_snapshot_id", "new_copy_path"],
        },
    },
    "reconcile-history-operation": {
        "category": "history",
        "risk": "filesystem-write",
        "description": "人工介入核对并显式处置一个歧义或中断的 History 操作。",
        "handler": "tool_reconcile_history_operation",
        "json_schema": {
            "type": "object",
            "properties": {
                "operation_id": {
                    "type": "string",
                    "examples": ["op_12345"],
                },
                "decision": {
                    "type": "string",
                    "examples": ["applied", "not_applied", "discarded", "replayed_manually"],
                },
                "notes": {
                    "type": "string",
                    "examples": ["经人工核对 CST 模型树，该操作已生效。"],
                },
                "project_path": {
                    "type": "string",
                    "examples": ["C:\\path\\to\\project.cst"],
                },
            },
            "required": ["operation_id", "decision", "notes"],
        },
    },
}


# --- Handlers ---

from ..lib import history as _history_lib
from ..history.recovery import reconcile_operation


def tool_list_history_log(args: dict) -> dict:
    records = _history_lib.list_history_log(
        project_path=args.get("project_path"),
        execution_state=args.get("execution_state"),
        reconciliation_state=args.get("reconciliation_state"),
        limit=int(args.get("limit", 50)),
    )
    return {
        "status": "success",
        "count": len(records),
        "operations": records,
    }


def tool_diff_history_snapshots(args: dict) -> dict:
    return _history_lib.diff_history_snapshots(
        before_snapshot_id=str(args["before_snapshot_id"]),
        after_snapshot_id=str(args["after_snapshot_id"]),
        project_path=args.get("project_path"),
    )


def tool_generate_restore_plan(args: dict) -> dict:
    return _history_lib.plan_restore(
        baseline_project_path=str(args["baseline_project_path"]),
        target_snapshot_id=str(args["target_snapshot_id"]),
    )


def tool_inspect_history_capabilities(args: dict) -> dict:
    return {
        "status": "success",
        "capabilities": _history_lib.inspect_capabilities(project_path=args.get("project_path")),
    }


def tool_export_history_snapshot(args: dict) -> dict:
    return _history_lib.export_history_snapshot(
        project_path=args.get("project_path"),
        reason=str(args.get("reason", "manual_export")),
    )


def tool_inspect_history_status(args: dict) -> dict:
    status_info = _history_lib.inspect_status(project_path=args.get("project_path"))
    return {
        "status": "success",
        **status_info,
    }


def tool_create_history_checkpoint(args: dict) -> dict:
    return _history_lib.create_checkpoint(
        checkpoint_name=str(args["checkpoint_name"]),
        description=str(args.get("description", "")),
        project_path=args.get("project_path"),
    )


def tool_create_project_checkpoint(args: dict) -> dict:
    return _history_lib.create_physical_checkpoint(
        checkpoint_dir=str(args["checkpoint_dir"]),
        description=str(args.get("description", "")),
        project_path=args.get("project_path"),
    )


def tool_checkout_replay_copy(args: dict) -> dict:
    return _history_lib.replay_to_copy(
        baseline_project_path=str(args["baseline_project_path"]),
        target_snapshot_id=str(args["target_snapshot_id"]),
        new_copy_path=str(args["new_copy_path"]),
    )


def tool_reconcile_history_operation(args: dict) -> dict:
    return reconcile_operation(
        operation_id=str(args["operation_id"]),
        decision=str(args["decision"]),
        notes=str(args["notes"]),
        project_path=args.get("project_path"),
    )


_register_tool_defs(TOOL_DEFS)
