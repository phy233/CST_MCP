"""project_ops.py — project_ops + project_identity 工具定义"""
from . import _register_tool_defs
from ..lib.modeling import CST_2022_SOLVER_TYPES


TOOL_DEFS = {
"change-parameter": {
    "category": "project_ops",
    "risk": "write",
    "description": "Change one CST parameter in the verified working project.",
    "handler": "tool_change_parameter",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "R"
                ]
            },
            "value": {
                "type": "number",
                "examples": [
                    0.102
                ]
            }
        },
        "required": [
            "project_path",
            "name",
            "value"
        ]
    },
},

"change-solver-type": {
    "category": "project_ops",
    "risk": "write",
    "description": "Change the CST solver type.",
    "handler": "tool_change_solver_type",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "solver_type": {
                "type": "string",
                "enum": list(CST_2022_SOLVER_TYPES),
                "examples": [
                    "HF Time Domain"
                ]
            }
        },
        "required": [
            "project_path",
            "solver_type"
        ]
    },
},

"define-background": {
    "category": "project_ops",
    "risk": "write",
    "description": "Set the background type (Normal or PEC).",
    "handler": "tool_define_background",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": ["C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"]
            },
            "background_type": {
                "type": "string",
                "default": "Normal",
                "description": "Background material type.",
                "examples": ["Normal", "PEC"]
            }
        },
        "required": ["project_path"]
    },
},

"define-boundary": {
    "category": "project_ops",
    "risk": "write",
    "description": (
        "设置全部面的通用边界和对称性；该工具不等价于完整的 Unit Cell 或 "
        "Floquet 配置。高级周期边界需求应由用户在 CST 图形界面中手动完成。"
    ),
    "handler": "tool_define_boundary",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": ["C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"]
            },
            "face_type": {
                "type": "string",
                "default": "expanded open",
                "description": "Boundary type for Xmin-Xmax, Ymin-Ymax, Zmin-Zmax.",
                "examples": ["expanded open", "electric", "magnetic", "open", "conducting wall"]
            },
            "symmetry_type": {
                "type": "string",
                "default": "none",
                "description": "Symmetry type for X/Y/Zsymmetry.",
                "examples": ["none", "electric", "magnetic"]
            }
        },
        "required": ["project_path"]
    },
},

"define-frequency-range": {
    "category": "project_ops",
    "risk": "write",
    "description": "Set the simulation frequency range.",
    "handler": "tool_define_frequency_range",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "start_freq": {
                "type": "number",
                "examples": [
                    2.0
                ]
            },
            "end_freq": {
                "type": "number",
                "examples": [
                    18.0
                ]
            }
        },
        "required": [
            "project_path",
            "start_freq",
            "end_freq"
        ]
    },
},

"define-mesh": {
    "category": "project_ops",
    "risk": "write",
    "description": "Configure the hexahedral mesh parameters.",
    "handler": "tool_define_mesh",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "steps_per_wave_near": {
                "type": "integer",
                "examples": [
                    5
                ]
            },
            "steps_per_wave_far": {
                "type": "integer",
                "examples": [
                    5
                ]
            },
            "steps_per_box_near": {
                "type": "integer",
                "examples": [
                    5
                ]
            },
            "steps_per_box_far": {
                "type": "integer",
                "examples": [
                    1
                ]
            }
        },
        "required": [
            "project_path",
            "steps_per_wave_near",
            "steps_per_wave_far",
            "steps_per_box_near",
            "steps_per_box_far"
        ]
    },
},

"define-monitor": {
    "category": "project_ops",
    "risk": "write",
    "description": "Define a farfield monitor over a frequency range.",
    "handler": "tool_define_monitor",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "start_freq": {
                "type": "number",
                "examples": [
                    2.0
                ]
            },
            "end_freq": {
                "type": "number",
                "examples": [
                    18.0
                ]
            },
            "step": {
                "type": "number",
                "examples": [
                    1
                ]
            }
        },
        "required": [
            "project_path",
            "start_freq",
            "end_freq",
            "step"
        ]
    },
},

