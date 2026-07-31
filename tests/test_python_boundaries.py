"""Python 运行边界的静态约束测试。"""
from __future__ import annotations

import ast
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills" / "cst-runtime-cli" / "scripts"


def test_packages_declare_separate_python_ranges() -> None:
    mcp_project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime_project = tomllib.loads((RUNTIME_SCRIPTS / "pyproject.toml").read_text(encoding="utf-8"))

    assert mcp_project["project"]["requires-python"] == ">=3.12"
    assert runtime_project["project"]["requires-python"] == ">=3.9,<3.10"


def test_bootstrap_never_installs_runtime_into_uv_environment() -> None:
    bootstrap = RUNTIME_SCRIPTS / "bootstrap.py"
    text = bootstrap.read_text(encoding="utf-8")

    assert 'requires-python = ">=3.9,<3.10"' in text
    assert '["uv", "sync"]' not in text
    assert 'dependencies = ["cst-runtime"]' not in text


def test_runtime_health_check_does_not_require_mcp_venv() -> None:
    environment = RUNTIME_SCRIPTS / "cst_runtime" / "core" / "environment.py"
    text = environment.read_text(encoding="utf-8")

    assert 'ws_root / ".venv"' not in text
    assert "uv pip install" not in text


def test_mcp_proxy_checks_worker_is_python_39() -> None:
    proxy = ROOT / "mcp_server" / "proxy.py"
    source = proxy.read_text(encoding="utf-8")
    tree = ast.parse(source)
    literals = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]

    assert "3.9" in literals
    assert "CST worker 必须使用 Python 3.9；" in source
