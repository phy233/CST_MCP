"""长任务让出（L1）的 lib 门面。

tools 层禁止直触 core（架构不变式见 test_architecture.py）；
wait-simulation / run-experiment 的 handler 一律经由本模块访问
阈值解析、阶段信标与让出 payload 构造。
"""
from __future__ import annotations

from ..core.environment import get_long_run_threshold as _core_threshold
from ..core.phase_beacon import POLLING as POLLING
from ..core.phase_beacon import write_phase as _core_write_phase
from ..core.relinquish import (
    RELINQUISH_ERROR_TYPE as RELINQUISH_ERROR_TYPE,
)
from ..core.relinquish import build_relinquish_result as _core_build_relinquish


def get_long_run_threshold() -> int:
    """长任务分界（秒），读 .cst_config.json 的 runtime.* 键。"""
    return _core_threshold()


def write_phase(project_path: str, phase: str) -> bool:
    """写入阶段信标（IO 失败静默）。"""
    return _core_write_phase(project_path, phase)


def build_relinquish_result(**kwargs):
    """构造 L1 让出的标准 terminal payload。"""
    return _core_build_relinquish(**kwargs)
