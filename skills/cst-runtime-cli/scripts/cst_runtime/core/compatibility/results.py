from __future__ import annotations

from typing import Any
from ..errors import UnsupportedFeatureError


def supports_2d_results(result_module: Any) -> bool:
    """Checks if the cst.results module supports 2D result extraction."""
    return hasattr(result_module, "get_result2d_item")


def get_result2d_item(result_module: Any, treepath: str) -> Any:
    """Gets a 2D result item if supported, otherwise raises UnsupportedFeatureError."""
    if not supports_2d_results(result_module):
        raise UnsupportedFeatureError("2D results extraction via cst.results is not supported in CST 2022 (0D/1D only).")
    return result_module.get_result2d_item(treepath)


def get_colormap_items(result_module: Any) -> list[str]:
    """Gets colormap items if supported, otherwise returns an empty list."""
    if not supports_2d_results(result_module):
        return []
    try:
        return [str(it) for it in result_module.get_tree_items(filter="colormap")]
    except TypeError:
        return []
