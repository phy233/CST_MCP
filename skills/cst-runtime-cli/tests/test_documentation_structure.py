"""纯离线测试：文档分层、Skill 入口与相对链接。"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


REPO_ROOT = Path(__file__).resolve().parents[3]
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def _active_markdown_files() -> list[Path]:
    """返回当前维护的文档；归档文档不承担实时链接契约。"""
    files = {
        REPO_ROOT / "README.md",
        REPO_ROOT / "INSTALL.md",
        REPO_ROOT / "devkit" / "README.md",
    }

    docs_root = REPO_ROOT / "docs"
    files.update(
        path
        for path in docs_root.rglob("*.md")
        if "archive" not in path.relative_to(docs_root).parts
    )

    for skill_root in (REPO_ROOT / "skills").iterdir():
        if not skill_root.is_dir():
            continue
        skill_entry = skill_root / "SKILL.md"
        if skill_entry.is_file():
            files.add(skill_entry)
        reference_root = skill_root / "references"
        if reference_root.is_dir():
            files.update(reference_root.rglob("*.md"))

    devkit_references = REPO_ROOT / "devkit" / "references"
    if devkit_references.is_dir():
        files.update(devkit_references.rglob("*.md"))

    return sorted(path for path in files if path.is_file())


def _relative_link_targets(document: Path) -> list[str]:
    targets: list[str] = []
    for raw_target in MARKDOWN_LINK_RE.findall(document.read_text(encoding="utf-8")):
        target = raw_target.strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        elif " " in target:
            # 普通 Markdown 链接可在路径后附标题；这里只取实际目标。
            target = target.split(maxsplit=1)[0]

        if target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target = unquote(target.split("#", maxsplit=1)[0])
        if target:
            targets.append(target)
    return targets


def test_canonical_document_paths_and_removed_obsolete_files() -> None:
    canonical_paths = [
        "docs/architecture/error-handling.md",
        "docs/architecture/mcp-exposure.md",
        "docs/compatibility/cst-2022.md",
        "docs/development/testing.md",
        "docs/guides/stepwise-cst-workflow.md",
        "devkit/references/lib-usage-guide.md",
        "skills/cst-metasurface-design/SKILL.md",
    ]
    obsolete_paths = [
        "docs/README.md",
        "docs/HISTORY_VERSIONING_AGENT_PROMPT.md",
        "docs/API_REFERENCE.md",
        "docs/error_handling.md",
        "docs/MCP_EXPOSURE.md",
        "docs/cst_2022_compatibility.md",
        "docs/testing.md",
        "docs/lib_usage_guide.md",
        "docs/WORKFLOW_REFERENCE.md",
    ]

    assert all((REPO_ROOT / path).is_file() for path in canonical_paths)
    assert all(not (REPO_ROOT / path).exists() for path in obsolete_paths)


def test_active_markdown_relative_links_resolve() -> None:
    broken_links: list[str] = []
    for document in _active_markdown_files():
        for target in _relative_link_targets(document):
            candidate = Path(target)
            if not candidate.is_absolute():
                candidate = document.parent / candidate
            if not candidate.exists():
                broken_links.append(
                    f"{document.relative_to(REPO_ROOT)} -> {target}"
                )

    assert not broken_links, "发现失效的相对链接：\n" + "\n".join(broken_links)
