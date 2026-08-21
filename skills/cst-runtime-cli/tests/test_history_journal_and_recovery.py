"""纯 Python 离线测试：History Journal、原子持久化、断点恢复判定与严格前缀恢复计划。"""
import json
from pathlib import Path
import pytest

from cst_runtime.history.models import (
    HistoryBlock,
    HistoryOperationRecord,
    HistorySnapshot,
)
from cst_runtime.history.journal import (
    append_operation,
    get_operation,
    list_operations,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)
from cst_runtime.history.recovery import (
    evaluate_interrupted_operation,
    reconcile_operation,
)
from cst_runtime.history.checkpoint import (
    generate_restore_plan,
    list_history_checkpoints,
    save_history_checkpoint,
)


def test_atomic_snapshot_save_and_load(tmp_path: Path):
    raw = {
        "list": [
            {"name": "b1", "contents": "VBA content 1"},
            {"name": "b2", "contents": "VBA content 2"},
        ]
    }
    snapshot = HistorySnapshot.from_raw_cst(
        raw,
        project_path=str(tmp_path / "test.cst"),
        reason="unit_test",
    )
    saved_path = save_snapshot(snapshot, storage_root=tmp_path)
    assert saved_path.is_file()

    loaded = load_snapshot(snapshot.snapshot_id, storage_root=tmp_path)
    assert loaded is not None
    assert loaded.snapshot_id == snapshot.snapshot_id
    assert loaded.snapshot_sha256 == snapshot.snapshot_sha256
    assert len(loaded.blocks) == 2

    snaps = list_snapshots(storage_root=tmp_path)
    assert len(snaps) == 1
    assert snaps[0]["snapshot_id"] == snapshot.snapshot_id


def test_operations_journal_append_and_tolerance(tmp_path: Path):
    op1 = HistoryOperationRecord(
        operation_id="op_1",
        history_label="block1",
        business_vba="Code 1",
        business_vba_sha256="",
        project_path=str(tmp_path / "p.cst"),
        execution_state="succeeded",
    )
    op2 = HistoryOperationRecord(
        operation_id="op_2",
        history_label="block2",
        business_vba="Code 2",
        business_vba_sha256="",
        project_path=str(tmp_path / "p.cst"),
        execution_state="pending",
    )

    append_operation(op1, storage_root=tmp_path)
    append_operation(op2, storage_root=tmp_path)

    # 模拟崩溃：在 operations.jsonl 末尾追加半截损坏行
    journal_file = tmp_path / "operations.jsonl"
    with journal_file.open("a", encoding="utf-8") as f:
        f.write('{"operation_id": "op_corrupted", "incomplete":')

    # 读取器应自动容错并忽略最后的残损行
    ops = list_operations(storage_root=tmp_path)
    assert len(ops) == 2
    assert {o["operation_id"] for o in ops} == {"op_1", "op_2"}

    fetched = get_operation("op_1", storage_root=tmp_path)
    assert fetched is not None
    assert fetched.history_label == "block1"


def test_breakpoint_recovery_evaluation_states():
    # 构造前置快照与后置快照
    snap_before = HistorySnapshot.from_raw_cst(
        {"list": [{"name": "init", "contents": "init vba"}]},
        project_path="C:/test/p.cst",
    )
    snap_after = HistorySnapshot.from_raw_cst(
        {
            "list": [
                {"name": "init", "contents": "init vba"},
                {"name": "brick1", "contents": "wrapped brick1 vba\nclean business code"},
            ]
        },
        project_path="C:/test/p.cst",
    )
    snap_diverged = HistorySnapshot.from_raw_cst(
        {"list": [{"name": "other", "contents": "other vba"}]},
        project_path="C:/test/p.cst",
    )

    op = HistoryOperationRecord(
        operation_id="op_test",
        history_label="brick1",
        business_vba="clean business code",
        business_vba_sha256="",
        project_path="C:/test/p.cst",
        before_snapshot_sha256=snap_before.snapshot_sha256,
        after_snapshot_sha256=snap_after.snapshot_sha256,
        execution_state="interrupted",
    )

    # 分支 1: 当前等于 before -> not_applied, can_retry=True
    r1 = evaluate_interrupted_operation(op, snap_before)
    assert r1["reconciliation_state"] == "not_applied"
    assert r1["can_retry"] is True

    # 分支 2: 当前等于 after -> applied, can_retry=False (禁止重复提交)
    r2 = evaluate_interrupted_operation(op, snap_after)
    assert r2["reconciliation_state"] == "applied"
    assert r2["can_retry"] is False

    # 分支 3: 都不匹配且分叉 -> ambiguous, can_retry=False (严禁自动重试)
    r3 = evaluate_interrupted_operation(op, snap_diverged)
    assert r3["reconciliation_state"] == "ambiguous"
    assert r3["can_retry"] is False


