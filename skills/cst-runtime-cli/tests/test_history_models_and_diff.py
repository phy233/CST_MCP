"""纯 Python 离线测试：History 数据模型、快照哈希与 Diff 比较引擎。"""
import pytest
from cst_runtime.history.models import (
    HistoryBlock,
    HistorySnapshot,
    HistoryOperationRecord,
    compute_snapshot_sha256,
)
from cst_runtime.history.diff import diff_snapshots


def test_history_block_from_raw_preserves_unknown_fields():
    raw = {
        "name": "define brick: component1:solid1",
        "contents": "With Brick\n  .Reset\n  .Name \"solid1\"\nEnd With",
        "version": "2022.5",
        "error": False,
        "exclude": False,
        "hide": False,
        "has_undo": True,
        "custom_vendor_flag": 12345,
        "meta_tag": "test_tag",
    }
    block = HistoryBlock.from_raw(0, raw)
    assert block.index == 0
    assert block.name == "define brick: component1:solid1"
    assert "With Brick" in block.contents
    assert block.has_undo is True
    assert block.extra_fields == {"custom_vendor_flag": 12345, "meta_tag": "test_tag"}
    assert len(block.contents_sha256) == 64

    # 还原为 raw
    cst_raw = block.to_cst_raw()
    assert cst_raw["custom_vendor_flag"] == 12345
    assert cst_raw["meta_tag"] == "test_tag"
    assert cst_raw["has_undo"] is True


def test_history_block_whitespace_and_unicode_fidelity():
    raw_text = "  ' 注释：测试 Unicode 字符与换行\r\nDim a As Double\r\na = 1.234\n"
    block = HistoryBlock.from_raw(1, {"name": "block1", "contents": raw_text})
    assert block.contents == raw_text
    assert block.contents_sha256 == block.contents_sha256


def test_snapshot_from_raw_cst_empty_list():
    snap = HistorySnapshot.from_raw_cst(
        {"list": None},
        project_path="C:/test/proj.cst",
        reason="empty_test",
    )
    assert len(snap.blocks) == 0
    assert snap.project_name == "proj"
    assert len(snap.snapshot_sha256) == 64


def test_snapshot_hash_determinism_and_sensitivity():
    blocks1 = [
        HistoryBlock.from_raw(0, {"name": "b1", "contents": "VBA 1"}),
        HistoryBlock.from_raw(1, {"name": "b2", "contents": "VBA 2"}),
    ]
    blocks2 = [
        HistoryBlock.from_raw(0, {"name": "b1", "contents": "VBA 1"}),
        HistoryBlock.from_raw(1, {"name": "b2", "contents": "VBA 2"}),
    ]
    blocks_diff = [
        HistoryBlock.from_raw(0, {"name": "b1", "contents": "VBA 1"}),
        HistoryBlock.from_raw(1, {"name": "b2", "contents": "VBA 2 "}),  # 尾部加空格
    ]

    h1 = compute_snapshot_sha256(blocks1)
    h2 = compute_snapshot_sha256(blocks2)
    h_diff = compute_snapshot_sha256(blocks_diff)

    assert h1 == h2
    assert h1 != h_diff


def test_diff_identical_snapshots():
    raw = {
        "list": [
            {"name": "b0", "contents": "code 0"},
            {"name": "b1", "contents": "code 1"},
        ]
    }
    s1 = HistorySnapshot.from_raw_cst(raw, project_path="C:/test/p.cst")
    s2 = HistorySnapshot.from_raw_cst(raw, project_path="C:/test/p.cst")

    res = diff_snapshots(s1, s2)
    assert res["status"] == "success"
    assert res["is_identical"] is True
    assert res["summary"]["unchanged_count"] == 2
    assert res["summary"]["added_count"] == 0
    assert res["summary"]["deleted_count"] == 0


def test_diff_added_modified_deleted_moved():
    before_raw = {
        "list": [
            {"name": "block_A", "contents": "Dim a\na = 1"},
            {"name": "block_B", "contents": "Dim b\nb = 2"},
            {"name": "block_C", "contents": "Dim c\nc = 3"},
        ]
    }
    after_raw = {
        "list": [
            {"name": "block_A", "contents": "Dim a\na = 10"},  # modified
            {"name": "block_C", "contents": "Dim c\nc = 3"},   # moved (index 2 -> 1)
            {"name": "block_D", "contents": "Dim d\nd = 4"},   # added
            # block_B deleted
        ]
    }

    s_before = HistorySnapshot.from_raw_cst(before_raw, project_path="C:/test/p.cst")
    s_after = HistorySnapshot.from_raw_cst(after_raw, project_path="C:/test/p.cst")

    res = diff_snapshots(s_before, s_after)
    assert res["status"] == "success"
    assert res["is_identical"] is False
    summary = res["summary"]

    assert summary["before_count"] == 3
    assert summary["after_count"] == 3
    assert summary["added_count"] == 1
    assert summary["deleted_count"] == 1
    assert summary["modified_count"] == 1
    assert summary["moved_count"] == 1

    # 检查 modified 块的 unified_diff
    mod_changes = [c for c in res["changes"] if c["change_type"] == "modified"]
    assert len(mod_changes) == 1
    assert "vba_unified_diff" in mod_changes[0]
    assert "-a = 1" in mod_changes[0]["vba_unified_diff"]
    assert "+a = 10" in mod_changes[0]["vba_unified_diff"]


def test_operation_record_creation_and_serialization():
    op = HistoryOperationRecord(
        operation_id="op_123",
        history_label="define brick: brick1",
        business_vba="With Brick\n  .Name \"brick1\"\nEnd With",
        business_vba_sha256="",
        project_path="C:/test/proj.cst",
        execution_state="succeeded",
        reconciliation_state="not_required",
    )
    assert len(op.business_vba_sha256) == 64
    d = op.to_dict()
    assert d["operation_id"] == "op_123"
    assert d["execution_state"] == "succeeded"

    restored = HistoryOperationRecord.from_dict(d)
    assert restored.operation_id == op.operation_id
    assert restored.business_vba == op.business_vba


def test_snapshot_roundtrip_idempotency_and_hash_stability():
    raw = {
        "list": [
            {
                "name": "brick1",
                "contents": "With Brick\n  .Name \"b1\"\nEnd With",
                "version": "2022.5",
                "custom_unknown_key": "val123",
            },
            {
                "name": "brick2",
                "contents": "With Brick\n  .Name \"b2\"\nEnd With",
                "version": "2022.5",
            },
        ]
    }
    snap = HistorySnapshot.from_raw_cst(raw, project_path="C:/test/p.cst", reason="init")
    initial_hash = snap.snapshot_sha256

    # 1. 序列化为 dict
    d1 = snap.to_dict()
    # 2. 从 dict 反序列化为新的 HistorySnapshot
    snap_restored1 = HistorySnapshot.from_dict(d1)
    # 3. 验证哈希和重新计算哈希完全一致
    assert snap_restored1.snapshot_sha256 == initial_hash
    assert compute_snapshot_sha256(snap_restored1.blocks) == initial_hash

    # 4. 再次序列化并反序列化（第二轮往返）
    d2 = snap_restored1.to_dict()
    snap_restored2 = HistorySnapshot.from_dict(d2)
    assert snap_restored2.snapshot_sha256 == initial_hash
    assert compute_snapshot_sha256(snap_restored2.blocks) == initial_hash

    # 5. 验证 extra_fields 没有被嵌套污染
    assert snap_restored2.blocks[0].extra_fields == {"custom_unknown_key": "val123"}
    assert snap_restored2.blocks[1].extra_fields == {}

