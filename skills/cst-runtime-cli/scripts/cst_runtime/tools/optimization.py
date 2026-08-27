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
        "description": (
            "Use this to create or load an Optuna study after the human has defined the "
            "parameter space, objective directions, constraints, and evaluation budget. "
            "It configures study storage only and does not run CST or choose the design problem."
        ),
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
                        "Parameter definitions as a JSON object or JSON string, for example "
                        "{\"R\": {\"type\": \"float\", \"min\": 0.1, \"max\": 0.5}}. "
                        "Supported types are float, int, and categorical."
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
                    "description": "Single-objective direction; mutually exclusive with directions."
                },
                "directions": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["minimize", "maximize"]
                    },
                    "default": [],
                    "description": (
                        "Multi-objective direction array whose length is the objective count; "
                        "mutually exclusive with direction. Leave empty for a single objective."
                    )
                },
                "value_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Objective names for readable reports; recommended for multi-objective studies."
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "object"},
                    "default": [],
                    "description": "Constraint definitions, each containing name, operator, and threshold.",
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
        "risk": "filesystem-write",
        "description": (
            "Use this when the next trial will actually be evaluated: it asks Optuna for "
            "parameters and persists a new pending trial. It is not a passive read; finish "
            "that trial with tell-study, or use run-optimization-step for a closed iteration."
        ),
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
        "description": (
            "Use this to finish one known trial returned by ask-study. Provide exactly one "
            "of value for a single objective or values for multiple objectives, and mark the "
            "trial complete or pruned; it does not run CST."
        ),
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
                    "description": "Trial number returned by ask-study.",
                    "examples": [
                        3
                    ]
                },
                "value": {
                    "type": ["number", "null"],
                    "default": None,
                    "description": "Single-objective value; mutually exclusive with values."
                },
                "values": {
                    "type": ["array", "null"],
                    "items": {"type": "number"},
                    "default": None,
                    "description": (
                        "Multi-objective value array whose length must match the study's "
                        "objective count; mutually exclusive with value."
                    )
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "number"},
                    "default": [],
                    "description": "Optional constraint values; leave empty when the study has no constraints.",
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
                    "description": (
                        "Final trial state: complete contributes to optimization results, "
                        "whereas pruned is excluded from the best result."
                    )
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
        "description": (
            "Use this to read the current best completed trial for a single objective or "
            "the Pareto-front samples for multiple objectives. It does not evaluate a trial "
            "or decide whether optimization should stop."
        ),
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
        "description": (
            "Use this to import already evaluated trials, such as a human-managed grid scan, "
            "into an existing study. It does not request suggestions or run CST; each trial "
            "must provide params, values, and optional constraints."
        ),
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
        "description": (
            "Use this after at least five completed trials to estimate which parameters most "
            "affect the objective. It reads study history only and does not alter the study."
        ),
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
        "description": (
            "Use this to obtain a regret-bound-based should_terminate recommendation from an "
            "existing study. It is decision support only: it neither stops the study nor "
            "replaces a human-defined evaluation budget or engineering acceptance criteria."
        ),
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
            "Use this to run the complete screening phase: generate Plackett-Burman probes, "
            "evaluate each in CST on a dedicated working_probe.cst copy, analyze main and "
            "two-way effects, and seed an Optuna study. It is not a general optimization loop; "
            "the human must define valid parameters, completion paths, objective, and probe budget."
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
                    "description": (
                        "Exact ResultTree paths used to confirm a new Run ID with nonempty data; "
                        "Floquet unit cells commonly use paths such as SZmin(1),Zmax(1)."
                    )
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
                        "expression{expr}. result_path supports normalized substring matching, such as 'zmax(1)'."
                    )
                }
            }
        }
    },
    "run-optimization-step": {
        "category": "optimization",
        "risk": "long-running",
        "description": (
            "Use this to execute exactly one closed Optuna iteration: request parameters, "
            "update the project, run the solver, compute the objective, and report the trial. "
            "It does not choose the design problem or stopping rule; inspect its output before "
            "invoking another step within the human-defined objective and evaluation budget."
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
                    "description": (
                        "Exact ResultTree paths used to confirm a new Run ID with nonempty data; "
                        "Floquet unit cells commonly use paths such as SZmin(1),Zmax(1)."
                    )
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
                        "expression{expr}. result_path supports normalized substring matching, such as 'zmax(1)'."
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
