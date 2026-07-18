"""MCP Tool definitions: CST Array operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def build_array(project_path: str, unit_builder: ModelBuilder, elements: list[ArrayElement], summary: str = 'Build Array') -> dict[str, Any]:
    """
    通过回调函数构建复杂阵列。

    该函数会自动开启并管理 Command Buffer 的生命周期。它将根据 `elements` 中
    不同的 `code` 进行分组，按组调用 `unit_builder` 构建参考单元，然后将参考单元
    复制并平移到相应的坐标，最后删除该组的参考单元。

    Args:
        project_path: .cst 文件的绝对路径。
        unit_builder: 负责构建单种形态样板的回调函数。
        elements: ArrayElement 数据类的列表。
        summary: 批处理任务的摘要名称，将在 CST History Tree 中显示。

    Returns:
        包含 "status" 和其他执行信息的字典。如果失败，"status" 为 "error"。
    """
    return call_cst("lib.array", "build_array", project_path=project_path, unit_builder=unit_builder, elements=elements, summary=summary)

ARRAY_TOOLS = [
    {"name": "build-array", "handler": build_array},
]
