"""simulation.py — simulation 工具定义"""
from . import _register_tool_defs


TOOL_DEFS = {
"run-experiment": {
    "category": "simulation",
    "risk": "long-running",
    "description": (
        "运行求解并等待完成；必须以指定 0D/1D 结果节点共同出现的新 Run ID 和非空数据验收。"
        "不执行任何结果导出，返回通用 result_metrics；S1,1 仅保留兼容 s11_metric。"
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
                    3600
                ]
            }
        },
        "required": ["project_path", "completion_result_paths", "timeout_seconds"],
        "additionalProperties": False
    },
},
}


# --- Handlers ---

from ..lib.experiments import run_experiment
from ._arguments import project_path_from_args


def tool_run_experiment(args: dict) -> dict:
    return run_experiment(
        project_path=str(args.get("project_path", "")),
        completion_result_paths=list(args.get("completion_result_paths") or []),
        timeout_seconds=int(args.get("timeout_seconds", 3600)),
    )


_register_tool_defs(TOOL_DEFS)
