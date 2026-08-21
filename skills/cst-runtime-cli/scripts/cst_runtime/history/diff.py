"""CST History 快照差异比对引擎。

负责比较任意两个 HistorySnapshot，识别新增、删除、移动、修改及未改变的块，
并生成原始 VBA 内容的统一 diff。本模块为纯 Python 算法，完全可离线测试。
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Any, Mapping

from .models import HistoryBlock, HistorySnapshot


@dataclass
class BlockDiff:
    """单个 History 块的差异详情。"""

    change_type: str  # unchanged, added, deleted, modified, moved, ambiguous
    before_index: int | None = None
    after_index: int | None = None
    before_name: str | None = None
    after_name: str | None = None
    field_changes: dict[str, dict[str, Any]] = field(default_factory=dict)
    vba_unified_diff: str = ""
    before_sha256: str | None = None
    after_sha256: str | None = None
    ambiguity_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "change_type": self.change_type,
            "before_index": self.before_index,
            "after_index": self.after_index,
            "before_name": self.before_name,
            "after_name": self.after_name,
            "before_sha256": self.before_sha256,
            "after_sha256": self.after_sha256,
        }
        if self.field_changes:
            res["field_changes"] = self.field_changes
        if self.vba_unified_diff:
            res["vba_unified_diff"] = self.vba_unified_diff
        if self.ambiguity_reason:
            res["ambiguity_reason"] = self.ambiguity_reason
        return res


def _compare_block_fields(
    b1: HistoryBlock,
    b2: HistoryBlock,
) -> dict[str, dict[str, Any]]:
    """比对两个块的属性差异（不包含 contents）。"""
    changes: dict[str, dict[str, Any]] = {}
    for attr in ("name", "version", "error", "exclude", "hide", "has_undo"):
        v1 = getattr(b1, attr)
        v2 = getattr(b2, attr)
        if v1 != v2:
            changes[attr] = {"before": v1, "after": v2}
    if b1.extra_fields != b2.extra_fields:
        all_keys = set(b1.extra_fields) | set(b2.extra_fields)
        for k in sorted(all_keys):
            ev1 = b1.extra_fields.get(k)
            ev2 = b2.extra_fields.get(k)
            if ev1 != ev2:
                changes[f"extra.{k}"] = {"before": ev1, "after": ev2}
    return changes


def _make_unified_diff(
    before_text: str,
    after_text: str,
    fromfile: str = "before.vba",
    tofile: str = "after.vba",
) -> str:
    """生成原始 VBA 统一 diff 字符串。"""
    before_lines = before_text.splitlines(keepends=True)
    after_lines = after_text.splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=fromfile,
            tofile=tofile,
        )
    )


def diff_snapshots(
    before: HistorySnapshot,
    after: HistorySnapshot,
) -> dict[str, Any]:
    """比对两个 History 快照并返回结构化差异报告。"""
    before_blocks = before.blocks
    after_blocks = after.blocks

    is_identical = before.snapshot_sha256 == after.snapshot_sha256
    if is_identical and len(before_blocks) == len(after_blocks):
        unchanged_list = [
            BlockDiff(
                change_type="unchanged",
                before_index=b.index,
                after_index=b.index,
                before_name=b.name,
                after_name=b.name,
                before_sha256=b.contents_sha256,
                after_sha256=b.contents_sha256,
            ).to_dict()
            for b in before_blocks
        ]
        return {
            "status": "success",
            "is_identical": True,
            "before_snapshot_id": before.snapshot_id,
            "after_snapshot_id": after.snapshot_id,
            "before_sha256": before.snapshot_sha256,
            "after_sha256": after.snapshot_sha256,
            "summary": {
                "before_count": len(before_blocks),
                "after_count": len(after_blocks),
                "added_count": 0,
                "deleted_count": 0,
                "modified_count": 0,
                "moved_count": 0,
                "unchanged_count": len(before_blocks),
                "ambiguous_count": 0,
            },
            "changes": unchanged_list,
        }

    # 匹配算法：基于位置、内容哈希、名称的多阶段对齐
    unmatched_before = list(range(len(before_blocks)))
    unmatched_after = list(range(len(after_blocks)))

    matched_pairs: list[tuple[int, int, str]] = []  # (b_idx, a_idx, match_type)

    # 阶段 1: 绝对精确匹配 (相同 index, 相同 content_sha256, 相同 name)
    for b_idx in list(unmatched_before):
        if b_idx in unmatched_after:
            b_blk = before_blocks[b_idx]
            a_blk = after_blocks[b_idx]
            if b_blk.contents_sha256 == a_blk.contents_sha256 and b_blk.name == a_blk.name:
                field_diffs = _compare_block_fields(b_blk, a_blk)
                if not field_diffs:
                    matched_pairs.append((b_idx, b_idx, "unchanged"))
                else:
                    matched_pairs.append((b_idx, b_idx, "modified_fields_only"))
                unmatched_before.remove(b_idx)
                unmatched_after.remove(b_idx)

    # 阶段 2: 内容哈希完全相同但位置发生移动 (moved)
    for b_idx in list(unmatched_before):
        b_blk = before_blocks[b_idx]
        candidates = [
            a_idx for a_idx in unmatched_after
            if after_blocks[a_idx].contents_sha256 == b_blk.contents_sha256 and after_blocks[a_idx].name == b_blk.name
        ]
        if len(candidates) == 1:
            a_idx = candidates[0]
            matched_pairs.append((b_idx, a_idx, "moved"))
            unmatched_before.remove(b_idx)
            unmatched_after.remove(a_idx)
        elif len(candidates) > 1:
            candidates.sort(key=lambda x: abs(x - b_idx))
            a_idx = candidates[0]
            matched_pairs.append((b_idx, a_idx, "moved"))
            unmatched_before.remove(b_idx)
            unmatched_after.remove(a_idx)

    # 阶段 3: 相同位置且相同名称但内容修改 (modified)
    for b_idx in list(unmatched_before):
        if b_idx in unmatched_after:
            b_blk = before_blocks[b_idx]
            a_blk = after_blocks[b_idx]
            if b_blk.name == a_blk.name:
                matched_pairs.append((b_idx, b_idx, "modified"))
                unmatched_before.remove(b_idx)
                unmatched_after.remove(b_idx)

    # 阶段 4: 同名块在不同位置的内容修改
    for b_idx in list(unmatched_before):
        b_blk = before_blocks[b_idx]
        candidates = [
            a_idx for a_idx in unmatched_after
            if after_blocks[a_idx].name == b_blk.name
        ]
        if len(candidates) == 1:
            a_idx = candidates[0]
            matched_pairs.append((b_idx, a_idx, "modified_and_moved"))
            unmatched_before.remove(b_idx)
            unmatched_after.remove(a_idx)

    # 汇总差异项
    diff_records: list[BlockDiff] = []

    for b_idx, a_idx, mtype in matched_pairs:
        b_blk = before_blocks[b_idx]
        a_blk = after_blocks[a_idx]
        field_diffs = _compare_block_fields(b_blk, a_blk)

        if mtype == "unchanged":
            diff_records.append(
                BlockDiff(
                    change_type="unchanged",
                    before_index=b_blk.index,
                    after_index=a_blk.index,
                    before_name=b_blk.name,
                    after_name=a_blk.name,
                    before_sha256=b_blk.contents_sha256,
                    after_sha256=a_blk.contents_sha256,
                )
            )
        elif mtype == "modified_fields_only":
            diff_records.append(
                BlockDiff(
                    change_type="modified",
                    before_index=b_blk.index,
                    after_index=a_blk.index,
                    before_name=b_blk.name,
                    after_name=a_blk.name,
                    field_changes=field_diffs,
                    before_sha256=b_blk.contents_sha256,
                    after_sha256=a_blk.contents_sha256,
                )
            )
        elif mtype == "moved":
            diff_records.append(
                BlockDiff(
                    change_type="moved",
                    before_index=b_blk.index,
                    after_index=a_blk.index,
                    before_name=b_blk.name,
                    after_name=a_blk.name,
                    field_changes=field_diffs,
                    before_sha256=b_blk.contents_sha256,
                    after_sha256=a_blk.contents_sha256,
                )
            )
        elif mtype in ("modified", "modified_and_moved"):
            vba_diff = _make_unified_diff(
                b_blk.contents,
                a_blk.contents,
                fromfile=f"block_{b_blk.index}_{b_blk.name}.vba",
                tofile=f"block_{a_blk.index}_{a_blk.name}.vba",
            )
            diff_records.append(
                BlockDiff(
                    change_type="modified",
                    before_index=b_blk.index,
                    after_index=a_blk.index,
                    before_name=b_blk.name,
                    after_name=a_blk.name,
                    field_changes=field_diffs,
                    vba_unified_diff=vba_diff,
                    before_sha256=b_blk.contents_sha256,
                    after_sha256=a_blk.contents_sha256,
                )
            )

    # 剩余未匹配的 before_blocks 视为 deleted
    for b_idx in unmatched_before:
        b_blk = before_blocks[b_idx]
        diff_records.append(
            BlockDiff(
                change_type="deleted",
                before_index=b_blk.index,
                after_index=None,
                before_name=b_blk.name,
                after_name=None,
                before_sha256=b_blk.contents_sha256,
                after_sha256=None,
            )
        )

    # 剩余未匹配的 after_blocks 视为 added
    for a_idx in unmatched_after:
        a_blk = after_blocks[a_idx]
        diff_records.append(
            BlockDiff(
                change_type="added",
                before_index=None,
                after_index=a_blk.index,
                before_name=None,
                after_name=a_blk.name,
                before_sha256=None,
                after_sha256=a_blk.contents_sha256,
            )
        )

    # 排序：优先按 after_index，无 after_index 的按 before_index
    def sort_key(d: BlockDiff) -> tuple[int, int]:
        primary = d.after_index if d.after_index is not None else 999999
        secondary = d.before_index if d.before_index is not None else 999999
        return (primary, secondary)

    diff_records.sort(key=sort_key)

    counts = {
        "before_count": len(before_blocks),
        "after_count": len(after_blocks),
        "added_count": sum(1 for d in diff_records if d.change_type == "added"),
        "deleted_count": sum(1 for d in diff_records if d.change_type == "deleted"),
        "modified_count": sum(1 for d in diff_records if d.change_type == "modified"),
        "moved_count": sum(1 for d in diff_records if d.change_type == "moved"),
        "unchanged_count": sum(1 for d in diff_records if d.change_type == "unchanged"),
        "ambiguous_count": sum(1 for d in diff_records if d.change_type == "ambiguous"),
    }

    return {
        "status": "success",
        "is_identical": False,
        "before_snapshot_id": before.snapshot_id,
        "after_snapshot_id": after.snapshot_id,
        "before_sha256": before.snapshot_sha256,
        "after_sha256": after.snapshot_sha256,
        "summary": counts,
        "changes": [d.to_dict() for d in diff_records],
    }
