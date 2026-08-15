"""CLI 测试的环境卫生检查：不得在仓库根留下运行时临时文件。"""
from __future__ import annotations

import pytest

from helpers import REPO_ROOT, run_cli

pytestmark = pytest.mark.subprocess


def _repo_args_snapshot() -> set[str]:
    tmp_dir = REPO_ROOT / ".cst_runtime" / "tmp"
    if not tmp_dir.is_dir():
        return set()
    return {path.name for path in tmp_dir.glob("args_*.json")}


def test_args_template_does_not_litter_repo_root() -> None:
    """args-template 的捕获文件必须落在会话临时 cwd，而非仓库根。"""
    before = _repo_args_snapshot()
    result = run_cli("args-template", "--tool", "health-check")
    assert result.returncode == 0, result.stderr
    after = _repo_args_snapshot()
    assert after == before, f"仓库根出现新的 args 捕获文件：{after - before}"
