"""跨包和 runtime 分层约束测试。"""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skills" / "cst-runtime-cli" / "scripts" / "cst_runtime"


def _imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level
            found.append((node.lineno, prefix + (node.module or "")))
    return found


def test_workflows_never_import_core() -> None:
    violations = [
        f"{path.name}:{line}"
        for path in (RUNTIME / "workflows").glob("*.py")
        for line, module in _imports(path)
        if module.startswith("..core") or module.startswith("cst_runtime.core")
    ]
    assert not violations


def test_lower_layers_never_import_upper_layers() -> None:
    violations: list[str] = []
    for layer, forbidden in {
        "core": ("cst_runtime.lib", "cst_runtime.workflows", "..lib", "..workflows"),
        "lib": ("cst_runtime.workflows", "..workflows", "cst_runtime.api", "..api"),
    }.items():
        for path in (RUNTIME / layer).rglob("*.py"):
            for line, module in _imports(path):
                if module.startswith(forbidden):
                    violations.append(f"{path.relative_to(RUNTIME)}:{line}:{module}")
    assert not violations


def test_removed_lib_workflow_modules_do_not_exist() -> None:
    for name in ("array.py", "sweep.py", "cross_process.py", "unit_cells.py"):
        assert not (RUNTIME / "lib" / name).exists()


def test_runtime_api_does_not_depend_on_mcp() -> None:
    violations = [
        f"{path.name}:{line}"
        for path in (RUNTIME / "api").glob("*.py")
        for line, module in _imports(path)
        if module == "mcp" or module.startswith("mcp.")
    ]
    assert not violations


def test_runtime_api_never_imports_cli_or_core() -> None:
    violations = [
        f"{path.name}:{line}:{module}"
        for path in (RUNTIME / "api").glob("*.py")
        for line, module in _imports(path)
        if module.startswith("..cli")
        or module.startswith("cst_runtime.cli")
        or module.startswith("..core")
        or module.startswith("cst_runtime.core")
    ]
    assert not violations
