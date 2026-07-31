"""从实际 Registry 和 handler 生成架构迁移清册。"""
from __future__ import annotations

import inspect
from typing import Any

from .atomic import atomic_definitions


def operation_inventory() -> list[dict[str, Any]]:
    """返回原子操作、handler 模块及当前公开边界状态。"""
    inventory: list[dict[str, Any]] = []
    for definition in atomic_definitions():
        handler = definition["handler"]
        source = inspect.getsource(inspect.getmodule(handler))
        inventory.append(
            {
                "operation": definition["name"],
                "handler": handler.__name__,
                "module": handler.__module__,
                "risk": definition["risk"],
                "uses_lib_boundary": "..lib" in source or "cst_runtime.lib" in source,
                "imports_core": "..core" in source or "cst_runtime.core" in source,
            }
        )
    return inventory
