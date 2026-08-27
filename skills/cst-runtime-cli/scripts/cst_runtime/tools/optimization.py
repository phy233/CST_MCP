from __future__ import annotations

from typing import Any

from ..lib import optimization as _opt
from . import _register_tool_defs


def _lazy_pipeline(name: str):
    import importlib
    mod = importlib.import_module("..cli.pipelines.impl", __package__)
    return getattr(mod, name)


_register_tool_defs({
    "create-study": {
        "category": "optimization",
        "risk": "filesystem-write",
        "description": "Create or load an Optuna optimization study. Supports single-objective, multi-objective (directions), and constraint-enabled studies.",
        "handler": "tool_create_study",
        "json_schema": {
            "type": "object",
            "properties": {
                "storage_path": {
                    "type": "string",
                    "examples": [
                        "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\studies\\optimization.db"
                    ]
                },
                "study_name": {
                    "type": "string",
                    "examples": [
                        "horn_matching"
                    ]
                },
                "parameters": {
                    "type": ["object", "string"],
                    "description": (
                        "参数定义，JSON 对象或 JSON 字符串；例如 "
                        "{\"R\": {\"type\": \"float\", \"min\": 0.1, \"max\": 0.5}}。"
                        "type 支持 float/int/categorical。"
                    ),
                    "examples": [
                        {
                            "R": {"type": "float", "min": 0.1, "max": 0.5},
                            "g": {"type": "float", "min": 20, "max": 30}
                        }
                    ]
                },
                "direction": {
                    "type": "string",
                    "enum": ["minimize", "maximize"],
                    "default": "minimize",
                    "description": "单目标优化方向；与 directions 二选一。"
                },
                "directions": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["minimize", "maximize"]
                    },
                    "default": [],
                    "description": "多目标方向数组（长度即目标数）；与 direction 二选一；留空表示单目标。"
                },
                "value_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "目标名称列表，便于报告阅读；多目标时建议提供。"
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "object"},
                    "default": [],
                    "description": "约束定义对象数组，每个含 name/operator/threshold。",
                    "examples": [
                        [
                            {
                                "name": "VSWR",
                                "operator": "<=",
                                "threshold": 2.0
                            }
                        ]
                    ]
                },
                "sampler": {
                    "type": "string",
                    "enum": ["tpe", "cma-es", "random"],
                    "default": "tpe"
                },
                "n_startup_trials": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 10
                }
            },
            "required": ["storage_path", "study_name", "parameters"]
        },
    },
    "ask-study": {
        "category": "optimization",
        "risk": "read",
        "description": "Ask the study for the next trial parameter suggestion.",
        "handler": "tool_ask_study",
        "json_schema": {
        "type": "object",
        "properties": {
            "storage_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\studies\\optimization.db"
                ]
            },
            "study_name": {
                "type": "string",
                "examples": [
                    "horn_matching"
                ]
            }
        },
        "required": [
            "storage_path",
            "study_name"
        ]
    },
    },
    "tell-study": {
        "category": "optimization",
        "risk": "filesystem-write",
        "description": "Report trial result. Provide exactly one of value (single-objective) or values (multi-objective); state is complete or pruned.",
        "handler": "tool_tell_study",
        "json_schema": {
            "type": "object",
            "properties": {
                "storage_path": {
                    "type": "string",
                    "examples": [
                        "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\studies\\optimization.db"
                    ]
                },
                "study_name": {
                    "type": "string",
                    "examples": [
                        "horn_matching"
                    ]
                },
                "trial_number": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "ask-study 返回的 trial 编号。",
                    "examples": [
                        3
                    ]
                },
                "value": {
                    "type": ["number", "null"],
                    "default": None,
                    "description": "单目标目标值；与 values 二选一。"
                },
                "values": {
                    "type": ["array", "null"],
                    "items": {"type": "number"},
                    "default": None,
                    "description": "多目标目标值数组，长度须等于 study 目标数；与 value 二选一。"
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "number"},
                    "default": [],
                    "description": "可选约束值数组；为空表示无约束。",
                    "examples": [
                        [
                            -1.0,
                            0.5
                        ]
                    ]
                },
                "state": {
                    "type": "string",
                    "enum": ["complete", "pruned"],
                    "default": "complete",
                    "description": "trial 终态：complete 计入优化，pruned 不计入 best。"
                }
            },
            "required": [
                "storage_path",
                "study_name",
                "trial_number"
            ],
            "anyOf": [
                {
                    "required": ["value"],
                    "not": {"required": ["values"]}
                },
                {
                    "required": ["values"],
                    "not": {"required": ["value"]}
                }
            ]
        },
    },
    "best-study": {
        "category": "optimization",
        "risk": "read",
        "description": "Get current best result. For multi-objective returns Pareto front samples.",
        "handler": "tool_best_study",
        "json_schema": {
        "type": "object",
        "properties": {
            "storage_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\studies\\optimization.db"
                ]
            },
            "study_name": {
                "type": "string",
                "examples": [
                    "horn_matching"
                ]
            }
        },
        "required": [
            "storage_path",
            "study_name"
        ]
    },
    },
    "study-add-trials": {
        "category": "optimization",
        "risk": "filesystem-write",
        "description": "Inject pre-computed trials (e.g. from manual grid scan) into a study. Each trial: {params, values, constraints?}.",
        "handler": "tool_add_trials",
        "json_schema": {
        "type": "object",
        "properties": {
            "storage_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\studies\\optimization.db"
                ]
            },
            "study_name": {
                "type": "string",
                "examples": [
                    "horn_matching"
                ]
            },
            "trials": {
                "type": "array",
                "items": {
                    "type": "object"
                },
                "examples": [
                    [
                        {
                            "params": {
                                "R": 0.1
                            },
                            "values": [
                                -28.7
                            ]
                        },
                        {
                            "params": {
                                "R": 0.2
                            },
                            "values": [
                                -39.9
                            ]
                        }
                    ]
                ]
            }
        },
        "required": [
            "storage_path",
            "study_name",
            "trials"
        ]
    },
    },
    "study-param-importances": {
        "category": "optimization",
        "risk": "read",
        "description": "Analyze which parameters most affect the objective. Requires at least 5 completed trials.",
        "handler": "tool_param_importances",
        "json_schema": {
        "type": "object",
        "properties": {
            "storage_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\studies\\optimization.db"
                ]
            },
            "study_name": {
                "type": "string",
                "examples": [
                    "horn_matching"
                ]
            }
        },
        "required": [
            "storage_path",
            "study_name"
        ]
    },
    },
    "study-terminate-check": {
        "category": "optimization",
        "risk": "read",
        "description": "Check if optimization has converged using Optuna's regret-bound evaluator. Returns should_terminate.",
        "handler": "tool_terminate_check",
        "json_schema": {
        "type": "object",
        "properties": {
            "storage_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\studies\\optimization.db"
                ]
            },
            "study_name": {
                "type": "string",
                "examples": [
                    "horn_matching"
                ]
            }
        },
        "required": [
            "storage_path",
            "study_name"
        ]
    },
    },
    "run-probe-phase": {
        "category": "optimization",
        "risk": "long-running",
        "description": (
            "Run the complete probe phase: design Plackett-Burman probes, simulate each "
            "(on a main-file-only working_probe.cst copy; companion dir is recreated by CST on first open), "
            "analyze main effects and interactions, then inject results into an Optuna study. "
            "Returns top_params, edge_hit, and suggested_algorithm. "
            "Objective spec supports metasurface metrics: {\"type\": \"s11_min_db\"} | "
            "{\"type\": \"s11_at_freq\", \"freq\": 10} | {\"type\": \"gain_max\"} | "
            "{\"type\": \"bandwidth\", \"below_db\": -10} | "
            "{\"type\": \"amp_at_freq\", \"result_path\": \"zmax(1)\", \"freq\": 10, \"direction\": \"maximize\"} | "
            "{\"type\": \"phase_at_freq\", \"result_path\": \"zmax(1)\", \"freq\": 10, \"target_deg\": 90} | "
            "{\"type\": \"expression\", \"expr\": \"abs(wrap(phase_deg('zmax(1)', 10) - 90))\"}; "
            "expression sandbox exposes s11_db/s11_freq, amp_db(path,f), phase_deg(path,f), wrap(x), min/max/len/abs."
        ),
        "handler": "tool_run_probe_phase",
        "json_schema": {
            "$schema": "https://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["project_path", "completion_result_paths", "parameters", "study_storage", "study_name"],
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to working.cst",
                    "default": "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                },
                "completion_result_paths": {
                    "type": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {"type": "string", "minLength": 1},
                    "description": "用于确认本次求解产生新 Run ID 且数据非空的真实 ResultTree 完整路径；Floquet 单元常用 SZmin(1),Zmax(1)"
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameter ranges for DOE screening, keyed by parameter name. Each value: {min, max, type?}. Names must exist in the project parameter table.",
                    "additionalProperties": {
                        "type": "object",
                        "required": ["min", "max"],
                        "properties": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                            "type": {"type": "string", "enum": ["float", "int"]}
                        }
                    }
                },
                "study_storage": {
                    "type": "string",
                    "description": "Path to Optuna SQLite storage file",
                    "default": "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\studies\\optimization.db"
                },
                "study_name": {
                    "type": "string",
                    "description": "Name for the Optuna study",
                    "default": "horn_matching"
                },
                "max_probes": {
                    "type": "integer",
                    "default": 12,
                    "description": "Maximum number of probe points"
                },
                "include_center": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include center point in probe design"
                },
                "objective": {
                    "type": "object",
                    "default": {"type": "s11_min_db"},
                    "description": (
                        "Objective function spec. Types: s11_min_db | s11_at_freq{freq} | gain_max | bandwidth | "
                        "amp_at_freq{result_path?,freq,direction?} | phase_at_freq{result_path?,freq,target_deg} | "
                        "expression{expr}. result_path 支持归一化子串匹配（如 'zmax(1)'）。"
                    )
                }
            }
        }
    },
    "run-optimization-step": {
        "category": "optimization",
        "risk": "long-running",
        "description": (
            "Run one optimization iteration: ask Optuna for next parameters, apply them, simulate, "
            "compute objective, and report back. Agent inspects the objective_value output to decide "
            "whether to stop or continue the loop. Objective spec supports metasurface metrics: "
            "{\"type\": \"s11_min_db\"} | {\"type\": \"s11_at_freq\", \"freq\": 10} | {\"type\": \"gain_max\"} | "
            "{\"type\": \"bandwidth\", \"below_db\": -10} | "
            "{\"type\": \"amp_at_freq\", \"result_path\": \"zmax(1)\", \"freq\": 10, \"direction\": \"maximize\"} | "
            "{\"type\": \"phase_at_freq\", \"result_path\": \"zmax(1)\", \"freq\": 10, \"target_deg\": 90} | "
            "{\"type\": \"expression\", \"expr\": \"abs(wrap(phase_deg('zmax(1)', 10) - 90))\"}; "
            "expression sandbox exposes s11_db/s11_freq, amp_db(path,f), phase_deg(path,f), wrap(x), min/max/len/abs."
        ),
        "handler": "tool_run_optimization_step",
        "json_schema": {
            "$schema": "https://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["project_path", "completion_result_paths", "study_storage", "study_name"],
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to working.cst",
                    "default": "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                },
                "completion_result_paths": {
                    "type": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {"type": "string", "minLength": 1},
                    "description": "用于确认本次求解产生新 Run ID 且数据非空的真实 ResultTree 完整路径；Floquet 单元常用 SZmin(1),Zmax(1)"
                },
                "study_storage": {
                    "type": "string",
                    "description": "Path to Optuna SQLite storage file",
                    "default": "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\studies\\optimization.db"
                },
                "study_name": {
                    "type": "string",
                    "description": "Name of the Optuna study",
                    "default": "horn_matching"
                },
                "objective": {
                    "type": "object",
                    "default": {"type": "s11_min_db"},
                    "description": (
                        "Objective function spec. Types: s11_min_db | s11_at_freq{freq} | gain_max | bandwidth | "
                        "amp_at_freq{result_path?,freq,direction?} | phase_at_freq{result_path?,freq,target_deg} | "
                        "expression{expr}. result_path 支持归一化子串匹配（如 'zmax(1)'）。"
                    )
                },
                "sampler": {
                    "type": "string",
                    "enum": ["tpe", "cma-es", "random"],
                    "description": "Override study sampler. Creates a new study with the specified sampler, migrates existing trials."
                }
            }
        }
    },
})