def test_reconcile_operation(tmp_path: Path):
    op = HistoryOperationRecord(
        operation_id="op_recon",
        history_label="brick1",
        business_vba="clean business code",
        business_vba_sha256="",
        project_path=str(tmp_path / "p.cst"),
        execution_state="interrupted",
        reconciliation_state="ambiguous",
    )
    append_operation(op, storage_root=tmp_path)

    res = reconcile_operation(
        "op_recon",
        decision="applied",
        notes="已人工核对模型树，结构体完整存在。",
        storage_root=tmp_path,
    )
    assert res["status"] == "success"
    assert res["reconciliation_state"] == "reconciled"

    updated = get_operation("op_recon", storage_root=tmp_path)
    assert updated.reconciliation_state == "reconciled"
    assert "已人工核对" in updated.reconciliation_notes


def test_generate_restore_plan_4_cases():
    s_a = HistorySnapshot.from_raw_cst(
        {"list": [{"name": "A", "contents": "vba A"}]},
        project_path="C:/test/p.cst",
    )
    s_ab = HistorySnapshot.from_raw_cst(
        {"list": [{"name": "A", "contents": "vba A"}, {"name": "B", "contents": "vba B"}]},
        project_path="C:/test/p.cst",
    )
    s_abcd = HistorySnapshot.from_raw_cst(
        {
            "list": [
                {"name": "A", "contents": "vba A"},
                {"name": "B", "contents": "vba B"},
                {"name": "C", "contents": "vba C"},
                {"name": "D", "contents": "vba D"},
            ]
        },
        project_path="C:/test/p.cst",
    )
    s_abc = HistorySnapshot.from_raw_cst(
        {
            "list": [
                {"name": "A", "contents": "vba A"},
                {"name": "B", "contents": "vba B"},
                {"name": "C", "contents": "vba C"},
            ]
        },
        project_path="C:/test/p.cst",
    )
    s_abx = HistorySnapshot.from_raw_cst(
        {
            "list": [
                {"name": "A", "contents": "vba A"},
                {"name": "B", "contents": "vba B"},
                {"name": "X", "contents": "vba X"},
            ]
        },
        project_path="C:/test/p.cst",
    )

    op_c = HistoryOperationRecord(
        operation_id="op_c", history_label="C", business_vba="biz VBA C",
        business_vba_sha256="", project_path="C:/test/p.cst",
        before_snapshot_sha256=s_ab.snapshot_sha256,
        after_snapshot_sha256=s_abc.snapshot_sha256,
    )
    op_d = HistoryOperationRecord(
        operation_id="op_d", history_label="D", business_vba="biz VBA D",
        business_vba_sha256="", project_path="C:/test/p.cst",
        before_snapshot_sha256=s_abc.snapshot_sha256,
        after_snapshot_sha256=s_abcd.snapshot_sha256,
    )

    # 情况一: 完全相同 -> already_at_target
    p1 = generate_restore_plan(s_ab, s_ab)
    assert p1["plan_type"] == "already_at_target"
    assert p1["can_execute"] is True
    assert len(p1["steps"]) == 0

    # 情况二: 严格前缀且均有 business_vba -> prefix_suffix_replay
    p2 = generate_restore_plan(s_ab, s_abcd, operations=[op_c, op_d])
    assert p2["plan_type"] == "prefix_suffix_replay"
    assert p2["can_execute"] is True
    assert p2["suffix_count"] == 2
    assert p2["steps"][0]["label"] == "C"
    assert p2["steps"][0]["business_vba"] == "biz VBA C"
    assert p2["steps"][1]["label"] == "D"

    # 情况二 (缺失 business_vba): 标记无法自动重放
    p2_missing = generate_restore_plan(s_ab, s_abcd, operations=[op_c])  # 缺少 D 的 operation
    assert p2_missing["plan_type"] == "prefix_suffix_replay"
    assert p2_missing["can_execute"] is False
    assert p2_missing["steps"][1]["status"] == "requires_manual_vba_or_physical_checkpoint"

    # 情况三: 基线比目标更长 -> cannot_rewind_forward_replay
    p3 = generate_restore_plan(s_abcd, s_ab)
    assert p3["plan_type"] == "cannot_rewind_forward_replay"
    assert p3["can_execute"] is False

    # 情况四: 基线与目标分叉 -> diverged_history_branch
    p4 = generate_restore_plan(s_abx, s_abcd)
    assert p4["plan_type"] == "diverged_history_branch"
    assert p4["can_execute"] is False


