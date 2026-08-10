"""CST 求解器控制操作。

用法：
    from cst_runtime.lib.solver import start, is_running, stop, rebuild

    # 同步启动并等待仿真结束
    start("C:\\path\\to\\model.cst")

    # 检查是否正在运行
    running = is_running("C:\\path\\to\\model.cst")

    # 停止仿真
    stop("C:\\path\\to\\model.cst")

    # 在修改参数后重建结构
    rebuild("C:\\path\\to\\model.cst")
"""
from __future__ import annotations

import time
from typing import Any

from ..core.simulation import start_simulation as _start_simulation
from ..core.simulation import start_simulation_async as _start_simulation_async
from ..core.simulation import is_simulation_running as _is_simulation_running
from ..core.simulation import stop_simulation as _stop_simulation
from ..core.simulation import set_frequency_range as _set_frequency_range
from ..core.simulation import rebuild_structure as _rebuild_structure
from ..core.simulation import delete_results as _delete_results
from ..core.simulation import get_solver_type as _get_solver_type
from ._facade import call_core
from .contracts import OperationResult, error_result, success_result


def set_frequency_range(project_path: str, fmin: float, fmax: float) -> OperationResult:
    """设置求解器的频率范围。

    Args:
        project_path: .cst 文件的绝对路径
        fmin: 最小频率 (GHz)
        fmax: 最大频率 (GHz)

    Raises:
        RuntimeError: 如果无法设置频率范围时抛出
    """
    return call_core(_set_frequency_range, project_path, fmin, fmax)


def start(project_path: str) -> OperationResult:
    """同步启动仿真，阻塞到结束，并检查 CST 返回的成功标志。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法启动仿真时抛出
    """
    return call_core(_start_simulation, project_path)


def start_async(project_path: str) -> OperationResult:
    """异步启动仿真，发送指令后立即返回，不代表求解成功。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法启动仿真时抛出
    """
    return call_core(_start_simulation_async, project_path)


def wait(project_path: str, timeout: int = 3600, interval: int = 10) -> OperationResult:
    """轮询等待异步仿真停止。

    该函数只依据 ``is_solver_running()``。``running=False`` 表示求解器已不再运行，
    不能像同步 ``start()`` 的 ``run_solver=True`` 那样证明求解成功。

    Args:
        project_path: .cst 文件的绝对路径
        timeout: 最大等待时间 (秒)，默认 3600 秒 (1小时)
        interval: 轮询状态的间隔 (秒)，默认 10 秒

    Returns:
        如果仿真在超时前完成则返回 True，如果超时未完成则返回 False
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        running_result = is_running(project_path)
        if running_result.get("status") == "error":
            return running_result
        if not running_result.get("running", False):
            return success_result(project_path=project_path, running=False, completed=True)
        time.sleep(interval)
    return error_result(
        "simulation_wait_timeout",
        "等待仿真完成超时",
        project_path=project_path,
        running=True,
        timeout_seconds=timeout,
    )


def is_running(project_path: str) -> OperationResult:
    """检查仿真当前是否正在运行。

    Args:
        project_path: .cst 文件的绝对路径

    Returns:
        如果正在运行返回 True，否则返回 False
    """
    return call_core(_is_simulation_running, project_path)


def stop(project_path: str) -> OperationResult:
    """手动停止正在运行的仿真。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法停止仿真时抛出
    """
    return call_core(_stop_simulation, project_path)


def rebuild(project_path: str) -> OperationResult:
    """根据最新参数重建几何结构；CST 官方说明此操作会删除全部结果。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果重建失败时抛出
    """
    return call_core(_rebuild_structure, project_path)


def delete_results(project_path: str) -> OperationResult:
    """删除当前工程的所有仿真结果。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法删除结果时抛出
    """
    return call_core(_delete_results, project_path)


def get_solver_type(project_path: str) -> OperationResult:
    """获取当前求解器的类型。

    Args:
        project_path: .cst 文件的绝对路径

    Returns:
        求解器类型的字符串 (例如 "Frequency", "Time", "Eigenmode")

    Raises:
        RuntimeError: 如果无法获取求解器类型时抛出
    """
    return call_core(_get_solver_type, project_path)


def _abs_project_path(project_path: str) -> str:
    """将相对路径转化为绝对路径。"""
    from pathlib import Path
    return str(Path(project_path).expanduser().resolve())
