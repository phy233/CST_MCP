"""cst_runtime.history — 纯 Python CST History 版本管理、快照、差异与恢复包。"""
from __future__ import annotations

from .checkpoint import (
    generate_restore_plan,
    list_history_checkpoints,
    save_history_checkpoint,
)
from .diff import BlockDiff, diff_snapshots
from .journal import (
    append_operation,
    get_operation,
    list_operations,
    list_snapshots,
    load_snapshot,
    resolve_history_root,
    save_snapshot,
)
from .models import (
    HistoryBlock,
    HistoryOperationRecord,
    HistorySnapshot,
    compute_snapshot_sha256,
)
from .recovery import evaluate_interrupted_operation, reconcile_operation

__all__ = [
    "HistoryBlock",
    "HistorySnapshot",
    "HistoryOperationRecord",
    "compute_snapshot_sha256",
    "BlockDiff",
    "diff_snapshots",
    "save_snapshot",
    "load_snapshot",
    "list_snapshots",
    "append_operation",
    "get_operation",
    "list_operations",
    "resolve_history_root",
    "evaluate_interrupted_operation",
    "reconcile_operation",
    "save_history_checkpoint",
    "list_history_checkpoints",
    "generate_restore_plan",
]
