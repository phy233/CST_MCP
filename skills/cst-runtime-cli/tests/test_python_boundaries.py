"""Python 运行边界的静态约束测试。"""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNTIME_SCRIPTS = ROOT / "skills" / "cst-runtime-cli" / "scripts"


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
