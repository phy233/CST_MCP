"""MCP 服务与 Python 3.9 Runtime Worker 的运行边界测试。"""
from __future__ import annotations

import ast
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_SCRIPTS = ROOT / "skills" / "cst-runtime-cli" / "scripts"


def test_packages_declare_separate_python_ranges() -> None:
    """MCP 服务与 Runtime 必须声明各自兼容的 Python 版本。"""
    mcp_project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime_project = tomllib.loads(
        (RUNTIME_SCRIPTS / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert mcp_project["project"]["requires-python"] == ">=3.12"
    assert runtime_project["project"]["requires-python"] == ">=3.9,<3.10"


def test_mcp_proxy_checks_worker_is_python_39() -> None:
    """MCP 代理必须在启动 Worker 前验证 Python 3.9。"""
    proxy = ROOT / "mcp_server" / "proxy.py"
    source = proxy.read_text(encoding="utf-8")
    tree = ast.parse(source)
    literals = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]

    assert "3.9" in literals
    assert "CST worker 必须使用 Python 3.9；" in source