def test_generate_restore_plan_duplicate_labels_matching():
    # 构造拥有 3 个完全同名标签 "define brick" 的快照序列
    from cst_runtime.history.models import compute_snapshot_sha256, HistoryBlock
    b0 = HistoryBlock.from_raw(0, {"name": "init", "contents": "init"})
    b1 = HistoryBlock.from_raw(1, {"name": "define brick", "contents": "brick 1 code"})
    b2 = HistoryBlock.from_raw(2, {"name": "define brick", "contents": "brick 2 code"})
    b3 = HistoryBlock.from_raw(3, {"name": "define brick", "contents": "brick 3 code"})

    h_base = compute_snapshot_sha256([b0])
    h_step1 = compute_snapshot_sha256([b0, b1])
    h_step2 = compute_snapshot_sha256([b0, b1, b2])
    h_step3 = compute_snapshot_sha256([b0, b1, b2, b3])

    s_base = HistorySnapshot.from_raw_cst({"list": [{"name": "init", "contents": "init"}]}, project_path="C:/test/p.cst")
    s_target = HistorySnapshot.from_raw_cst(
        {
            "list": [
                {"name": "init", "contents": "init"},
                {"name": "define brick", "contents": "brick 1 code"},
                {"name": "define brick", "contents": "brick 2 code"},
                {"name": "define brick", "contents": "brick 3 code"},
            ]
        },
        project_path="C:/test/p.cst",
    )

    op1 = HistoryOperationRecord(
        operation_id="op_brick_1",
        history_label="define brick",
        business_vba="biz VBA brick 1",
        business_vba_sha256="",
        project_path="C:/test/p.cst",
        before_snapshot_sha256=h_base,
        after_snapshot_sha256=h_step1,
    )
    op2 = HistoryOperationRecord(
        operation_id="op_brick_2",
        history_label="define brick",
        business_vba="biz VBA brick 2",
        business_vba_sha256="",
        project_path="C:/test/p.cst",
        before_snapshot_sha256=h_step1,
        after_snapshot_sha256=h_step2,
    )
    op3 = HistoryOperationRecord(
        operation_id="op_brick_3",
        history_label="define brick",
        business_vba="biz VBA brick 3",
        business_vba_sha256="",
        project_path="C:/test/p.cst",
        before_snapshot_sha256=h_step2,
        after_snapshot_sha256=h_step3,
    )

    # 乱序传入 operations，验证基于前后哈希的严格精确匹配
    plan = generate_restore_plan(s_base, s_target, operations=[op3, op1, op2])
    assert plan["plan_type"] == "prefix_suffix_replay"
    assert plan["can_execute"] is True
    assert len(plan["steps"]) == 3

    assert plan["steps"][0]["operation_id"] == "op_brick_1"
    assert plan["steps"][0]["business_vba"] == "biz VBA brick 1"
    assert plan["steps"][0]["expected_before_snapshot_sha256"] == h_base
    assert plan["steps"][0]["expected_after_snapshot_sha256"] == h_step1

    assert plan["steps"][1]["operation_id"] == "op_brick_2"
    assert plan["steps"][1]["business_vba"] == "biz VBA brick 2"
    assert plan["steps"][1]["expected_before_snapshot_sha256"] == h_step1
    assert plan["steps"][1]["expected_after_snapshot_sha256"] == h_step2

    assert plan["steps"][2]["operation_id"] == "op_brick_3"
    assert plan["steps"][2]["business_vba"] == "biz VBA brick 3"
    assert plan["steps"][2]["expected_before_snapshot_sha256"] == h_step2
    assert plan["steps"][2]["expected_after_snapshot_sha256"] == h_step3


