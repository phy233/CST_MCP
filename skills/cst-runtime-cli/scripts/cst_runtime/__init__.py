"""独立、协议无关的 CST Studio Suite Python 库。"""
from __future__ import annotations

import importlib
from typing import Any


__all__ = ["api", "core", "lib", "workflows", "analysis"]


def __getattr__(name: str) -> Any:
    """按需加载公开子包。"""
    if name in __all__:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(name)