def tool_create_study(args: dict) -> dict:
    from ..lib.contracts import error_result

    direction = args.get("direction")
    directions = args.get("directions") or None
    if direction is not None and directions is not None:
        normalized = [str(item) for item in directions]
        if str(direction) not in normalized or len(normalized) != 1:
            return error_result(
                "invalid_arguments",
                "direction 与 directions 同时提供且不一致；单目标请只提供其一",
            )
    if direction is None and directions is None:
        direction = "minimize"
    return _opt.create_study(
        storage_path=str(args.get("storage_path", "")),
        study_name=str(args.get("study_name", "")),
        parameters=args.get("parameters", "{}"),
        direction=str(direction or "minimize"),
        directions=list(directions) if directions else None,
        value_names=(args.get("value_names") or None),
        constraints=(args.get("constraints") or None),
        sampler=str(args.get("sampler", "tpe")),
        n_startup_trials=int(args.get("n_startup_trials", 10)),
    )


def tool_ask_study(args: dict) -> dict:
    return _opt.ask_study(
        storage_path=str(args.get("storage_path", "")),
        study_name=str(args.get("study_name", "")),
    )


def tool_tell_study(args: dict) -> dict:
    from ..lib.contracts import error_result

    value = args.get("value")
    values = args.get("values")
    if (value is None) == (values is None):
        return error_result(
            "invalid_arguments",
            "value 与 values 必须二选一：单目标传 value，多目标传 values",
        )
    constraints = args.get("constraints")
    if isinstance(constraints, list) and not constraints:
        constraints = None
    state = str(args.get("state") or "complete")
    if state not in {"complete", "pruned"}:
        return error_result(
            "invalid_arguments",
            f"state 仅支持 complete/pruned，收到: {state}",
        )
    return _opt.tell_study(
        storage_path=str(args.get("storage_path", "")),
        study_name=str(args.get("study_name", "")),
        trial_number=int(args.get("trial_number", 0)),
        value=value,
        values=list(values) if values is not None else None,
        constraints=constraints,
        state=state,
    )


