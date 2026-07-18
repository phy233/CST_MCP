"""MCP Tool definitions: CST Solver operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def start(project_path: str) -> dict[str, Any]:
    """
    启动仿真 (阻塞模式，直到完成才会返回)。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法启动仿真时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.solver", "start", project_path=project_path)

def wait(project_path: str, timeout: int = 3600, interval: int = 10) -> dict[str, Any]:
    """
    等待仿真完成。

    Args:
        project_path: .cst 文件的绝对路径
        timeout: 最大等待时间 (秒)，默认 3600 秒 (1小时)
        interval: 轮询状态的间隔 (秒)，默认 10 秒

    Returns:
        如果仿真在超时前完成则返回 True，如果超时未完成则返回 False
    """
    return call_cst("lib.solver", "wait", project_path=project_path, timeout=timeout, interval=interval)

def is_running(project_path: str) -> dict[str, Any]:
    """
    检查仿真当前是否正在运行。

    Args:
        project_path: .cst 文件的绝对路径

    Returns:
        如果正在运行返回 True，否则返回 False
    """
    return call_cst("lib.solver", "is_running", project_path=project_path)

def stop(project_path: str) -> dict[str, Any]:
    """
    手动停止正在运行的仿真。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法停止仿真时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.solver", "stop", project_path=project_path)

def rebuild(project_path: str) -> dict[str, Any]:
    """
    根据最新的参数重建几何结构 (相当于点击 CST 里的 F7)。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果重建失败时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.solver", "rebuild", project_path=project_path)

def delete_results(project_path: str) -> dict[str, Any]:
    """
    删除当前工程的所有仿真结果。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法删除结果时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.solver", "delete_results", project_path=project_path)

def set_frequency_range(project_path: str, fmin: float, fmax: float) -> dict[str, Any]:
    """
    设置求解器的频率范围。

    Args:
        project_path: .cst 文件的绝对路径
        fmin: 最小频率 (GHz)
        fmax: 最大频率 (GHz)

    Raises:
        RuntimeError: 如果无法设置频率范围时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.solver", "set_frequency_range", project_path=project_path, fmin=fmin, fmax=fmax)

SOLVER_TOOLS = [
    {"name": "start", "handler": start},
    {"name": "wait", "handler": wait},
    {"name": "is-running", "handler": is_running},
    {"name": "stop", "handler": stop},
    {"name": "rebuild", "handler": rebuild},
    {"name": "delete-results", "handler": delete_results},
    {"name": "set-frequency-range", "handler": set_frequency_range},
]
