"""Agent/MCP 工具暴露策略。

CLI 仍可发现全部工具；MCP 只注册这里明确列入 ``AGENT_TOOLS`` 的工具。
任何新增工具默认都是 ``cli_only``，从而避免因遗漏元数据而意外公开。
"""
from __future__ import annotations


VALID_EXPOSURES = frozenset({"agent", "cli_only", "experimental"})

# 首批仅开放无副作用的项目与结果查询。写入、会话控制、安装和长任务均默认拒绝。
AGENT_TOOLS = frozenset(
    {
        "get-parameter-combination",
        "get-version-info",
        "health-check",
        "inspect-farfield-monitors",
        "inspect-project",
        "list-field-results",
        "list-entities",
        "list-materials",
        "list-open-projects",
        "list-parameters",
        "list-result-items",
        "list-run-ids",
        "list-sparameter-results",
        "list-subprojects",
        "open-results-project",
        "verify-project-identity",
    }
)

# 尚未完成 CST 2022 实机验收的工具必须保持隐藏。
EXPERIMENTAL_TOOLS = frozenset(
    {
        "define-fdsolver-stimulation",
        "define-farfield-monitor",
        "export-sparameter",
        "export-touchstone",
        "export-e-field",
        "export-h-field",
        "export-surface-current",
        "export-power-flow",
        "export-current-density",
        "export-power-loss-density",
        "export-voltage-result",
        "define-unit-cell-boundary",
        "inspect-boundary",
        "define-floquet-port",
        "inspect-floquet-ports",
        "define-plane-wave",
        "inspect-plane-wave",
        "configure-frequency-domain-solver",
        "list-monitors",
        "analyze-metasurface-sparameters",
    }
)


def exposure_for(tool_name: str) -> str:
    """按默认拒绝策略返回公开级别。"""
    if tool_name in AGENT_TOOLS:
        return "agent"
    if tool_name in EXPERIMENTAL_TOOLS:
        return "experimental"
    return "cli_only"


def validate_exposure(exposure: str) -> str:
    """拒绝未知暴露值，避免注册端静默降级。"""
    if exposure not in VALID_EXPOSURES:
        allowed = "、".join(sorted(VALID_EXPOSURES))
        raise ValueError(f"未知 exposure={exposure!r}；允许值为：{allowed}")
    return exposure
