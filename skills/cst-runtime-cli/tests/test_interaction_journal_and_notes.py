"""纯 Python 离线测试：MCP Interaction Journal、大 Payload 内容寻址存储与 Agent 显式工作笔记。"""
from pathlib import Path
import pytest

from cst_runtime.interaction.models import (
    AgentWorkNote,
    MCPInteractionRecord,
    PayloadReference,
)
from cst_runtime.interaction.journal import (
    append_interaction_event,
    get_session_storage_root,
    list_interactions,
    read_payload_reference,
)
from cst_runtime.interaction.notes import (
    list_work_notes,
    record_work_note,
)


def test_interaction_record_lifecycle(tmp_path: Path):
    rec = MCPInteractionRecord(
        interaction_id="int_001",
        tool_name="define-brick",
        tool_args={"name": "b1", "xrange": [0, 10]},
        task_id="task_test",
        run_id="run_001",
        workspace=str(tmp_path),
        state="requested",
    )
    append_interaction_event(rec, workspace=str(tmp_path))

    # 更新为 running
    rec.state = "running"
    append_interaction_event(rec, workspace=str(tmp_path))

    # 更新为 succeeded
    rec.state = "succeeded"
    rec.duration_ms = 45.2
    rec.result = {"status": "success", "operation_id": "op_999"}
    append_interaction_event(rec, workspace=str(tmp_path))

    items = list_interactions(workspace=str(tmp_path))
    assert len(items) == 1
    item = items[0]
    assert item["interaction_id"] == "int_001"
    assert item["state"] == "succeeded"
    assert item["duration_ms"] == 45.2
    assert item["result"]["operation_id"] == "op_999"


def test_large_payload_content_addressed_storage(tmp_path: Path):
    # 构造一个 > 20KB 的大字典
    large_data = {f"key_{i}": f"large_value_string_{i}" * 20 for i in range(100)}

    rec = MCPInteractionRecord(
        interaction_id="int_large",
        tool_name="custom-large-op",
        tool_args=large_data,
        workspace=str(tmp_path),
        state="requested",
    )
    append_interaction_event(rec, workspace=str(tmp_path))

    items = list_interactions(workspace=str(tmp_path))
    assert len(items) == 1
    saved_rec = items[0]

    # tool_args 应该被外置并附加 preview 与 ref
    assert "request_payload_ref" in saved_rec
    ref = saved_rec["request_payload_ref"]
    assert ref["size_bytes"] > 16384
    assert Path(ref["storage_path"]).is_file()

    # 通过 read_payload_reference 还原完整原始数据
    reconstituted = read_payload_reference(ref)
    assert isinstance(reconstituted, dict)
    assert reconstituted["key_0"] == large_data["key_0"]
    assert len(reconstituted) == 100


def test_agent_work_notes(tmp_path: Path):
    n1 = record_work_note(
        "计划采用圆柱波导以优化高频模式隔离度。",
        category="plan",
        task_id="task_ant",
        workspace=str(tmp_path),
    )
    assert n1["status"] == "success"

    n2 = record_work_note(
        "与用户确认将仿真扫频步长设为 1001 点。",
        category="user_confirmation",
        task_id="task_ant",
        user_confirmed=True,
        workspace=str(tmp_path),
    )
    assert n2["status"] == "success"

    notes = list_work_notes(workspace=str(tmp_path), task_id="task_ant")
    assert len(notes) == 2
    # 最新的排在前面
    assert notes[0]["category"] == "user_confirmation"
    assert notes[0]["user_confirmed"] is True
    assert notes[1]["category"] == "plan"

    # 按 category 过滤
    filtered = list_work_notes(workspace=str(tmp_path), category="decision")
    assert len(filtered) == 0


def test_large_response_content_addressed_storage(tmp_path: Path):
    large_result = {f"res_key_{i}": f"large_result_field_{i}" * 25 for i in range(100)}
    rec = MCPInteractionRecord(
        interaction_id="int_large_res",
        tool_name="export-large-mesh",
        tool_args={"mesh_id": 1},
        workspace=str(tmp_path),
        state="succeeded",
        result=large_result,
    )
    append_interaction_event(rec, workspace=str(tmp_path))

    items = list_interactions(workspace=str(tmp_path))
    assert len(items) == 1
    saved_rec = items[0]

    assert "response_payload_ref" in saved_rec
    ref = saved_rec["response_payload_ref"]
    assert ref["size_bytes"] > 16384
    assert Path(ref["storage_path"]).is_file()

    reconstituted = read_payload_reference(ref)
    assert isinstance(reconstituted, dict)
    assert reconstituted["res_key_0"] == large_result["res_key_0"]


def test_inspect_interaction_history_bidirectional_linkage(tmp_path: Path, monkeypatch):
    from cst_runtime.history.models import HistoryOperationRecord, HistorySnapshot
    from cst_runtime.history.journal import append_operation, save_snapshot
    from cst_runtime.lib.interaction import inspect_interaction_history

    monkeypatch.setenv("CST_WORKSPACE", str(tmp_path))

    # 1. 建立前后快照
    s_before = HistorySnapshot.from_raw_cst(
        {"list": [{"name": "init", "contents": "init"}]},
        project_path=str(tmp_path / "proj.cst"),
    )
    s_after = HistorySnapshot.from_raw_cst(
        {"list": [{"name": "init", "contents": "init"}, {"name": "brick1", "contents": "brick code"}]},
        project_path=str(tmp_path / "proj.cst"),
    )
    save_snapshot(s_before, project_path=str(tmp_path / "proj.cst"))
    save_snapshot(s_after, project_path=str(tmp_path / "proj.cst"))

    # 2. 建立 Operation
    op = HistoryOperationRecord(
        operation_id="op_linked_123",
        history_label="brick1",
        business_vba="brick code",
        business_vba_sha256="",
        project_path=str(tmp_path / "proj.cst"),
        interaction_id="int_linked_999",
        before_snapshot_id=s_before.snapshot_id,
        before_snapshot_sha256=s_before.snapshot_sha256,
        after_snapshot_id=s_after.snapshot_id,
        after_snapshot_sha256=s_after.snapshot_sha256,
        execution_state="succeeded",
    )
    append_operation(op, project_path=str(tmp_path / "proj.cst"))

    # 3. 建立 MCP Interaction
    rec = MCPInteractionRecord(
        interaction_id="int_linked_999",
        tool_name="define-brick",
        tool_args={"name": "brick1"},
        workspace=str(tmp_path),
        project_path=str(tmp_path / "proj.cst"),
        state="succeeded",
        operation_id="op_linked_123",
    )
    append_interaction_event(rec, workspace=str(tmp_path))

    # 4. 执行 inspect_interaction_history 双向联合查询
    res = inspect_interaction_history("int_linked_999", project_path=str(tmp_path / "proj.cst"))
    assert res["status"] == "success"
    assert res["interaction"]["interaction_id"] == "int_linked_999"
    assert res["operation"]["operation_id"] == "op_linked_123"
    assert res["before_snapshot"]["snapshot_id"] == s_before.snapshot_id
    assert res["after_snapshot"]["snapshot_id"] == s_after.snapshot_id
    assert res["diff"] is not None
    assert res["diff"]["summary"]["added_count"] == 1
    added_changes = [c for c in res["diff"]["changes"] if c["change_type"] == "added"]
    assert len(added_changes) == 1
    assert added_changes[0]["name"] == "brick1"

