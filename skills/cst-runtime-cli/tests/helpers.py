"""Shared test factory functions for cst-runtime-cli tests."""
from __future__ import annotations

import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPO_ROOT / "skills" / "cst-runtime-cli"
PYTHON = sys.executable
RUNTIME_PYTHONPATH = str(SKILL_ROOT / "scripts")

# CLI 子进程以仓库根为 cwd 时，args-template 等命令会把捕获文件写进
# <cwd>/.cst_runtime/tmp。测试统一改用会话级临时 cwd，从根上避免污染仓库，
# 会话结束时由 atexit 兜底删除。
_CLI_CWD: Path | None = None


def _cli_cwd() -> Path:
    global _CLI_CWD
    if _CLI_CWD is None:
        _CLI_CWD = Path(tempfile.mkdtemp(prefix="cst-runtime-cli-tests-"))
        atexit.register(lambda: shutil.rmtree(_CLI_CWD, ignore_errors=True))
    return _CLI_CWD


def run_cli(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    """在子进程中运行 cst_runtime CLI（纯离线工具），返回 CompletedProcess。"""
    env = {**os.environ, "PYTHONPATH": RUNTIME_PYTHONPATH}
    return subprocess.run(
        [PYTHON, "-m", "cst_runtime", *args],
        cwd=_cli_cwd(),
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def assert_json_error(result: dict, error_type: str) -> dict:
    """Assert JSON response has specific error type."""
    assert result["status"] == "error", f"Expected error, got: {result}"
    assert result["error_type"] == error_type, \
        f"Expected error_type='{error_type}', got: '{result.get('error_type')}'"
    return result
