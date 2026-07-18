"""MCP Tool definitions: CST Session operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def open_project(project_path: str) -> dict[str, Any]:
    """
    打开 CST 工程 (Public API)。

    Args (参数):
        project_path: .cst 文件的绝对路径。

    Returns (返回值):
        包含 CST 状态信息和工程详情的字典。

    Raises (抛出异常):
        RuntimeError: 如果由于进程卡死、路径错误或许可证问题导致工程无法打开时抛出。

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.session", "open_project", project_path=project_path)

def close_project(project_path: str, save: bool = False) -> dict[str, Any]:
    """
    关闭CST工程.

    Args:
        project_path: .cst 文件的绝对路径。
        save: 关闭前是否保存

    Returns:
        包含 CST 状态信息和工程详情的字典。

    Raises:
        RuntimeError: 如果工程无法关闭，抛出错误
    """
    return call_cst("lib.session", "close_project", project_path=project_path, save=save)

def create_blank_project(project_path: str) -> dict[str, Any]:
    """
    创建一个全新的空白 CST 工程。

    Args:
        project_path: .cst 文件的绝对路径。

    Returns:
        包含 CST 状态信息和工程详情的字典。
    """
    return call_cst("lib.session", "create_blank_project", project_path=project_path)

def save_project(project_path: str) -> dict[str, Any]:
    """
    保存当前的 CST 工程。

    Args:
        project_path: .cst 文件的绝对路径。

    Returns:
        包含执行信息的字典。
    """
    return call_cst("lib.session", "save_project", project_path=project_path)

def quit_cst(project_path: str = '') -> dict[str, Any]:
    """
    完全退出 CST 软件进程。

    Args:
        project_path: （可选）特定工程的路径

    Returns:
        包含状态的字典

    Raises:
        RuntimeError: 如果 CST 进程无法退出时抛出
    """
    return call_cst("lib.session", "quit_cst", project_path=project_path)

SESSION_TOOLS = [
    {"name": "open-project", "handler": open_project},
    {"name": "close-project", "handler": close_project},
    {"name": "create-blank-project", "handler": create_blank_project},
    {"name": "save-project", "handler": save_project},
    {"name": "quit-cst", "handler": quit_cst},
]
