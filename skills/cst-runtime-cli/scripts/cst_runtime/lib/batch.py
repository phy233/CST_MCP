"""CST 建模批处理的原子公共门面。"""
from __future__ import annotations

from typing import Any

from ..core.modeling import begin_batch as _begin_batch
from ..core.modeling import discard_batch as _discard_batch
from ..core.modeling import flush_batch as _flush_batch


def begin(project_path: str, summary: str = "Batch Execution") -> dict[str, Any]:
    """开始一次建模批处理。"""
    return _begin_batch(project_path, summary=summary)


def flush(project_path: str) -> dict[str, Any]:
    """提交并执行当前批处理。"""
    return _flush_batch(project_path)


def discard(project_path: str) -> dict[str, Any]:
    """丢弃当前批处理。"""
    return _discard_batch(project_path)