"define-parameters": {
    "category": "project_ops",
    "risk": "write",
    "description": "Batch-define multiple CST parameters using StoreParameters.",
    "handler": "tool_define_parameters",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "names": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "examples": [
                    [
                        "a",
                        "b",
                        "h"
                    ]
                ]
            },
            "values": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "examples": [
                    [
                        "10",
                        "5*b",
                        "2"
                    ]
                ]
            }
        },
        "required": [
            "project_path",
            "names",
            "values"
        ]
    },
},

"define-port": {
    "category": "project_ops",
    "risk": "write",
    "description": (
        "Define an internal axis-aligned waveguide port from global X/Y/Z ranges. "
        "Collapse the normal-axis range to the port plane; *min radiates +axis and *max radiates -axis."
    ),
    "handler": "tool_define_port",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "port_number": {
                "type": "string",
                "examples": [
                    "1"
                ]
            },
            "x_min": {
                "type": "number",
                "description": "Global lower X bound.",
                "examples": [
                    -10
                ]
            },
            "x_max": {
                "type": "number",
                "description": "Global upper X bound.",
                "examples": [
                    10
                ]
            },
            "y_min": {
                "type": "number",
                "description": "Global lower Y bound.",
                "examples": [
                    -10
                ]
            },
            "y_max": {
                "type": "number",
                "description": "Global upper Y bound.",
                "examples": [
                    10
                ]
            },
            "z_min": {
                "type": "number",
                "description": "Global lower Z bound.",
                "examples": [
                    0
                ]
            },
            "z_max": {
                "type": "number",
                "description": "Global upper Z bound.",
                "examples": [
                    5
                ]
            },
            "orientation": {
                "type": "string",
                "description": "Port normal side and radiation direction: xmin/xmax/ymin/ymax/zmin/zmax.",
                "examples": [
                    "zmin"
                ]
            }
        },
        "required": [
            "project_path",
            "port_number",
            "x_min",
            "x_max",
            "y_min",
            "y_max",
            "z_min",
            "z_max",
            "orientation"
        ]
    },
},

"define-solver": {
    "category": "project_ops",
    "risk": "write",
    "description": "Configure the time-domain solver settings.",
    "handler": "tool_define_solver",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": ["C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"]
            },
            "stimulation_port":         {"type": "string",  "default": "All", "examples": ["All"]},
            "stimulation_mode":         {"type": "string",  "default": "All", "examples": ["All"]},
            "steady_state_limit":       {"type": "number",  "default": -40,   "examples": [-40]},
            "norming_impedance":        {"type": "number",  "default": 50,    "examples": [50]},
            "mesh_adaption":            {"type": "boolean", "default": False},
            "auto_norm_impedance":      {"type": "boolean", "default": True},
            "calculate_modes_only":     {"type": "boolean", "default": False},
            "s_para_symmetry":          {"type": "boolean", "default": False},
            "store_td_results":         {"type": "boolean", "default": False},
            "run_discretizer_only":     {"type": "boolean", "default": False},
            "full_deembedding":         {"type": "boolean", "default": False},
            "superimpose_plw":          {"type": "boolean", "default": False},
            "use_sensitivity":          {"type": "boolean", "default": False}
        },
        "required": ["project_path", "stimulation_port", "steady_state_limit", "norming_impedance"]
    },
},

