"""Agent 可见的 Floquet 和 Unit Cell 能力边界测试。"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_agent_skills_explain_exposure_and_verification_are_different() -> None:
    documents = [
        REPO_ROOT / "skills" / "cst-mcp" / "SKILL.md",
        REPO_ROOT / "skills" / "cst-runtime-cli" / "SKILL.md",
    ]

    for document in documents:
        text = document.read_text(encoding="utf-8")
        assert "超表面基本闭环" in text
        assert "已向 Agent 暴露" in text
        assert "真机验收" in text


def test_generic_boundary_tool_disclaims_advanced_configuration() -> None:
    from cst_runtime.tools.project import TOOL_DEFS

    description = TOOL_DEFS["define-boundary"]["description"]
    assert "不等价于完整的 Unit Cell 或 Floquet 配置" in description
    assert "手动完成" in description


def test_metasurface_tools_are_agent_exposed() -> None:
    from cst_runtime.api.atomic import atomic_definitions

    definitions = {item["name"]: item for item in atomic_definitions()}
    assert definitions["define-floquet-port"]["exposure"] == "agent"
    assert definitions["define-unit-cell-boundary"]["exposure"] == "agent"
    assert definitions["inspect-floquet-ports"]["exposure"] == "agent"
    assert definitions["analyze-metasurface-sparameters"]["exposure"] == "agent"
