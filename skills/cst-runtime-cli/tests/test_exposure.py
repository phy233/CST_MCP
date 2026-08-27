"""Agent/MCP 完整工程能力与高风险隔离策略测试。"""
from __future__ import annotations


def test_every_operation_has_valid_exposure() -> None:
    from cst_runtime.api.exposure import VALID_EXPOSURES
    from cst_runtime.api.registry import operations

    specs = operations()
    assert specs
    assert {spec.exposure for spec in specs.values()} <= VALID_EXPOSURES


def test_only_explicit_high_risk_tools_remain_cli_only() -> None:
    from cst_runtime.api.exposure import HIGH_RISK_CLI_ONLY_TOOLS
    from cst_runtime.api.registry import tools

    public = tools()
    cli_only = {
        name for name, spec in public.items()
        if spec.exposure == "cli_only"
    }
    experimental = {
        name for name, spec in public.items()
        if spec.exposure == "experimental"
    }
    assert cli_only == HIGH_RISK_CLI_ONLY_TOOLS
    assert not experimental


def test_agent_allowlist_covers_complete_project_workflow() -> None:
    from cst_runtime.api.exposure import AGENT_TOOLS, HIGH_RISK_CLI_ONLY_TOOLS
    from cst_runtime.api.registry import tools

    public = tools()
    exposed = {name for name, spec in public.items() if spec.exposure == "agent"}
    assert exposed == AGENT_TOOLS
    assert set(public) == AGENT_TOOLS | HIGH_RISK_CLI_ONLY_TOOLS
    assert not (AGENT_TOOLS & HIGH_RISK_CLI_ONLY_TOOLS)
    assert {
        "create-blank-project",
        "define-brick",
        "define-fdsolver-stimulation",
        "run-experiment",
        "export-touchstone",
        "run-optimization-step",
        "save-project",
        "cst-session-close",
    } <= exposed
    assert public["quick-sweep"].risk == "long-running"


def test_solver_error_propagation_tools_are_agent_exposed() -> None:
    """start-simulation 与 get-background 必须对 MCP Agent 可见。"""
    from cst_runtime.api.exposure import AGENT_TOOLS
    from cst_runtime.api.registry import tools

    public = tools()
    assert "get-background" in AGENT_TOOLS
    assert "start-simulation" in AGENT_TOOLS
    assert public["get-background"].risk == "read"
    assert public["start-simulation"].risk == "long-running"


def test_raw_history_and_project_deletion_are_not_registered_tools() -> None:
    from cst_runtime.api.registry import tools

    public = tools()
    assert "add-to-history" not in public
    assert "delete-project" not in public


def test_all_atomic_tools_reject_unknown_top_level_fields() -> None:
    from cst_runtime.api import invoke_tool
    from cst_runtime.tools import all_defs

    definitions = all_defs()
    assert definitions
    assert all(
        definition["json_schema"].get("additionalProperties") is False
        for definition in definitions.values()
    )
    result = invoke_tool("health-check", {"workspace": "", "auto_fxi": True})
    assert result["status"] == "error"
    assert result["error_type"] == "invalid_arguments"
    assert result["unknown_arguments"] == ["auto_fxi"]


def test_all_atomic_tools_have_output_schema() -> None:
    from cst_runtime.api import describe_tools

    described = describe_tools()
    assert described
    assert all(item.get("output_schema") for item in described)
    result_tools = {
        item["name"]: item["output_schema"]
        for item in described
        if item["name"] in {
            "run-experiment",
            "list-sparameter-results",
            "export-sparameter",
            "list-field-results",
        }
    }
    assert set(result_tools) == {
        "run-experiment",
        "list-sparameter-results",
        "export-sparameter",
        "list-field-results",
    }
    assert "result_metrics" in result_tools["run-experiment"]["properties"]
    assert "results" in result_tools["list-field-results"]["properties"]