def test_generate_restore_plan_rejects_label_only_fallback():
    baseline = HistorySnapshot.from_raw_cst(
        {"list": [{"name": "init", "contents": "init"}]},
        project_path="C:/test/p.cst",
    )
    target = HistorySnapshot.from_raw_cst(
        {
            "list": [
                {"name": "init", "contents": "init"},
                {"name": "define brick", "contents": "目标包装 VBA"},
            ]
        },
        project_path="C:/test/p.cst",
    )
    unrelated = HistoryOperationRecord(
        operation_id="other_operation",
        history_label="define brick",
        business_vba="不属于目标块的 VBA",
        business_vba_sha256="",
        project_path="C:/test/p.cst",
    )

    plan = generate_restore_plan(baseline, target, operations=[unrelated])

    assert plan["plan_type"] == "prefix_suffix_replay"
    assert plan["can_execute"] is False
    assert plan["steps"][0]["status"] == "requires_manual_vba_or_physical_checkpoint"
    assert "无法通过前后哈希" in plan["steps"][0]["warning"]



def test_history_checkpoint_persistence(tmp_path: Path):
    snap = HistorySnapshot.from_raw_cst(
        {"list": [{"name": "blk", "contents": "vba"}]},
        project_path=str(tmp_path / "p.cst"),
    )
    res = save_history_checkpoint(
        snap,
        checkpoint_name="test_chk",
        description="单元测试检查点",
        storage_root=tmp_path,
    )
    assert res["status"] == "success"

    chks = list_history_checkpoints(storage_root=tmp_path)
    assert len(chks) == 1
    assert chks[0]["checkpoint_name"] == "test_chk"
    assert chks[0]["description"] == "单元测试检查点"


def test_submit_vba_history_automatic_journaling_and_snapshots(tmp_path: Path):
    from unittest.mock import MagicMock
    from cst_runtime.core.error_gateway import submit_vba_history

    proj_file = tmp_path / "test_proj.cst"
    proj_file.touch()

    # 构造 mock project 对象
    history_state = [{"name": "init", "contents": "init vba"}]
    mock_modeler = MagicMock()
    status_dir = tmp_path

    def mock_add_to_history(name, script):
        history_state.append({"name": name, "contents": script})
        # 写出 status 文件模拟正常上报
        for arm_file in status_dir.glob("cst-runtime-*.arm"):
            status_file = status_dir / arm_file.name.replace(".arm", ".status")
            status_file.write_text("OK\n", encoding="utf-8")
        return True

    mock_modeler.add_to_history = mock_add_to_history
    mock_modeler._GetHistory.side_effect = lambda: {"list": list(history_state)}
    mock_project = MagicMock()
    mock_project.modeler = mock_modeler

    res = submit_vba_history(
        mock_project,
        "define brick: b1",
        ["With Brick", "  .Name \"b1\"", "End With"],
        project_path=str(proj_file),
        _status_directory=status_dir,
    )

    assert res["status"] == "success"
    assert "operation_id" in res
    assert "before_snapshot_sha256" in res
    assert "after_snapshot_sha256" in res
    assert res["before_snapshot_sha256"] != res["after_snapshot_sha256"]

    # 验证 operations.jsonl 自动记录
    ops = list_operations(project_path=str(proj_file))
    assert len(ops) == 1
    last_op = ops[0]
    assert last_op["execution_state"] == "succeeded"
    assert last_op["history_label"] == "define brick: b1"
    assert "With Brick" in last_op["business_vba"]
    assert last_op["after_snapshot_sha256"] == res["after_snapshot_sha256"]


