"""纯 Python 离线测试：History 与 Interaction 工具注册、参数 Schema 与暴露白名单。"""
import pytest
from cst_runtime.tools import all_defs
from cst_runtime.api.exposure import AGENT_TOOLS, HIGH_RISK_CLI_ONLY_TOOLS, exposure_for
from cst_runtime.tools.history import (
    tool_list_history_log,
    tool_inspect_history_status,
)
from cst_runtime.tools.interaction import (
    tool_list_interaction_log,
    tool_record_agent_note,
    tool_list_agent_notes,
)


def test_all_new_tools_registered_with_valid_schema():
    defs = all_defs()
    expected_history_tools = [
        "list-history-log",
        "diff-history-snapshots",
        "generate-restore-plan",
        "inspect-history-capabilities",
        "export-history-snapshot",
        "inspect-history-status",
        "create-history-checkpoint",
        "create-project-checkpoint",
        "checkout-replay-copy",
        "reconcile-history-operation",
    ]
    expected_interaction_tools = [
        "list-interaction-log",
        "inspect-interaction-history",
        "record-agent-note",
        "list-agent-notes",
    ]

    for tool_name in expected_history_tools + expected_interaction_tools:
        assert tool_name in defs, f"工具 {tool_name} 未在工具表中注册"
        t_def = defs[tool_name]
        assert "json_schema" in t_def
        assert t_def["json_schema"]["type"] == "object"
        assert "description" in t_def
        assert "risk" in t_def
        assert "handler" in t_def


def test_exposure_policy_and_whitelist():
    # Agent 可见白名单工具
    assert exposure_for("list-history-log") == "agent"
    assert exposure_for("diff-history-snapshots") == "agent"
    assert exposure_for("generate-restore-plan") == "agent"
    assert exposure_for("list-interaction-log") == "agent"
    assert exposure_for("inspect-interaction-history") == "agent"
    assert exposure_for("record-agent-note") == "agent"
    assert exposure_for("list-agent-notes") == "agent"

    # 高风险 / 物理 / 人工介入工具仅限 CLI
    assert exposure_for("checkout-replay-copy") == "cli_only"
    assert exposure_for("create-project-checkpoint") == "cli_only"
    assert exposure_for("create-history-checkpoint") == "cli_only"
    assert exposure_for("reconcile-history-operation") == "cli_only"
    assert exposure_for("export-history-snapshot") == "cli_only"
    assert exposure_for("inspect-history-capabilities") == "cli_only"
    assert exposure_for("inspect-history-status") == "cli_only"

    # 严禁暴露的私有接口绝对不可在注册表中找到
    defs = all_defs()
    assert "_ResizeHistory" not in defs
    assert "_TryToUndoNTimes" not in defs
    assert "RemoveBlocksFromHistory" not in defs


def test_interaction_and_note_tools_offline():
    # 测试 record-agent-note
    n_res = tool_record_agent_note({
        "content": "测试离线添加笔记",
        "category": "milestone",
    })
    assert n_res["status"] == "success"
    assert "note_id" in n_res

    # 测试 list-agent-notes
    notes_res = tool_list_agent_notes({})
    assert notes_res["status"] == "success"
    assert notes_res["count"] >= 1

    # 测试 list-interaction-log
    int_res = tool_list_interaction_log({})
    assert int_res["status"] == "success"


def test_history_status_tool_offline():
    status_res = tool_inspect_history_status({})
    assert status_res["status"] == "success"
    assert "has_interrupted_operations" in status_res


def test_agent_note_schema_exposes_handler_supported_context_fields():
    """避免处理器已支持关联字段、Agent 却无法从公开 Schema 传入。"""
    defs = all_defs()
    record_properties = defs["record-agent-note"]["json_schema"]["properties"]
    list_properties = defs["list-agent-notes"]["json_schema"]["properties"]

    assert "project_path" in record_properties
    assert "snapshot_id" in record_properties
    assert "project_path" in list_properties
    assert record_properties["project_path"]["type"] == "string"
    assert record_properties["snapshot_id"]["type"] == "string"
