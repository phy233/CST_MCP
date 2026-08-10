"""测试体系自身的分层和安全策略检查。"""
from __future__ import annotations

import ast
from pathlib import Path


TEST_ROOT = Path(__file__).resolve().parent
FORBIDDEN_FIXTURES = {"monkeypatch", "mocker"}
FORBIDDEN_CALLS = {"MagicMock", "Mock", "AsyncMock", "patch"}


def _is_cst_integration(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "cst_integration":
            return True
    return False


def _mock_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    if not _is_cst_integration(tree):
        return []

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            argument_names = {
                argument.arg
                for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
            }
            forbidden = argument_names & FORBIDDEN_FIXTURES
            if forbidden:
                violations.append(
                    f"第 {node.lineno} 行使用伪造夹具：{', '.join(sorted(forbidden))}"
                )
        if isinstance(node, ast.ImportFrom) and node.module == "unittest.mock":
            violations.append(f"第 {node.lineno} 行导入 unittest.mock")
        if isinstance(node, ast.Call):
            function = node.func
            name = function.id if isinstance(function, ast.Name) else getattr(function, "attr", "")
            if name in FORBIDDEN_CALLS:
                violations.append(f"第 {node.lineno} 行调用 {name}")
    return violations


def test_cst_integration_modules_do_not_use_mock_substitutes() -> None:
    """真机模块不能用 mock 代替 CST、Worker 或实际状态查询。"""
    failures: list[str] = []
    for path in sorted(TEST_ROOT.rglob("test*.py")):
        for violation in _mock_violations(path):
            failures.append(f"{path.relative_to(TEST_ROOT)}：{violation}")
    assert not failures, "\n" + "\n".join(failures)


def test_no_interactive_input_remains_in_test_scripts() -> None:
    """测试目录不得再依赖人工按键继续。"""
    failures: list[str] = []
    for path in sorted(TEST_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "input":
                    failures.append(f"{path.relative_to(TEST_ROOT)}：第 {node.lineno} 行")
    assert not failures, "仍存在人工 input()：\n" + "\n".join(failures)
