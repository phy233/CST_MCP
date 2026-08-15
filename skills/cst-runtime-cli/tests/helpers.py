"""Shared test factory functions for cst-runtime-cli tests."""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPO_ROOT / "skills" / "cst-runtime-cli"
PYTHON = sys.executable
RUNTIME_PYTHONPATH = str(SKILL_ROOT / "scripts")


def run_cli(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    """在子进程中运行 cst_runtime CLI（纯离线工具），返回 CompletedProcess。"""
    env = {**os.environ, "PYTHONPATH": RUNTIME_PYTHONPATH}
    return subprocess.run(
        [PYTHON, "-m", "cst_runtime", *args],
        cwd=REPO_ROOT,
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