def test_submit_vba_history_marks_snapshot_recording_failure_incomplete(
    tmp_path: Path,
    monkeypatch,
):
    from unittest.mock import MagicMock
    from cst_runtime.core.error_gateway import submit_vba_history
    from cst_runtime.history import journal as history_journal

    proj_file = tmp_path / "test_proj.cst"
    proj_file.touch()
    history_state = [{"name": "init", "contents": "init vba"}]
    mock_modeler = MagicMock()

    def mock_add_to_history(name, script):
        history_state.append({"name": name, "contents": script})
        for arm_file in tmp_path.glob("cst-runtime-*.arm"):
            status_file = tmp_path / arm_file.name.replace(".arm", ".status")
            status_file.write_text("OK\n", encoding="utf-8")
        return True

    mock_modeler.add_to_history = mock_add_to_history
    mock_modeler._GetHistory.side_effect = lambda: {"list": list(history_state)}
    mock_project = MagicMock()
    mock_project.modeler = mock_modeler
    monkeypatch.setattr(
        history_journal,
        "save_snapshot",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("磁盘写入失败")),
    )

    result = submit_vba_history(
        mock_project,
        "define brick: b1",
        ["With Brick", "End With"],
        project_path=str(proj_file),
        _status_directory=tmp_path,
    )

    assert result["status"] == "success"
    assert result["recording_status"] == "incomplete"
    assert result["before_snapshot_id"] is None
    assert result["after_snapshot_id"] is None
    assert {item["stage"] for item in result["recording_issues"]} == {
        "before_submission",
        "after_submission",
    }


def test_physical_checkpoint_locked_raises_timeout_error(tmp_path: Path, monkeypatch):
    from cst_runtime.lib import history as history_lib

    proj_file = tmp_path / "sample.cst"
    proj_file.touch()
    comp_dir = tmp_path / "sample"
    comp_dir.mkdir(parents=True, exist_ok=True)
    chk_dir = tmp_path / "chk_01"
    monkeypatch.setattr(history_lib, "get_attached_project", lambda _path: None)
    monkeypatch.setattr(
        history_lib,
        "wait_project_unlocked",
        lambda *_args, **_kwargs: {
            "status": "error",
            "locked": True,
            "message": "锁文件尚未释放",
            "lock_files": [str(comp_dir / "Model.lok")],
        },
    )

    with pytest.raises(TimeoutError) as exc_info:
        history_lib.create_physical_checkpoint(chk_dir, project_path=str(proj_file))

    assert "锁文件" in str(exc_info.value)
    assert not (chk_dir / "sample.cst").exists()


def test_physical_checkpoint_closes_open_project_before_copy(tmp_path: Path, monkeypatch):
    from cst_runtime.lib import history as history_lib

    proj_file = tmp_path / "sample.cst"
    proj_file.write_bytes(b"cst-project")
    comp_dir = tmp_path / "sample"
    comp_dir.mkdir()
    (comp_dir / "Model.dat").write_bytes(b"companion")
    chk_dir = tmp_path / "chk_01"
    close_calls = []

    monkeypatch.setattr(history_lib, "get_attached_project", lambda _path: object())

    def fake_close(project_path, **kwargs):
        close_calls.append((project_path, kwargs))
        return {
            "status": "success",
            "close_result": {"status": "success", "saved": True},
            "unlock_result": {"status": "success", "locked": False},
        }

    monkeypatch.setattr(history_lib, "close_project", fake_close)
    result = history_lib.create_physical_checkpoint(
        chk_dir,
        project_path=str(proj_file),
    )

    assert close_calls
    assert close_calls[0][1]["save"] is True
    assert close_calls[0][1]["kill_processes"] is False
    assert (chk_dir / "sample.cst").read_bytes() == b"cst-project"
    assert (chk_dir / "sample" / "Model.dat").read_bytes() == b"companion"
    assert result["manifest"]["source_closed_for_consistent_copy"] is True


def test_open_exact_project_rejects_non_matching_active_project(tmp_path: Path, monkeypatch):
    from cst_runtime.lib import history as history_lib

    project_path = tmp_path / "target.cst"
    project_path.touch()
    monkeypatch.setattr(history_lib, "get_attached_project", lambda _path: None)
    monkeypatch.setattr(
        history_lib,
        "open_project",
        lambda _path: {"status": "success", "project_path": str(project_path)},
    )

    with pytest.raises(RuntimeError) as exc_info:
        history_lib._open_exact_project(str(project_path))

    assert "精确路径" in str(exc_info.value)


