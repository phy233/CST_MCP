"""CST 工程生命周期管理
    “门面模式” Facade Pattern

用法:
    从 cst_runtime.lib.session 导入所需函数: open_project, close_project, inspect

    # 打开现有CST工程
    open_project("C:\\path\\to\\model.cst")

    # 检查CST工程状态
    status = inspect("C:\\path\\to\\model.cst")

    # 保存并关闭CST工程
    close_project("C:\\path\\to\\model.cst", save=True)
"""
from __future__ import annotations

from typing import Any

# 从上级目录(..)导入核心模块的函数，别名前加下划线伪装为私有函数，避免命名冲突
from ..core.session import open_project as _open_project
from ..core.session import close_project as _close_project
from ..core.session import inspect as _inspect
from ..core.session import quit_cst as _quit_cst
from ..core.identity import list_open_projects as _list_open_projects


def open_project(project_path: str) -> dict[str, Any]:
    """打开 CST 工程 (Public API)。

    Args (参数):
        project_path: .cst 文件的绝对路径。

    Returns (返回值):
        包含 CST 状态信息和工程详情的字典。

    Raises (抛出异常):
        RuntimeError: 如果由于进程卡死、路径错误或许可证问题导致工程无法打开时抛出。
    """
    result = _open_project(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to open project, check if a hung process, incorrect path, or license issue."))
    return result


def close_project(project_path: str, save: bool = False) -> dict[str, Any]:
    """关闭CST工程.

    Args:
        project_path: .cst 文件的绝对路径。
        save: 关闭前是否保存

    Returns:
        包含 CST 状态信息和工程详情的字典。

    Raises:
        RuntimeError: 如果工程无法关闭，抛出错误
    """
    result = _close_project(project_path, save=save)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to close project"))
    return result


def inspect(project_path: str = "") -> dict[str, Any]:
    """检查 CST 运行环境的状态。

    Args:
        project_path: （可选）特定工程的路径，留空则检查全局 CST 环境

    Returns:
        包含环境状态信息的字典
    """
    return _inspect(project_path)


def quit_cst(project_path: str = "") -> dict[str, Any]:
    """完全退出 CST 软件进程。

    Args:
        project_path: （可选）特定工程的路径

    Returns:
        包含状态的字典

    Raises:
        RuntimeError: 如果 CST 进程无法退出时抛出
    """
    result = _quit_cst(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to quit CST"))
    return result


def list_open() -> list[str]:
    """列出当前所有已经打开的 CST 工程路径。

    Returns:
        包含打开的工程文件路径的列表
    """
    result = _list_open_projects()
    if result.get("status") == "error":
        return []
    return result.get("projects", [])


def is_locked(project_path: str) -> bool:
    """检查指定的 CST 工程是否被锁定（正在运行或异常退出遗留锁文件）。

    Args:
        project_path: .cst 文件的绝对路径

    Returns:
        如果工程被锁定则返回 True，否则返回 False
    """
    import pathlib
    lock_file = pathlib.Path(project_path).with_suffix(".cst.lock")
    return lock_file.exists()
