"""simulation.py — simulation 工具定义"""
from . import _register_tool_defs


TOOL_DEFS = {
"rebuild-model": {
    "category": "simulation",
    "risk": "write",
    "description": (
        "Use this after changing model parameters, in this required order: change-parameter / define-parameters -> "
        "rebuild-model -> save-project. Write all parameters for the current update before rebuilding once. Only save "
        "or solve after rebuild succeeds; stop on failure. This does not start a solver. By default it rebuilds affected "
        "history blocks and removes invalidated results. full_rebuild=true replays all history and deletes all results. "
        "Saving or reopening the project cannot replace rebuilding."
    ),
    "handler": "tool_rebuild_model",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string"},
            "full_rebuild": {"type": "boolean", "default": False},
        },
        "required": ["project_path"],
    },
},
"run-experiment": {
    "category": "simulation",
    "risk": "long-running",
    "description": (
        "Use this to run a fully configured solver and accept completion only when every specified "
        "0D or 1D result path has nonempty data under one new Run ID. Result paths absent before "
        "the solve form an empty baseline, which is valid for a first simulation. It does not "
        "export results; it returns generic result_metrics and retains s11_metric only for S1,1 "
        "compatibility. When timeout_seconds is omitted, the tool returns a terminal "
        "long_run_relinquish signal after runtime.long_run_threshold_seconds (600 seconds by "
        "default) while CST keeps running. Continue with wait-simulation or read evidence using "
        "list-run-ids and export-sparameter. An explicit timeout preserves the traditional "
        "pipeline_sim_timeout behavior and is rejected when it exceeds the MCP transport budget. "
        "Use start-simulation for a plain synchronous solve without result-node acceptance."
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
from ..lib.solver import rebuild
from ._arguments import project_path_from_args


def tool_rebuild_model(args: dict) -> dict:
    """默认只更新受参数影响的历史块，不启动求解器。"""
    return rebuild(project_path_from_args(args), full_rebuild=args.get("full_rebuild", False))


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
