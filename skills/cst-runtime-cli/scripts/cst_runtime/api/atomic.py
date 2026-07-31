"""现有原子操作的 handler 与元数据发现。

该模块位于 API 层，CLI 与 worker 共用这里的单一清单。工具模块中的可选依赖
均在实际调用时加载，因此发现清单不会要求安装全部可选依赖。
"""
from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Any, Callable


_TOOL_MODULES = (
    "simulation",
    "modeling",
    "project",
    "results",
    "farfield",
    "session",
    "audit",
    "workspace",
    "optimization",
    "doe",
)


@lru_cache(maxsize=1)
def atomic_handler_map() -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    """发现受控 tools 包中的全部 ``tool_*`` handler。"""
    handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
    for module_name in _TOOL_MODULES:
        module = importlib.import_module(f"cst_runtime.tools.{module_name}")
        for attribute_name in dir(module):
            if not attribute_name.startswith("tool_"):
                continue
            value = getattr(module, attribute_name)
            if callable(value):
                handlers[attribute_name] = value
    return handlers


def atomic_definitions() -> list[dict[str, Any]]:
    """返回带 handler 的原子操作定义。"""
    from ..tools import all_defs

    handlers = atomic_handler_map()
    definitions: list[dict[str, Any]] = []
    for name, definition in all_defs().items():
        handler_name = str(definition["handler"])
        try:
            handler = handlers[handler_name]
        except KeyError as exc:
            raise KeyError(
                f"操作 {name} 缺少 handler: {handler_name}"
            ) from exc
        definitions.append(
            {
                "name": name,
                "description": str(definition.get("description", name)),
                "risk": str(definition.get("risk", "read")),
                "input_schema": definition["json_schema"],
                "handler": handler,
            }
        )
    return definitions
