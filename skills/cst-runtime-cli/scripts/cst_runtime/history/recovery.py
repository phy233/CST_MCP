"""CST History 断点恢复判定机与人工对齐 (Reconciliation)。

负责在进程中断、崩溃后，根据当前工程快照与崩溃前记录判定操作生效状态
（not_applied / applied / ambiguous），并提供显式的人工处置通道。
本模块为纯 Python 领域逻辑，100% 可离线测试。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .journal import append_operation, get_operation, resolve_history_root
from .models import HistoryOperationRecord, HistorySnapshot, _now_iso


def evaluate_interrupted_operation(
    operation: HistoryOperationRecord,
    current_snapshot: HistorySnapshot,
) -> dict[str, Any]:
    """对一个未正常闭合或中断的 operation 进行生效状态判定。"""
    curr_sha = current_snapshot.snapshot_sha256
    before_sha = operation.before_snapshot_sha256
    after_sha = operation.after_snapshot_sha256

    # 规则 1: 快照哈希完全等于 expected_before
    if before_sha and curr_sha == before_sha:
        return {
            "status": "success",
            "operation_id": operation.operation_id,
            "reconciliation_state": "not_applied",
            "reason": "current_snapshot_matches_before",
            "message": "工程历史与提交前一致，该操作大概率未被 CST 执行应用。",
            "can_retry": True,
            "recommendation": "用户明确确认后可重新提交该操作。",
        }

    # 规则 2: 快照哈希完全等于 expected_after
    if after_sha and curr_sha == after_sha:
        return {
            "status": "success",
            "operation_id": operation.operation_id,
            "reconciliation_state": "applied",
            "reason": "current_snapshot_matches_after",
            "message": "工程历史与提交后快照完全一致，该操作已在 CST 中生效。",
            "can_retry": False,
            "recommendation": "自动标记为已应用，禁止重复执行，防止模型几何冲突。",
        }

    # 规则 3: 当 before/after 快照哈希已记录但当前与两者均不相等时 -> 歧义/分叉
    if before_sha or after_sha:
        return {
            "status": "success",
            "operation_id": operation.operation_id,
            "reconciliation_state": "ambiguous",
            "reason": "hash_mismatch_ambiguity",
            "message": "当前工程历史与期望前后快照均不匹配，存在歧义或分叉状态。",
            "can_retry": False,
            "recommendation": "【安全铁律】绝对禁止自动重试！必须由人工排查并显式标记处置结论 (reconcile)。",
        }

    # 规则 4: 未记录快照哈希时的降级兜底：基于标签与业务代码交叉校验
    blocks = current_snapshot.blocks
    matching_label_blocks = [b for b in blocks if b.name == operation.history_label]

    if not matching_label_blocks:
        return {
            "status": "success",
            "operation_id": operation.operation_id,
            "reconciliation_state": "not_applied",
            "reason": "history_label_absent",
            "message": "当前工程 History 中未找到该操作的标签，操作未生效。",
            "can_retry": True,
            "recommendation": "用户明确确认后可重新提交。",
        }

    if len(matching_label_blocks) == 1:
        matched_block = matching_label_blocks[0]
        if operation.business_vba and operation.business_vba in matched_block.contents:
            return {
                "status": "success",
                "operation_id": operation.operation_id,
                "reconciliation_state": "applied",
                "reason": "business_vba_found_in_single_matching_block",
                "message": "当前工程已包含该标签及业务 VBA 内容，操作已生效。",
                "can_retry": False,
                "recommendation": "自动标记为已应用，禁止重复重试。",
            }

    return {
        "status": "success",
        "operation_id": operation.operation_id,
        "reconciliation_state": "ambiguous",
        "reason": "fallback_block_mismatch_ambiguity",
        "message": "当前工程历史存在歧义状态，无法确定是否已应用。",
        "can_retry": False,
        "recommendation": "【安全铁律】绝对禁止自动重试！必须由人工排查并显式标记处置结论 (reconcile)。",
    }


def reconcile_operation(
    operation_id: str,
    decision: str,
    notes: str,
    *,
    project_path: str | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    """人工介入将一个 operation 标记为 reconciled。"""
    root = storage_root or resolve_history_root(project_path=project_path)
    op = get_operation(operation_id, storage_root=root, project_path=project_path)
    if op is None:
        raise ValueError(f"未找到 operation_id={operation_id} 的记录")

    if not notes or not notes.strip():
        raise ValueError("人工处置说明 notes 不能为空")

    valid_decisions = {"applied", "not_applied", "discarded", "replayed_manually"}
    if decision not in valid_decisions:
        raise ValueError(f"无效的处置决定 decision={decision!r}；允许值: {sorted(valid_decisions)}")

    op.reconciliation_state = "reconciled"
    op.reconciliation_notes = f"[{decision}] {notes.strip()} (at {_now_iso()})"

    append_operation(op, storage_root=root, project_path=project_path)

    return {
        "status": "success",
        "operation_id": operation_id,
        "decision": decision,
        "reconciliation_state": op.reconciliation_state,
        "reconciliation_notes": op.reconciliation_notes,
    }
