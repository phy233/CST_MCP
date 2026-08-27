"""Agent/MCP 工具暴露策略。

CLI 始终可发现完整工具集；MCP 只注册 ``AGENT_TOOLS`` 中明确列出的工具。
当前策略允许 Agent 完成工程创建、建模、求解、结果导出和优化闭环，但继续
隔离会修改运行环境或直接终止 CST 进程的高风险入口。未来新增工具仍默认
``cli_only``，避免因遗漏安全审查而自动公开。
"""
from __future__ import annotations


VALID_EXPOSURES = frozenset({"agent", "cli_only", "experimental"})

# 这份白名单覆盖当前完整工程工作流。项目内删除实体、监视器或探针是建模纠错
# 所需能力，仍通过 MCP 的 destructiveHint 明确标记为有副作用操作。
AGENT_TOOLS = frozenset(
    {
        "analyze-metasurface-sparameters",
        "analyze-probes",
        "ask-study",
        "best-study",
        "boolean-add",
        "boolean-insert",
        "boolean-intersect",
        "boolean-subtract",
        "build-array",
        "calculate-farfield-neighborhood-flatness",
        "capture-3d-view",
        "change-material",
        "change-parameter",
        "change-solver-type",
        "configure-frequency-domain-solver",
        "create-blank-project",
        "create-component",
        "create-hollow-sweep",
        "create-horn-segment",
        "create-loft-sweep",
        "create-mesh-group",
        "create-study",
        "cst-session-close",
        "cst-session-inspect",
        "cst-session-open",
        "cst-session-reattach",
        "define-analytical-curve",
        "define-background",
        "define-boundary",
        "define-brick",
        "define-cone",
        "define-cylinder",
        "define-extrude-curve",
        "define-farfield-monitor",
        "define-fdsolver-stimulation",
        "define-floquet-port",
        "define-frequency-range",
        "define-loft",
        "define-material-from-mtd",
        "define-mesh",
        "define-parameters",
        "define-plane-wave",
        "define-polygon-3d",
        "define-port",
        "define-rectangle",
        "define-solver",
        "define-unit-cell-boundary",
        "define-units",
        "delete-entity",
        "delete-monitor",
        "delete-probe",
        "design-probes",
        "diff-history-snapshots",
        "export-current-density",
        "export-e-field",
        "export-farfield-cut",
        "export-farfield-grid",
        "export-h-field",
        "export-power-flow",
        "export-power-loss-density",
        "export-sparameter",
        "export-surface-current",
        "export-touchstone",
        "export-voltage-result",
        "generate-report",
        "generate-restore-plan",
        "get-background",
        "get-1d-result",
        "get-2d-result",
        "get-parameter-combination",
        "get-run-context",
        "get-version-info",
        "health-check",
        "infer-run-dir",
        "init-task",
        "init-workspace",
        "inspect-boundary",
        "inspect-farfield-monitors",
        "inspect-floquet-ports",
        "inspect-interaction-history",
        "inspect-model-view",
        "inspect-plane-wave",
        "inspect-project",
        "is-simulation-running",
        "list-agent-notes",
        "list-entities",
        "list-field-results",
        "list-history-log",
        "list-interaction-log",
        "list-materials",
        "list-monitors",
        "list-open-projects",
        "list-parameters",
        "list-result-items",
        "list-run-ids",
        "list-sparameter-results",
        "list-subprojects",
        "open-results-project",
        "pause-simulation",
        "pick-face",
        "plot-exported-file",
        "prepare-experiment",
        "prepare-run",
        "quick-sweep",
        "record-agent-note",
        "record-stage",
        "rename-entity",
        "resume-simulation",
        "run-experiment",
        "run-optimization-step",
        "run-probe-phase",
        "save-project",
        "set-background-with-space",
        "set-efield-monitor",
        "set-entity-color",
        "set-farfield-plot-cuts",
        "set-fdsolver-extrude-open-bc",
        "set-field-monitor",
        "set-mesh-fpbavoid-nonreg-unite",
        "set-mesh-minimum-step-number",
        "set-probe",
        "set-solver-acceleration",
        "show-bounding-box",
        "stage-evidence",
        "start-simulation",
        "start-simulation-async",
        "stop-simulation",
        "study-add-trials",
        "study-param-importances",
        "study-terminate-check",
        "tell-study",
        "transform-curve",
        "transform-shape",
        "update-status",
        "verify-project-identity",
        "wait-project-unlocked",
        "wait-simulation",
    }
)

# 这些入口不属于完成单个 CST 工程所必需的能力，且会改变 Python/CST 运行环境
# 或直接退出进程，因此仅允许用户在 CLI 中显式调用。
HIGH_RISK_CLI_ONLY_TOOLS = frozenset(
    {
        "checkout-replay-copy",
        "create-history-checkpoint",
        "create-project-checkpoint",
        "cst-session-quit",
        "export-history-snapshot",
        "health-repair",
        "inspect-history-capabilities",
        "inspect-history-status",
        "install-cst-libraries",
        "reconcile-history-operation",
    }
)

# 保留该级别以兼容清单协议；当前没有仅因缺少真机测试而隐藏的工具。
EXPERIMENTAL_TOOLS = frozenset()


def exposure_for(tool_name: str) -> str:
    """按显式白名单返回公开级别，未知工具仍默认仅限 CLI。"""
    if tool_name in HIGH_RISK_CLI_ONLY_TOOLS:
        return "cli_only"
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
