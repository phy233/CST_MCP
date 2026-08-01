from __future__ import annotations

from typing import Any
from .base import unsupported_feature


def supports_2d_results(result_module: Any) -> bool:
    """Checks if the cst.results module supports 2D result extraction."""
    return hasattr(result_module, "get_result2d_item")


def get_result2d_item(result_module: Any, treepath: str) -> Any:
    """Gets a 2D result item if supported, otherwise raises UnsupportedFeatureError."""
    if not supports_2d_results(result_module):
        raise unsupported_feature(
            "results.2d",
            required_capability="result2d",
            next_action="CST 2022 请改用 0D/1D 结果或 colormap 枚举。",
        )
    return result_module.get_result2d_item(treepath)


def get_colormap_items(result_module: Any) -> list[str]:
    """Gets colormap items if supported, otherwise returns an empty list."""
    if not supports_2d_results(result_module):
        return []
    try:
        return [str(it) for it in result_module.get_tree_items(filter="colormap")]
    except TypeError:
        return []


def list_all_result_items(result_module: Any) -> list[str]:
    """仅在结果模块确实公开全量枚举能力时调用私有兼容接口。"""
    getter = getattr(result_module, "_get_all_result_items", None)
    if not callable(getter):
        raise unsupported_feature(
            "results.list_all",
            required_capability="results_all_items",
            next_action="请将 filter_type 改为 0D/1D 或 colormap。",
        )
    treepaths: list[str] = []
    seen: set[str] = set()
    for item in getter():
        treepath = getattr(item, "treepath", None)
        if treepath and treepath not in seen:
            seen.add(treepath)
            treepaths.append(str(treepath))
    return treepaths


__all__ = [
    "get_colormap_items",
    "get_result2d_item",
    "list_all_result_items",
    "supports_2d_results",
]