def test_checkout_replay_copy_closes_baseline_and_verifies_each_hash(
    tmp_path: Path,
    monkeypatch,
):
    from cst_runtime.lib import history as history_lib

    baseline_path = tmp_path / "baseline.cst"
    baseline_path.write_bytes(b"baseline")
    baseline_companion = tmp_path / "baseline"
    baseline_companion.mkdir()
    (baseline_companion / "Model.dat").write_bytes(b"model")
    replay_path = tmp_path / "replayed.cst"

    raw_a = [{"name": "A", "contents": "vba A"}]
    raw_b = {"name": "重复标签", "contents": "wrapped op_b"}
    raw_c = {"name": "重复标签", "contents": "wrapped op_c"}
    target = HistorySnapshot.from_raw_cst(
        {"list": [*raw_a, raw_b, raw_c]},
        project_path=str(baseline_path),
    )
    snapshot_a = HistorySnapshot.from_raw_cst(
        {"list": raw_a},
        project_path=str(baseline_path),
    )
    snapshot_ab = HistorySnapshot.from_raw_cst(
        {"list": [*raw_a, raw_b]},
        project_path=str(baseline_path),
    )
    op_b = HistoryOperationRecord(
        operation_id="op_b",
        history_label="重复标签",
        business_vba="business B",
        business_vba_sha256="",
        project_path=str(baseline_path),
        before_snapshot_sha256=snapshot_a.snapshot_sha256,
        after_snapshot_sha256=snapshot_ab.snapshot_sha256,
    )
    op_c = HistoryOperationRecord(
        operation_id="op_c",
        history_label="重复标签",
        business_vba="business C",
        business_vba_sha256="",
        project_path=str(baseline_path),
        before_snapshot_sha256=snapshot_ab.snapshot_sha256,
        after_snapshot_sha256=target.snapshot_sha256,
    )

    class FakeModeler:
        def __init__(self, blocks):
            self.blocks = list(blocks)

        def _GetHistory(self):
            return {"list": list(self.blocks)}

    class FakeProject:
        def __init__(self, blocks):
            self.modeler = FakeModeler(blocks)

    base_project = FakeProject(raw_a)
    replay_project = FakeProject(raw_a)
    events = []

    def fake_open_exact(path):
        normalized = str(Path(path).resolve())
        if normalized == str(baseline_path.resolve()):
            events.append("open_baseline")
            return base_project, False
        if normalized == str(replay_path.resolve()):
            events.append("open_replay")
            return replay_project, True
        raise AssertionError(f"意外工程路径: {path}")

    def fake_close(path, **kwargs):
        events.append("close_baseline")
        assert str(Path(path).resolve()) == str(baseline_path.resolve())
        assert kwargs["save"] is True
        return {
            "status": "success",
            "close_result": {"status": "success", "saved": True},
            "unlock_result": {"status": "success", "locked": False},
        }

    target_blocks = {"op_b": raw_b, "op_c": raw_c}
    submit_calls = []

    def fake_submit(project, label, vba_lines, **kwargs):
        operation_id = kwargs["operation_id"]
        submit_calls.append((label, list(vba_lines), operation_id))
        project.modeler.blocks.append(target_blocks[operation_id])
        return {"status": "success", "operation_id": operation_id}

    monkeypatch.setattr(history_lib, "_open_exact_project", fake_open_exact)
    monkeypatch.setattr(history_lib, "close_project", fake_close)
    monkeypatch.setattr(history_lib, "submit_vba_history", fake_submit)
    monkeypatch.setattr(
        history_lib,
        "save_project",
        lambda _path: {"status": "success"},
    )

    result = history_lib.checkout_and_replay_copy(
        str(baseline_path),
        target,
        str(replay_path),
        operations=[op_c, op_b],
    )

    assert result["status"] == "success"
    assert result["final_snapshot_sha256"] == target.snapshot_sha256
    assert [call[2] for call in submit_calls] == ["op_b", "op_c"]
    assert events.index("close_baseline") < events.index("open_replay")
