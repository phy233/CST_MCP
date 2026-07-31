"""CST 原子能力的公共 Python 门面。

子模块按需加载，未安装可选依赖时不会影响其他原子能力。
"""
from __future__ import annotations

import importlib
from typing import Any


__all__ = [
    "session",
    "parameters",
    "geometry",
    "materials",
    "mesh",
    "boundary",
    "port",
    "solver",
    "monitors",
    "results",
    "farfield",
    "optimization",
    "batch",
]


def __getattr__(name: str) -> Any:
    """按需导入公开子模块。"""
    if name not in __all__:
        raise AttributeError(name)
    module = importlib.import_module(f"{__name__}.{name}")
    globals()[name] = module
    return module