def tool_best_study(args: dict) -> dict:
    return _opt.best_study(
        storage_path=str(args.get("storage_path", "")),
        study_name=str(args.get("study_name", "")),
    )


def tool_add_trials(args: dict) -> dict:
    return _opt.add_trials(
        storage_path=str(args.get("storage_path", "")),
        study_name=str(args.get("study_name", "")),
        trials=args.get("trials", []),
    )


def tool_param_importances(args: dict) -> dict:
    return _opt.param_importances(
        storage_path=str(args.get("storage_path", "")),
        study_name=str(args.get("study_name", "")),
    )


def tool_terminate_check(args: dict) -> dict:
    return _opt.terminate_check(
        storage_path=str(args.get("storage_path", "")),
        study_name=str(args.get("study_name", "")),
    )


def tool_run_probe_phase(args: dict) -> dict:
    _run = _lazy_pipeline("pipeline_run_probe_phase")
    return _run(
        project_path=str(args["project_path"]),
        completion_result_paths=list(args["completion_result_paths"]),
        parameters=args.get("parameters", {}),
        study_storage=str(args["study_storage"]),
        study_name=str(args["study_name"]),
        max_probes=int(args.get("max_probes", 12)),
        include_center=bool(args.get("include_center", True)),
        objective=args.get("objective"),
    )


def tool_run_optimization_step(args: dict) -> dict:
    _run = _lazy_pipeline("pipeline_run_optimization_step")
    return _run(
        project_path=str(args["project_path"]),
        completion_result_paths=list(args["completion_result_paths"]),
        study_storage=str(args["study_storage"]),
        study_name=str(args["study_name"]),
        objective=args.get("objective"),
        sampler=args.get("sampler"),
    )
