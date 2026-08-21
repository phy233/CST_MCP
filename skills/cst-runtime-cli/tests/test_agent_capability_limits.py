"""Agent 可见的 Floquet 和 Unit Cell 能力边界测试。"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_agent_skills_split_transport_and_domain_responsibilities() -> None:
    """验证 Skill 路由和引用文件，而不是绑定某一段说明文案。"""
    transport_skills = [
        REPO_ROOT / "skills" / "cst-mcp" / "SKILL.md",
        REPO_ROOT / "skills" / "cst-runtime-cli" / "SKILL.md",
    ]
    domain_skill = REPO_ROOT / "skills" / "cst-metasurface-design" / "SKILL.md"

    assert domain_skill.is_file()
    domain_text = domain_skill.read_text(encoding="utf-8")
    assert "name: cst-metasurface-design" in domain_text

    for document in transport_skills:
        assert document.is_file()
        assert "cst-metasurface-design" in document.read_text(encoding="utf-8")

    reference_names = {
        "requirements-and-physics-gates.md",
        "geometry-and-history.md",
        "simulation-and-result-validation.md",
        "design-iteration.md",
    }
    reference_dir = domain_skill.parent / "references"
    assert reference_names <= {path.name for path in reference_dir.glob("*.md")}
def test_generic_boundary_tool_disclaims_advanced_configuration() -> None:
    from cst_runtime.tools.project import TOOL_DEFS

    description = TOOL_DEFS["define-boundary"]["description"]
    assert "不等价于完整的 Unit Cell 或 Floquet 配置" in description
    assert "手动完成" in description
