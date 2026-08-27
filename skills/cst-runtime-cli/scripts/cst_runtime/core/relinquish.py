"""长任务让出（L1 relinquish）的统一返回形态。

冻结计划 v3.3：solver 实际运行时长达到 ``long_run_threshold_seconds``
（默认 600s）时，runtime 主动结束本次阻塞调用——不做 postflight、
不关闭工程、CST/DE 原样保留，由 MCP proxy 记录 journal 终态后终止
worker 进程；agent 收到 terminal payload 后停止等待并结束回合。

CLI 直调同样得到该结构化信号；显式传入更大的 timeout_seconds 表示
选择"单次等待到底"，让出机制自动禁用（MCP 治理层会拒绝超过其传输
预算的值，CLI 则完全自由）。
"""
from __future__ import annotations

from typing import Any


def build_relinquish_result(
    *,
    project_path: str,
    waited_seconds: float,
    polls: int,
    long_run_threshold_seconds: int,
    source_tool: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构造 L1 让出的标准错误形态（status=error 但 terminal=True）。"""
    payload: dict[str, Any] = {
        "status": "error",
        "error_type": "long_run_relinquish",
        "message": (
            f"求解器已运行 {waited_seconds:.0f}s 达到长任务分界 "
            f"{long_run_threshold_seconds}s，本次调用让出等待；"
            "CST 求解器仍在后台运行且未被触碰。"
        ),
        "project_path": str(project_path),
        "terminal": True,
        "await_user_decision": True,
        "timeout_class": "expected_simulation",
        "solver_left_running": True,
        "long_run_threshold_seconds": long_run_threshold_seconds,
        "waited_seconds": round(float(waited_seconds), 3),
        "polls": int(polls),
        "source_tool": str(source_tool),
        "next_action": [
            "立即停止本回合对该任务的所有后续 CST 工具调用"
            "（不重试、不轮询、不重复启动求解）",
            "把 detached 状态作为阶段结论汇报给用户，注明求解仍在进行",
            "恢复时机由用户决定，参照 recovery 序列",
        ],
        "recovery": [
            "cst-session-inspect --project-path <工程> 先确认锁与求解器状态",
            "list-run-ids / export-sparameter 只读取证已完成的 Run ID",
            "确需模型会话时使用 cst-session-reattach 的授权接管流程",
        ],
        "runtime_module": "cst_runtime.core.relinquish",
    }
    if extra:
        payload.update(extra)
    return payload
