from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = str(Path(__file__).resolve().parents[1] / "scripts")
sys.path.insert(0, SCRIPTS)

def test_deleted_s11_pipeline_helpers_are_not_public() -> None:
    """run-experiment 已与导出解耦，不再保留按 s11_run 文件判定的辅助函数。"""
    from cst_runtime.cli.pipelines import impl

    assert not hasattr(impl, "_parse_s11_json")
