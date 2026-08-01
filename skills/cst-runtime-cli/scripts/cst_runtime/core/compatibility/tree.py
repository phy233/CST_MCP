from __future__ import annotations

from typing import Any
from .base import unsupported_feature
from .execution import execute_text_query, vba_string


def get_tree_items(project: Any, filter: str | None = None) -> list[Any]:
    """
    Retrieves tree items using the most appropriate API available in the current CST version.
    Falls back gracefully to older methods if model3d is not available.
    """
    # 1. Try CST 2023+ model3d
    if hasattr(project, "model3d") and hasattr(project.model3d, "get_tree_items"):
        if filter:
            return list(project.model3d.get_tree_items(filter=filter))
        return list(project.model3d.get_tree_items())

    # 2. Try CST 2022 modeler
    if hasattr(project, "modeler") and hasattr(project.modeler, "get_tree_items"):
        if filter:
            try:
                # modeler get_tree_items may not support filter keyword in older versions
                return list(project.modeler.get_tree_items(filter=filter))
            except TypeError:
                pass
        return list(project.modeler.get_tree_items())

    raise unsupported_feature(
        "tree.list_items",
        project=project,
        required_capability="tree_items_api",
        next_action="结果工程请改用 cst.results 的 0D/1D 或 colormap 过滤枚举。",
    )


def select_tree_item(project: Any, tree_path: str) -> None:
    """Selects an item in the CST Navigation Tree."""
    if hasattr(project, "model3d") and hasattr(project.model3d, "SelectTreeItem"):
        project.model3d.SelectTreeItem(tree_path)
    elif hasattr(project, "modeler") and hasattr(project.modeler, "SelectTreeItem"):
        project.modeler.SelectTreeItem(tree_path)
    else:
        raise unsupported_feature(
            "tree.select_item",
            project=project,
            required_capability="select_tree_item",
        )


def result_item_exists(project: Any, tree_path: str) -> bool:
    """检查结果树节点，缺少新版 ResultTree 时使用旧版 VBA。"""
    model3d = getattr(project, "model3d", None)
    result_tree = getattr(model3d, "ResultTree", None)
    checker = getattr(result_tree, "DoesTreeItemExist", None)
    if callable(checker):
        return bool(checker(tree_path))
    for candidate in (getattr(project, "modeler", None), project):
        checker = getattr(candidate, "DoesTreeItemExist", None)
        if callable(checker):
            return bool(checker(tree_path))
    output = execute_text_query(
        project,
        [
            f'If DoesTreeItemExist("{vba_string(tree_path)}") Then',
            'Print #cstRtQueryFile, "1"',
            "Else",
            'Print #cstRtQueryFile, "0"',
            "End If",
        ],
    )
    return bool(output and output[0].strip() == "1")


__all__ = ["get_tree_items", "result_item_exists", "select_tree_item"]
