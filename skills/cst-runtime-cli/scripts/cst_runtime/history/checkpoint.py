"""CST History 检查点清单管理与严格前缀恢复计划生成。

本模块属于纯 Python 领域逻辑，零 CST 依赖，100% 可离线测试。
包含轻量检查点元数据持久化、基线与目标前缀判定以及单步重放计划计算。
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Mapping

from .journal import resolve_history_root
from .models import HistoryOperationRecord, HistorySnapshot, _now_iso


def get_checkpoints_dir(root: Path) -> Path:
    checkpoints_dir = root / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    return checkpoints_dir


def save_history_checkpoint(
    snapshot: HistorySnapshot,
    checkpoint_name: str,
    description: str = "",
    *,
    checkpoint_id: str | None = None,
    storage_root: Path | None = None,
    project_path: str | None = None,
) -> dict[str, Any]:
    """保存一份轻量 History 检查点索引记录。"""
    root = storage_root or resolve_history_root(project_path=project_path or snapshot.project_path)
    cid = checkpoint_id or uuid.uuid4().hex
    record: dict[str, Any] = {
        "checkpoint_id": cid,
        "checkpoint_name": checkpoint_name.strip() or f"checkpoint_{cid[:8]}",
        "description": description.strip(),
        "created_at": _now_iso(),
        "project_path": snapshot.project_path,
        "project_name": snapshot.project_name,
        "cst_version": snapshot.cst_version,
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_sha256": snapshot.snapshot_sha256,
        "block_count": len(snapshot.blocks),
    }

    checkpoints_dir = get_checkpoints_dir(root)
    chk_file = checkpoints_dir / f"{cid}.json"
    temp_file = checkpoints_dir / f"{cid}.tmp.{uuid.uuid4().hex[:8]}"

    data_bytes = json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8")
    temp_file.write_bytes(data_bytes)
    temp_file.replace(chk_file)

    return {
        "status": "success",
        "checkpoint_id": cid,
        "checkpoint_file": str(chk_file),
        "checkpoint": record,
    }


def list_history_checkpoints(
    *,
    storage_root: Path | None = None,
    project_path: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """列出保存的轻量检查点。"""
    root = storage_root or resolve_history_root(project_path=project_path)
    checkpoints_dir = root / "checkpoints"
    if not checkpoints_dir.is_dir():
        return []

    checkpoints: list[dict[str, Any]] = []
    files = sorted(checkpoints_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["checkpoint_file"] = str(f)
            checkpoints.append(data)
            if len(checkpoints) >= limit:
                break
        except Exception:
            continue

    return checkpoints


def generate_restore_plan(
    baseline_snapshot: HistorySnapshot,
    target_snapshot: HistorySnapshot,
    operations: list[HistoryOperationRecord] | Mapping[str, HistoryOperationRecord] | None = None,
) -> dict[str, Any]:
    """根据严格前缀重放算法，生成从基线到目标的单步恢复计划。

    严格处理 4 类分支：
      情况一: 基线与目标完全相同 (already_at_target)
      情况二: 基线是目标的严格前缀 (prefix_suffix_replay)
      情况三: 基线比目标更长 (cannot_rewind_forward_replay)
      情况四: 基线与目标分叉 (diverged_history_branch)
    """
    b_blocks = baseline_snapshot.blocks
    t_blocks = target_snapshot.blocks
    len_b = len(b_blocks)
    len_t = len(t_blocks)

    # 情况一: 完全相同
    if baseline_snapshot.snapshot_sha256 == target_snapshot.snapshot_sha256 and len_b == len_t:
        return {
            "status": "success",
            "plan_type": "already_at_target",
            "can_execute": True,
            "message": "基线工程历史与目标快照完全一致，无需执行任何重放。",
            "baseline_sha256": baseline_snapshot.snapshot_sha256,
            "target_sha256": target_snapshot.snapshot_sha256,
            "baseline_block_count": len_b,
            "target_block_count": len_t,
            "steps": [],
        }

    # 检查 B 是否是 T 的严格前缀
    is_strict_prefix = False
    if len_b < len_t:
        prefix_matches = True
        for idx in range(len_b):
            b_blk = b_blocks[idx]
            t_blk = t_blocks[idx]
            if b_blk.name != t_blk.name or b_blk.contents_sha256 != t_blk.contents_sha256:
                prefix_matches = False
                break
        is_strict_prefix = prefix_matches

    # 情况二: B 是 T 的严格前缀 -> 计算缺失后缀
    if is_strict_prefix:
        from .models import compute_snapshot_sha256

        # 预计算目标快照各前缀切片的规范哈希
        prefix_hashes: list[str] = [
            compute_snapshot_sha256(t_blocks[:k])
            for k in range(len_t + 1)
        ]

        op_list: list[HistoryOperationRecord] = []
        if operations:
            raw_ops = list(operations.values()) if isinstance(operations, Mapping) else list(operations)
            op_list = [o if isinstance(o, HistoryOperationRecord) else HistoryOperationRecord.from_dict(o) for o in raw_ops]

        used_op_ids: set[str] = set()
        suffix_blocks = t_blocks[len_b:]
        steps: list[dict[str, Any]] = []
        all_have_business_vba = True

        for s_idx, t_blk in enumerate(suffix_blocks):
            global_idx = len_b + s_idx
            exp_before_sha = prefix_hashes[global_idx]
            exp_after_sha = prefix_hashes[global_idx + 1]
            step_num = s_idx + 1

            candidates = [
                op for op in op_list
                if op.operation_id not in used_op_ids
                and op.history_label == t_blk.name
                and op.business_vba
            ]
            exact_hash_candidates = [
                op for op in candidates
                if op.before_snapshot_sha256 == exp_before_sha
                and op.after_snapshot_sha256 == exp_after_sha
            ]

            matched_op: HistoryOperationRecord | None = None
            match_warning = ""
            if len(exact_hash_candidates) == 1:
                matched_op = exact_hash_candidates[0]
            elif len(exact_hash_candidates) > 1:
                match_warning = "存在多个前后快照哈希均相同的候选 operation，无法唯一确定重放脚本。"
            else:
                # 日志快照不完整时，仅允许用目标原始包装 VBA 中的 operation ID 唯一对齐；
                # 只按同名标签或列表顺序选择会在重复标签场景中重放错误脚本。
                id_candidates = []
                for op in candidates:
                    if not op.operation_id or op.operation_id not in t_blk.contents:
                        continue
                    before_conflict = bool(
                        op.before_snapshot_sha256
                        and op.before_snapshot_sha256 != exp_before_sha
                    )
                    after_conflict = bool(
                        op.after_snapshot_sha256
                        and op.after_snapshot_sha256 != exp_after_sha
                    )
                    if not before_conflict and not after_conflict:
                        id_candidates.append(op)
                if len(id_candidates) == 1:
                    matched_op = id_candidates[0]
                elif len(id_candidates) > 1:
                    match_warning = "目标原始 VBA 中匹配到多个 operation ID，恢复关系存在歧义。"
                elif candidates:
                    match_warning = "同名 operation 无法通过前后哈希或原始 VBA 中的 operation ID 精确对齐。"

            if matched_op and matched_op.business_vba:
                used_op_ids.add(matched_op.operation_id)
                steps.append({
                    "step": step_num,
                    "target_block_index": t_blk.index,
                    "label": t_blk.name,
                    "action": "submit_business_vba",
                    "business_vba": matched_op.business_vba,
                    "business_vba_sha256": matched_op.business_vba_sha256,
                    "operation_id": matched_op.operation_id,
                    "expected_before_snapshot_sha256": exp_before_sha,
                    "expected_after_snapshot_sha256": exp_after_sha,
                    "status": "ready",
                })
            else:
                all_have_business_vba = False
                steps.append({
                    "step": step_num,
                    "target_block_index": t_blk.index,
                    "label": t_blk.name,
                    "action": "manual_or_physical",
                    "raw_contents": t_blk.contents,
                    "expected_before_snapshot_sha256": exp_before_sha,
                    "expected_after_snapshot_sha256": exp_after_sha,
                    "status": "requires_manual_vba_or_physical_checkpoint",
                    "warning": (
                        f"历史块 [{t_blk.name}] 缺失可唯一验证的 clean business_vba 记录；"
                        f"{match_warning}"
                        "为防止嵌套网关或未预期副作用，禁止自动重放，需人工提供脚本或使用物理工程检查点恢复。"
                    ),
                })

        return {
            "status": "success",
            "plan_type": "prefix_suffix_replay",
            "can_execute": all_have_business_vba,
            "message": (
                f"基线为目标的严格前缀，需正向补齐 {len(suffix_blocks)} 个后缀历史块。"
                if all_have_business_vba
                else f"需补齐 {len(suffix_blocks)} 个后缀历史块，但部分步骤缺少业务 VBA 记录，禁止盲目自动重放。"
            ),
            "baseline_sha256": baseline_snapshot.snapshot_sha256,
            "target_sha256": target_snapshot.snapshot_sha256,
            "baseline_block_count": len_b,
            "target_block_count": len_t,
            "suffix_count": len(suffix_blocks),
            "steps": steps,
        }

    # 情况三: B 比 T 更长
    if len_b > len_t:
        return {
            "status": "error",
            "plan_type": "cannot_rewind_forward_replay",
            "can_execute": False,
            "message": (
                f"基线历史长度 ({len_b}) 大于目标历史长度 ({len_t})，"
                "无法通过正向追加重放实现历史回退！必须寻找包含目标版本的物理工程检查点，"
                "或从更早的基线/空白工程新建副本重新执行至目标状态。"
            ),
            "baseline_sha256": baseline_snapshot.snapshot_sha256,
            "target_sha256": target_snapshot.snapshot_sha256,
            "baseline_block_count": len_b,
            "target_block_count": len_t,
            "steps": [],
        }

    # 情况四: 分叉 (Diverged)
    return {
        "status": "error",
        "plan_type": "diverged_history_branch",
        "can_execute": False,
        "message": (
            "基线工程历史与目标工程历史已发生分叉（前缀不匹配）！"
            "严禁直接向当前基线追加目标操作，否则会导致严重的几何/参数冲突。"
            "必须从两者的共同前缀物理检查点（或空白基线）创建新工程副本再执行目标分支。"
        ),
        "baseline_sha256": baseline_snapshot.snapshot_sha256,
        "target_sha256": target_snapshot.snapshot_sha256,
        "baseline_block_count": len_b,
        "target_block_count": len_t,
        "steps": [],
    }
