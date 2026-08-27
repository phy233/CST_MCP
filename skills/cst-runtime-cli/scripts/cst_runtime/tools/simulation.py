"""simulation.py — simulation 工具定义"""
from . import _register_tool_defs


TOOL_DEFS = {
"run-experiment": {
    "category": "simulation",
    "risk": "long-running",
    "description": (
        "运行求解并等待完成；必须以指定 0D/1D 结果节点共同出现的新 Run ID 和非空数据验收。"
        "求解前结果节点尚不存在视为空基线（首次仿真的正常初始状态，支持由本次仿真生成节点）；"
        "不执行任何结果导出，返回通用 result_metrics；S1,1 仅保留兼容 s11_metric。"
        "省缺 timeout_seconds 为自动让出模式：solver 实际运行达到 "
        "runtime.long_run_threshold_seconds（默认 600s）时返回 "
        "long_run_relinquish 终态信号（terminal=true，CST 继续运行），"
        "完成后用 list-run-ids/export-sparameter 只读取证或以 "
        "wait-simulation 接力；显式传值则维持传统阻塞上限语义"
        "（pipeline_sim_timeout，MCP 下超过传输预算会被治理拒绝）。"
    ),
    "handler": "tool_run_experiment",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "completion_result_paths": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {
                    "type": "string",
                    "minLength": 1
                },
                "examples": [
                    ["1D Results\\S-Parameters\\SZmin(1),Zmax(1)"]
                ]
            },
            "timeout_seconds": {
                "type": "integer",
                "examples": [
                    600
                ]
            }
        },
        "required": ["project_path", "completion_result_paths", "timeout_seconds"],
        "additionalProperties": False
    },
},
}


# --- Handlers ---

from typing import Any

from ..lib.experiments import run_experiment
from ._arguments import project_path_from_args


def tool_run_experiment(args: dict) -> dict:
    """timeout_seconds 省缺 ⇒ 自动让出模式（L1，见 lib.experiments 文档）；
    显式数值 ⇒ 传统阻塞上限语义，不触发自动让出。"""
    passthrough: dict[str, Any] = {}
    if args.get("timeout_seconds") is not None:
        passthrough["timeout_seconds"] = float(args["timeout_seconds"])
    return run_experiment(
        project_path=str(args.get("project_path", "")),
        completion_result_paths=list(args.get("completion_result_paths") or []),
        **passthrough,
    )


_register_tool_defs(TOOL_DEFS)
