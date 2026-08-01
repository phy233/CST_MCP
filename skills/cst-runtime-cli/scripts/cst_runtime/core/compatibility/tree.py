from __future__ import annotations

from typing import Any
from .base import unsupported_feature
from .execution import execute_text_query, vba_string


_LEGACY_TREE_ROOTS = (
    "Components",
    "Materials",
    "Ports",
    "Monitors",
    "Farfields",
    "1D Results",
    "2D/3D Results",
    "Tables",
)


def _unique_nonempty(lines: list[str]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for line in lines:
        item = line.strip()
        if item and item not in seen:
            seen.add(item)
            items.append(item)
    return items


def _legacy_navigation_tree_items(project: Any) -> list[str]:
    """使用 CST 2022 ResultTree VBA 递归枚举常用导航树根节点。"""
    root_upper_bound = len(_LEGACY_TREE_ROOTS) - 1
    lines = [
        f"Dim cstRtTreeRoots(0 To {root_upper_bound}) As String",
        *(
            f'cstRtTreeRoots({index}) = "{vba_string(root)}"'
            for index, root in enumerate(_LEGACY_TREE_ROOTS)
        ),
        "Dim cstRtTreeQueue() As String",
        "Dim cstRtTreeHead As Long",
        "Dim cstRtTreeTail As Long",
        "Dim cstRtTreeRootIndex As Long",
        "Dim cstRtTreeParent As String",
        "Dim cstRtTreeChild As String",
        "ReDim cstRtTreeQueue(0 To 31)",
        "cstRtTreeHead = 0",
        "cstRtTreeTail = -1",
        f"For cstRtTreeRootIndex = 0 To {root_upper_bound}",
        "If ResultTree.DoesTreeItemExist(cstRtTreeRoots(cstRtTreeRootIndex)) Then",
        "cstRtTreeTail = cstRtTreeTail + 1",
        "If cstRtTreeTail > UBound(cstRtTreeQueue) Then ReDim Preserve cstRtTreeQueue(0 To cstRtTreeTail + 32)",
        "cstRtTreeQueue(cstRtTreeTail) = cstRtTreeRoots(cstRtTreeRootIndex)",
        "End If",
        "Next cstRtTreeRootIndex",
        "Do While cstRtTreeHead <= cstRtTreeTail",
        "cstRtTreeParent = cstRtTreeQueue(cstRtTreeHead)",
        "cstRtTreeChild = ResultTree.GetFirstChildName(cstRtTreeParent)",
        'Do While cstRtTreeChild <> ""',
        "Print #cstRtQueryFile, cstRtTreeChild",
        "cstRtTreeTail = cstRtTreeTail + 1",
        "If cstRtTreeTail > UBound(cstRtTreeQueue) Then ReDim Preserve cstRtTreeQueue(0 To cstRtTreeTail + 32)",
        "cstRtTreeQueue(cstRtTreeTail) = cstRtTreeChild",
        "cstRtTreeChild = ResultTree.GetNextItemName(cstRtTreeChild)",
        "Loop",
        "cstRtTreeHead = cstRtTreeHead + 1",
        "Loop",
    ]
    return _unique_nonempty(execute_text_query(project, lines, timeout=5.0))


def _legacy_filtered_result_items(project: Any, filter_type: str) -> list[str]:
    """使用 CST 2022 ResultTree.GetTreeResults 枚举筛选后的结果节点。"""
    normalized_filter = filter_type.strip() or "0D/1D"
    if normalized_filter.casefold() == "all":
        normalized_filter = "folder 0D/1D 2D/3D farfield colormap matrix"
    if "recursive" not in normalized_filter.casefold().split():
        normalized_filter += " recursive"
    result_roots = ("1D Results", "2D/3D Results", "Farfields", "Tables")
    root_upper_bound = len(result_roots) - 1
    lines = [
        f"Dim cstRtResultRoots(0 To {root_upper_bound}) As String",
        *(
            f'cstRtResultRoots({index}) = "{vba_string(root)}"'
            for index, root in enumerate(result_roots)
        ),
        "Dim cstRtResultPaths As Variant",
        "Dim cstRtResultTypes As Variant",
        "Dim cstRtResultFiles As Variant",
        "Dim cstRtResultInfo As Variant",
        "Dim cstRtResultCount As Long",
        "Dim cstRtResultRootIndex As Long",
        "Dim cstRtResultIndex As Long",
        f"For cstRtResultRootIndex = 0 To {root_upper_bound}",
        "If ResultTree.DoesTreeItemExist(cstRtResultRoots(cstRtResultRootIndex)) Then",
        (
            "cstRtResultCount = ResultTree.GetTreeResults("
            "cstRtResultRoots(cstRtResultRootIndex), "
            f'"{vba_string(normalized_filter)}", "", '
            "cstRtResultPaths, cstRtResultTypes, cstRtResultFiles, cstRtResultInfo)"
        ),
        "For cstRtResultIndex = 0 To cstRtResultCount - 1",
        "Print #cstRtQueryFile, CStr(cstRtResultPaths(cstRtResultIndex))",
        "Next cstRtResultIndex",
        "End If",
        "Next cstRtResultRootIndex",
    ]
    return _unique_nonempty(execute_text_query(project, lines, timeout=5.0))


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

    if filter:
        return _legacy_filtered_result_items(project, filter)
    return _legacy_navigation_tree_items(project)


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
            f'If ResultTree.DoesTreeItemExist("{vba_string(tree_path)}") Then',
            'Print #cstRtQueryFile, "1"',
            "Else",
            'Print #cstRtQueryFile, "0"',
            "End If",
        ],
    )
    return bool(output and output[0].strip() == "1")


__all__ = ["get_tree_items", "result_item_exists", "select_tree_item"]
