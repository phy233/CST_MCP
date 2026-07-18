from __future__ import annotations

from typing import Any
from ..errors import UnsupportedFeatureError


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

    raise UnsupportedFeatureError("Neither model3d nor modeler 'get_tree_items' is supported in this version of CST.")


def select_tree_item(project: Any, tree_path: str) -> None:
    """Selects an item in the CST Navigation Tree."""
    if hasattr(project, "model3d") and hasattr(project.model3d, "SelectTreeItem"):
        project.model3d.SelectTreeItem(tree_path)
    elif hasattr(project, "modeler") and hasattr(project.modeler, "SelectTreeItem"):
        project.modeler.SelectTreeItem(tree_path)
    else:
        raise UnsupportedFeatureError("SelectTreeItem is not supported in this version of CST.")