"infer-run-dir": {
    "category": "project_identity",
    "risk": "read",
    "description": "Infer run_dir from a projects/working.cst project path.",
    "handler": "tool_infer_run_dir",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"inspect-project": {
    "category": "project_ops",
    "risk": "read",
    "description": "Open a CST project, list all parameters and entities, then close. Returns parameter names/values and entity names.",
    "handler": "tool_inspect_project",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"is-simulation-running": {
    "category": "project_ops",
    "risk": "read",
    "description": "Check whether the CST solver is currently running for the verified working project.",
    "handler": "tool_is_simulation_running",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"list-open-projects": {
    "category": "project_identity",
    "risk": "read",
    "description": "List CST projects visible through DesignEnvironment.connect_to_any().",
    "handler": "tool_list_open_projects",
    "json_schema": {
        "type": "object",
        "properties": {},
        "required": []
    },
},

"list-parameters": {
    "category": "project_ops",
    "risk": "read",
    "description": "List parameters from the verified CST working project.",
    "handler": "tool_list_parameters",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"pause-simulation": {
    "category": "project_ops",
    "risk": "session",
    "description": "Pause the currently running CST solver.",
    "handler": "tool_pause_simulation",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"prepare-experiment": {
    "category": "project_ops",
    "risk": "write",
    "description": "Open a CST project, change one or more parameters, confirm, then save and close. Supports batch via names+values arrays. Use before run-experiment.",
    "handler": "tool_prepare_experiment",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "param_name": {
                "type": "string",
                "examples": [
                    "g"
                ]
            },
            "param_value": {
                "type": "number",
                "examples": [
                    23.5
                ]
            },
            "names": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "examples": [
                    [
                        "R",
                        "g"
                    ]
                ]
            },
            "values": {
                "type": "array",
                "items": {
                    "type": "number"
                },
                "examples": [
                    [
                        0.16,
                        23.0
                    ]
                ]
            }
        },
        "required": [
            "project_path",
            "param_name",
            "param_value",
            "names",
            "values"
        ]
    },
},

"resume-simulation": {
    "category": "project_ops",
    "risk": "write",
    "description": "Resume a paused CST solver.",
    "handler": "tool_resume_simulation",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"set-fdsolver-extrude-open-bc": {
    "category": "project_ops",
    "risk": "write",
    "description": "Enable or disable FD solver extruded open boundary.",
    "handler": "tool_set_fdsolver_extrude_open_bc",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"define-fdsolver-stimulation": {
    "category": "project_ops",
    "risk": "write",
    "description": (
        "依据本机 CST 2022 手册先执行 FDSolver.Reset（会重置此前的频域求解器"
        "设置），再设置激励。当前仅完成离线命令生成和参数校验，尚未经过本轮 "
        "CST 实机验收。"
    ),
    "handler": "tool_define_fdsolver_stimulation",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "port": {
                "description": "正整数端口号或 CST 2022 手册允许的激励枚举。",
                "type": ["integer", "string"],
                "anyOf": [
                    {"type": "integer", "minimum": 1},
                    {
                        "type": "string",
                        "enum": ["All", "All+Floquet", "Plane Wave", "List", "CMA"]
                    }
                ],
                "examples": [1]
            },
            "mode": {
                "description": "正整数模式号或 CST 2022 手册允许的激励枚举。",
                "type": ["integer", "string"],
                "anyOf": [
                    {"type": "integer", "minimum": 1},
                    {
                        "type": "string",
                        "enum": ["All", "All+Floquet", "List", "CMA"]
                    }
                ],
                "examples": [1]
            }
        },
        "required": ["project_path", "port", "mode"]
    },
},

"set-mesh-fpbavoid-nonreg-unite": {
    "category": "project_ops",
    "risk": "write",
    "description": "Enable or disable mesh FPBA non-regular unite avoidance.",
    "handler": "tool_set_mesh_fpbavoid_nonreg_unite",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"set-mesh-minimum-step-number": {
    "category": "project_ops",
    "risk": "write",
    "description": "Set the minimum mesh step number.",
    "handler": "tool_set_mesh_minimum_step_number",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "num_steps": {
                "type": "integer",
                "examples": [
                    5
                ]
            }
        },
        "required": [
            "project_path",
            "num_steps"
        ]
    },
},

"set-solver-acceleration": {
    "category": "project_ops",
    "risk": "write",
    "description": "Configure solver parallelization and hardware acceleration.",
    "handler": "tool_set_solver_acceleration",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "use_parallelization": {
                "type": "boolean",
                "examples": [
                    True
                ]
            },
            "max_threads": {
                "type": "integer",
                "examples": [
                    1024
                ]
            }
        },
        "required": [
            "project_path",
            "use_parallelization",
            "max_threads"
        ]
    },
},

