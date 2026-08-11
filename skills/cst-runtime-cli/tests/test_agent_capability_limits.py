"""Agent 可见的 Floquet 和 Unit Cell 能力边界测试。"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_agent_skills_expose_manual_floquet_limit() -> None:
    documents = [
        REPO_ROOT / "skills" / "cst-mcp" / "SKILL.md",
        REPO_ROOT / "skills" / "cst-runtime-cli" / "SKILL.md",
    ]

    for document in documents:
        text = document.read_text(encoding="utf-8")
        assert "Floquet Port 与 Unit Cell 能力限制" in text
        assert "手动完成" in text


def test_generic_boundary_tool_disclaims_advanced_configuration() -> None:
    from cst_runtime.tools.project import TOOL_DEFS

    description = TOOL_DEFS["define-boundary"]["description"]
    assert "不等价于完整的 Unit Cell 或 Floquet 配置" in description
    assert "手动完成" in description


def test_incomplete_periodic_methods_are_not_exposed_as_tools() -> None:
    from cst_runtime.tools import all_defs

    tool_names = set(all_defs())
    assert "define-floquet-port" not in tool_names
    assert "define-unit-cell-boundary" not in tool_names
