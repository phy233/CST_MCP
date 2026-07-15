"""CST 求解器控制操作。

用法：
    from cst_runtime.lib.solver import start, is_running, stop, rebuild

    # 启动仿真 (非阻塞)
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
from ..core.identity import attach_expected_project


def set_frequency_range(project_path: str, fmin: float, fmax: float) -> None:
    """设置求解器的频率范围。

    Args:
        project_path: .cst 文件的绝对路径
        fmin: 最小频率 (GHz)
        fmax: 最大频率 (GHz)

    Raises:
        RuntimeError: 如果无法设置频率范围时抛出
    """
    from ..core.simulation import _single_vba_pops
    vba = f'Solver.FrequencyRange "{fmin}", "{fmax}"'
    result = _single_vba_pops(project_path, "Set Frequency Range", vba)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set frequency range"))


def start(project_path: str) -> None:
    """启动仿真 (阻塞模式，直到完成才会返回)。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法启动仿真时抛出
    """
    result = _start_simulation(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to start simulation"))


def start_async(project_path: str) -> None:
    """启动仿真 (非阻塞模式，发送指令后立即返回)。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法启动仿真时抛出
    """
    result = _start_simulation_async(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to start simulation"))


def wait(project_path: str, timeout: int = 3600, interval: int = 10) -> bool:
    """等待仿真完成。

    Args:
        project_path: .cst 文件的绝对路径
        timeout: 最大等待时间 (秒)，默认 3600 秒 (1小时)
        interval: 轮询状态的间隔 (秒)，默认 10 秒

    Returns:
        如果仿真在超时前完成则返回 True，如果超时未完成则返回 False
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not is_running(project_path):
            return True
        time.sleep(interval)
    return False


def is_running(project_path: str) -> bool:
    """检查仿真当前是否正在运行。

    Args:
        project_path: .cst 文件的绝对路径

    Returns:
        如果正在运行返回 True，否则返回 False
    """
    result = _is_simulation_running(project_path)
    if result.get("status") == "error":
        return False
    return result.get("running", False)


def stop(project_path: str) -> None:
    """手动停止正在运行的仿真。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法停止仿真时抛出
    """
    result = _stop_simulation(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to stop simulation"))


def rebuild(project_path: str) -> None:
    """根据最新的参数重建几何结构 (相当于点击 CST 里的 F7)。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果重建失败时抛出
    """
    from ..core.simulation import _single_vba_pops
    result = _single_vba_pops(project_path, "Rebuild", "Application.Rebuild")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to rebuild structure"))


def delete_results(project_path: str) -> None:
    """删除当前工程的所有仿真结果。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法删除结果时抛出
    """
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        raise RuntimeError(status.get("message", "Project not found"))
    try:
        project.model3d.DeleteResults()
    except Exception as e:
        raise RuntimeError(f"Failed to delete results: {e}")


def get_solver_type(project_path: str) -> str:
    """获取当前求解器的类型。

    Args:
        project_path: .cst 文件的绝对路径

    Returns:
        求解器类型的字符串 (例如 "Frequency", "Time", "Eigenmode")

    Raises:
        RuntimeError: 如果无法获取求解器类型时抛出
    """
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        raise RuntimeError(status.get("message", "Project not found"))
    try:
        return project.model3d.GetSolverType()
    except Exception as e:
        raise RuntimeError(f"Failed to get solver type: {e}")


def _abs_project_path(project_path: str) -> str:
    """将相对路径转化为绝对路径。"""
    from pathlib import Path
    return str(Path(project_path).expanduser().resolve())