"start-simulation-async": {
    "category": "project_ops",
    "risk": "long-running",
    "description": "异步启动 CST 求解器；返回成功只表示启动调用完成，不代表求解成功。",
    "handler": "tool_start_simulation_async",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"stop-simulation": {
    "category": "project_ops",
    "risk": "session",
    "description": "Stop the currently running CST solver.",
    "handler": "tool_stop_simulation",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"verify-project-identity": {
    "category": "project_identity",
    "risk": "read",
    "description": "Verify the expected project is the sole open CST project before writes.",
    "handler": "tool_verify_project_identity",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"wait-project-unlocked": {
    "category": "project_identity",
    "risk": "read",
    "description": "Wait for a project companion directory to have no .lok files.",
    "handler": "tool_wait_project_unlocked",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "timeout_seconds": {
                "type": "number",
                "examples": [
                    30
                ]
            },
            "poll_interval_seconds": {
                "type": "number",
                "examples": [
                    0.5
                ]
            }
        },
        "required": [
            "project_path",
            "timeout_seconds",
            "poll_interval_seconds"
        ]
    },
},

"wait-simulation": {
    "category": "project_ops",
    "risk": "long-running",
    "description": "轮询直到求解器不再运行或超时；running=false 只表示停止，不能证明求解成功。",
    "handler": "tool_wait_simulation",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "timeout_seconds": {
                "type": "number",
                "examples": [
                    3600
                ]
            },
            "poll_interval_seconds": {
                "type": "number",
                "examples": [
                    10
                ]
            }
        },
        "required": [
            "project_path",
            "timeout_seconds",
            "poll_interval_seconds"
        ]
    },
},

"capture-3d-view": {
    "category": "project_ops",
    "risk": "filesystem-write",
    "description": "Export the current 3D sheet to PNG. Use a CST reserved view or relative horizontal/vertical rotations from Front.",
    "handler": "tool_capture_3d_view",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "CST project file path (must point to specific .cst file)",
                "examples": ["C:/path/to/tasks/task_xxx/runs/run_001/projects/working.cst"]
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory for screenshots (default: <project_dir>/exports/screenshots/)",
                "examples": ["C:/path/to/exports/screenshots/"]
            },
            "filename_prefix": {
                "type": "string",
                "description": "Filename prefix for output files",
                "default": "view",
                "examples": ["model_snapshot", "antenna_v1"]
            },
            "view_type": {
                "type": "string",
                "description": "preset uses a reserved view; custom rotates from Front",
                "enum": ["custom", "preset"],
                "default": "preset"
            },
            "preset_name": {
                "type": "string",
                "description": "CST reserved view used by preset",
                "enum": ["Front", "Back", "Top", "Bottom", "Left", "Right", "Perspective"],
                "default": "Perspective"
            },
            "horizontal_rotation_deg": {
                "type": "number",
                "description": "Custom rotation from Front; positive is left, negative is right",
                "default": 45.0,
                "examples": [45]
            },
            "vertical_rotation_deg": {
                "type": "number",
                "description": "Custom rotation after horizontal rotation; positive is up, negative is down",
                "default": 30.0,
                "examples": [30]
            },
            "return_image_data": {
                "type": "boolean",
                "description": "If true, include base64-encoded PNG data in response for agent analysis",
                "default": False
            }
        },
        "required": ["project_path"]
    },
},

"inspect-model-view": {
    "category": "project_ops",
    "risk": "filesystem-write",
    "description": "Export a documented preset or Front-relative 3D view and return the PNG as base64.",
    "handler": "tool_inspect_model_view",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "CST project file path",
                "examples": ["C:/path/to/tasks/task_xxx/runs/run_001/projects/working.cst"]
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory (optional)",
                "examples": ["C:/path/to/exports/"]
            },
            "filename_prefix": {
                "type": "string",
                "default": "inspect",
                "examples": ["model_check"]
            },
            "view_type": {
                "type": "string",
                "description": "preset uses a reserved view; custom rotates from Front",
                "enum": ["custom", "preset"],
                "default": "preset"
            },
            "preset_name": {
                "type": "string",
                "description": "CST reserved view used by preset",
                "enum": ["Front", "Back", "Top", "Bottom", "Left", "Right", "Perspective"],
                "default": "Perspective"
            },
            "horizontal_rotation_deg": {
                "type": "number",
                "description": "Custom rotation from Front; positive is left, negative is right",
                "default": 45.0
            },
            "vertical_rotation_deg": {
                "type": "number",
                "description": "Custom rotation after horizontal rotation; positive is up, negative is down",
                "default": 30.0
            }
        },
        "required": ["project_path"]
    },
},
}


# --- Handlers ---

from ..lib import project as _po
from ..lib import simulation as _sim
from ..lib import modeling as _md
from ..lib import identity as _pi
from ._arguments import project_path_from_args
from pathlib import Path
import time


def _lazy_pipeline(name: str):
    """Lazy-import a pipeline function to break circular dependency."""
    import importlib
    mod = importlib.import_module("..cli.pipelines.impl", __package__)
    return getattr(mod, name)


def tool_inspect_project(args: dict) -> dict:
    _inspect = _lazy_pipeline("pipeline_inspect_project")
    return _inspect(
        project_path=str(args.get("project_path", "")),
    )


def tool_prepare_experiment(args: dict) -> dict:
    _prepare = _lazy_pipeline("pipeline_prepare_experiment")
    names = args.get("names") or args.get("param_names")
    values = args.get("values") or args.get("param_values")
    if isinstance(names, list) and isinstance(values, list):
        return _prepare(project_path=str(args.get("project_path", "")), names=names, values=values)
    return _prepare(
        project_path=str(args.get("project_path", "")),
        param_name=str(args.get("param_name", "")),
        param_value=float(args.get("param_value", 0)),
    )


def tool_list_materials(args: dict) -> dict:
    materials_path = Path(__file__).resolve().parents[3] / "references" / "materials_name_list.txt"
    if not materials_path.is_file():
        return {
            "status": "error",
            "error_type": "materials_list_not_found",
            "expected_path": str(materials_path),
        }
    names = [line.strip() for line in materials_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {
        "status": "success",
        "count": len(names),
        "material_names": names,
        "source": str(materials_path),
        "usage": "Pass the name to change-material --material '<name>', or use define-material-from-mtd --material-name '<name>'.",
    }


def tool_list_parameters(args: dict) -> dict:
    return _po.list_parameters(project_path_from_args(args))


def tool_list_entities(args: dict) -> dict:
    return _po.list_entities(
        project_path=project_path_from_args(args),
        component=str(args.get("component", "")),
    )


def tool_change_parameter(args: dict) -> dict:
    project_path = project_path_from_args(args)
    tool_args = {key: value for key, value in args.items() if key not in {"project_path", "fullpath", "working_project"}}
    return _po.change_parameter(project_path=project_path, **tool_args)


def tool_define_parameters(args: dict) -> dict:
    return _po.define_parameters(
        project_path=project_path_from_args(args),
        names=args.get("names", []),
        values=args.get("values", []),
    )


def tool_start_simulation(args: dict) -> dict:
    return _sim.start_simulation(project_path_from_args(args))


def tool_start_simulation_async(args: dict) -> dict:
    return _sim.start_simulation_async(project_path_from_args(args))


def tool_is_simulation_running(args: dict) -> dict:
    return _sim.is_simulation_running(project_path_from_args(args))


def tool_wait_simulation(args: dict) -> dict:
    project_path = project_path_from_args(args)
    timeout_seconds = float(args.get("timeout_seconds", 3600.0))
    poll_interval_seconds = float(args.get("poll_interval_seconds", 10.0))
    started = time.monotonic()
    polls = 0
    last_result = None
    while True:
        polls += 1
        last_result = _sim.is_simulation_running(project_path)
        if last_result.get("status") == "error":
            return {**last_result, "polls": polls, "waited_seconds": round(time.monotonic() - started, 3)}
        if not bool(last_result.get("running")):
            return {
                "status": "success",
                "project_path": last_result.get("project_path", project_path),
                "running": False,
                "polls": polls,
                "waited_seconds": round(time.monotonic() - started, 3),
                "runtime_module": "cst_runtime._tools.project_ops",
            }
        if time.monotonic() - started >= timeout_seconds:
            return {
                "status": "error",
                "error_type": "simulation_wait_timeout",
                "message": "simulation still running after timeout",
                "project_path": project_path,
                "running": True,
                "polls": polls,
                "timeout_seconds": timeout_seconds,
                "last_result": last_result,
                "runtime_module": "cst_runtime._tools.project_ops",
            }
        time.sleep(poll_interval_seconds)


def tool_stop_simulation(args: dict) -> dict:
    return _sim.stop_simulation(project_path_from_args(args))


def tool_pause_simulation(args: dict) -> dict:
    return _sim.pause_simulation(project_path_from_args(args))


def tool_resume_simulation(args: dict) -> dict:
    return _sim.resume_simulation(project_path_from_args(args))


def tool_set_solver_acceleration(args: dict) -> dict:
    return _sim.set_solver_acceleration(**args)


def tool_set_fdsolver_extrude_open_bc(args: dict) -> dict:
    return _sim.set_fdsolver_extrude_open_bc(**args)


def tool_define_fdsolver_stimulation(args: dict) -> dict:
    return _sim.define_fdsolver_stimulation(**args)


def tool_set_mesh_fpbavoid_nonreg_unite(args: dict) -> dict:
    return _sim.set_mesh_fpbavoid_nonreg_unite(**args)


def tool_set_mesh_minimum_step_number(args: dict) -> dict:
    return _sim.set_mesh_minimum_step_number(**args)


def tool_list_open_projects(args: dict) -> dict:
    return _pi.list_open_projects()


def tool_verify_project_identity(args: dict) -> dict:
    return _pi.verify_project_identity(project_path_from_args(args))


def tool_infer_run_dir(args: dict) -> dict:
    project_path = project_path_from_args(args)
    run_dir = _pi.infer_run_dir_from_project(project_path)
    return {
        "status": "success",
        "project_path": str(project_path),
        "run_dir": run_dir.as_posix() if run_dir else None,
        "runtime_module": "cst_runtime._tools.project_ops",
    }


def tool_wait_project_unlocked(args: dict) -> dict:
    project_path = project_path_from_args(args)
    return _pi.wait_project_unlocked(
        project_path=project_path,
        timeout_seconds=float(args.get("timeout_seconds", 10.0)),
        poll_interval_seconds=float(args.get("poll_interval_seconds", 0.5)),
    )


def tool_define_frequency_range(args: dict) -> dict:
    return _md.define_frequency_range(**args)


def tool_change_solver_type(args: dict) -> dict:
    return _md.change_solver_type(**args)


def tool_define_background(args: dict) -> dict:
    return _md.define_background(**args)


def tool_define_boundary(args: dict) -> dict:
    return _md.define_boundary(**args)


def tool_define_mesh(args: dict) -> dict:
    return _md.define_mesh(**args)


def tool_define_solver(args: dict) -> dict:
    return _md.define_solver(**args)


def tool_define_port(args: dict) -> dict:
    return _md.define_port(**args)


def tool_define_monitor(args: dict) -> dict:
    return _md.define_monitor(**args)


def tool_capture_3d_view(args: dict) -> dict:
    """Handler for capture-3d-view tool."""
    return _md.capture_3d_view(
        project_path=args.get("project_path", ""),
        output_dir=args.get("output_dir", ""),
        filename_prefix=args.get("filename_prefix", "view"),
        view_type=args.get("view_type", "preset"),
        preset_name=args.get("preset_name", "Perspective"),
        horizontal_rotation_deg=args.get("horizontal_rotation_deg"),
        vertical_rotation_deg=args.get("vertical_rotation_deg"),
        return_image_data=args.get("return_image_data", False),
    )


def tool_inspect_model_view(args: dict) -> dict:
    """Handler for inspect-model-view tool - capture and return image for agent analysis."""
    # Always return image data for this tool
    return _md.capture_3d_view(
        project_path=args.get("project_path", ""),
        output_dir=args.get("output_dir", ""),
        filename_prefix=args.get("filename_prefix", "inspect"),
        view_type=args.get("view_type", "preset"),
        preset_name=args.get("preset_name", "Perspective"),
        horizontal_rotation_deg=args.get("horizontal_rotation_deg"),
        vertical_rotation_deg=args.get("vertical_rotation_deg"),
        return_image_data=True,  # Always include base64 image data
    )


_register_tool_defs(TOOL_DEFS)
