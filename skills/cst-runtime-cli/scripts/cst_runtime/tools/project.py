"""project_ops.py — project_ops + project_identity 工具定义"""
from . import _register_tool_defs
from ..lib.modeling import CST_2022_SOLVER_TYPES


TOOL_DEFS = {
"change-parameter": {
    "category": "project_ops",
    "risk": "write",
    "description": (
        "Use this to change one known CST parameter to a numeric value or an expression that "
        "evaluates to a number. Use define-parameters for a batch definition and "
        "prepare-experiment when the parameter change must be saved and the project closed."
    ),
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
    "description": (
        "Use this to explicitly select the current CST solver before calling solver-specific "
        "configuration tools. It does not configure solver settings, boundaries, ports, sources, "
        "or monitors; do not mix time-domain and frequency-domain configuration afterward."
    ),
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
    "description": (
        "Use this to set the calculation-domain background as Normal or PEC, with explicit "
        "relative epsilon and mu for Normal; 1.0/1.0 is Vacuum and farfield-compatible. CST 2022 "
        "has no Background getter, so returned and later get-background values are Runtime-tracked."
    ),
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
                "enum": ["Normal", "PEC"],
                "default": "Normal",
                "description": "Background type: Normal dielectric/magnetic medium or perfect electric conductor (PEC).",
                "examples": ["Normal", "PEC"]
            },
            "epsilon": {
                "type": "number",
                "default": 1.0,
                "description": "Relative permittivity of a Normal background; farfield monitors require 1.0 (Vacuum).",
                "examples": [1.0]
            },
            "mu": {
                "type": "number",
                "default": 1.0,
                "description": "Relative permeability of a Normal background; farfield monitors require 1.0 (Vacuum).",
                "examples": [1.0]
            }
        },
        "required": ["project_path"]
    },
},

"get-background": {
    "category": "project_ops",
    "risk": "read",
    "description": (
        "Use this only when the Runtime-tracked background request is needed for planning or "
        "diagnosis. It cannot read GUI changes because CST 2022 exposes no Background getter; "
        "background_state_unknown means define-background has not tracked a value in this session."
    ),
    "handler": "tool_get_background",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": ["C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"]
            }
        },
        "required": ["project_path"]
    },
},

"define-boundary": {
    "category": "project_ops",
    "risk": "write",
    "description": (
        "Use this to set ordinary six-face calculation-domain boundary types and symmetry before "
        "simulation. It is not a complete periodic Unit Cell or Floquet setup; use "
        "define-unit-cell-boundary with define-floquet-port for an infinite periodic unit cell."
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
    "description": (
        "Use this to set the simulation start and end frequencies after the project frequency "
        "unit and solver choice are known. It does not configure the solver's sweep or adaptive "
        "settings."
    ),
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
    "description": (
        "Use this to set the hexahedral mesh steps per wavelength and per box for a compatible "
        "solver and mesh method. It does not select the solver or frequency-domain mesh method."
    ),
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

"define-parameters": {
    "category": "project_ops",
    "risk": "write",
    "description": (
        "Use this to create or overwrite multiple CST parameters in one StoreParameters call "
        "when names and values are already user-defined and aligned. Use change-parameter for "
        "one existing parameter."
    ),
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
        "Use this to define an internal axis-aligned waveguide port from explicit global X/Y/Z "
        "ranges. Collapse the normal-axis range to the port plane; *min orientations radiate "
        "toward +axis and *max orientations radiate toward -axis."
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
    "description": (
        "Use this to configure Solver Object settings only when the current solver is HF Time "
        "Domain. It does not switch solver type or configure the frequency-domain FDSolver."
    ),
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
    "description": (
        "Use this to derive the Runtime run directory from a project path that follows the "
        "runs/<run_id>/projects/working.cst layout. It does not open CST or validate simulation "
        "results."
    ),
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
    "description": (
        "Use this on demand to open one CST project, list its parameters and geometry entities, "
        "and close it. It is a broad inspection tool, not a mandatory pre-check before ordinary "
        "modeling or configuration calls."
    ),
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
    "description": (
        "Use this to read whether the solver is currently running for the verified working "
        "project, typically after an asynchronous start. running=false means only that the "
        "solver is stopped, not that it completed successfully."
    ),
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
    "description": (
        "Use this to list CST projects visible to DesignEnvironment when project identity or "
        "session ownership is unclear. Use cst-session-inspect for the broader process, lock, "
        "and reattach-readiness view."
    ),
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
    "description": (
        "Use this to obtain exact CST parameter names and current values when they are unknown "
        "before change-parameter, define-parameters, or an experiment. It is not a routine "
        "verification call after a successful parameter write."
    ),
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
    "description": (
        "Use this only to pause a solver that is currently running. Continue it with "
        "resume-simulation or terminate it with stop-simulation; do not call start-simulation "
        "again as a substitute for resume."
    ),
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
    "description": (
        "Use this to apply one or more already selected parameter values, then save and close the "
        "project before run-experiment. It does not run the solver; names and values must remain "
        "aligned for a batch update."
    ),
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
    "description": (
        "Use this only to resume a solver that was paused with pause-simulation. It is not a "
        "general simulation start tool and must not be used when no paused solve exists."
    ),
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
    "description": (
        "Use this to enable or disable FDSolver.ExtrudeOpenBC only when the current solver is HF "
        "Frequency Domain and open boundaries are configured. It does not switch solver type or "
        "replace define-boundary."
    ),
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
        "Use this to set FDSolver.Stimulation for an existing port or Floquet mode only when the "
        "current solver is HF Frequency Domain. It neither switches solver type nor calls "
        "FDSolver.Reset, and it does not create the referenced excitation."
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
                "description": "Positive port number or an excitation selector documented by CST 2022.",
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
                "description": "Positive mode number or an excitation selector documented by CST 2022.",
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
    "description": (
        "Use this to enable or disable FPBA non-regular-unite avoidance only for a compatible "
        "solver and mesh method when the user explicitly needs that option. It is not a general "
        "mesh configuration tool."
    ),
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
    "description": (
        "Use this to set the minimum mesh-step count for a compatible solver and mesh method "
        "after the main mesh settings are known. It does not define the global hexahedral mesh "
        "parameters."
    ),
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
    "description": (
        "Use this to configure Solver Object parallelization, thread count, MPI, or hardware "
        "acceleration only when the current solver is HF Time Domain. It is not a cross-solver "
        "resource configuration tool."
    ),
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

"start-simulation": {
    "category": "project_ops",
    "risk": "long-running",
    "description": (
        "Use this to run the explicitly selected and fully configured CST solver synchronously "
        "until run_solver returns. It reports success only for run_solver=True; unlike "
        "run-experiment, it does not require or validate new result-node data."
    ),
    "handler": "tool_start_simulation",
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

"start-simulation-async": {
    "category": "project_ops",
    "risk": "long-running",
    "description": (
        "Use this to start an explicitly selected and fully configured CST solver asynchronously "
        "when the caller must return immediately. A successful response means only that the start "
        "call completed; use wait-simulation and result or log evidence for completion."
    ),
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
    "description": (
        "Use this only to stop a solver that is currently running or paused. Follow with "
        "wait-simulation when the caller must know that execution has stopped; stopping does not "
        "mean the solve succeeded."
    ),
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
    "description": (
        "Use this safety check when CST project identity or session ownership is ambiguous before "
        "a write. It verifies that the expected project is the sole open project; it is not a "
        "routine pre- or post-check for every successful CST operation."
    ),
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
    "description": (
        "Use this when a file-level operation requires the CST project companion directory to be "
        "unlocked, such as after closing before copying. It waits for .lok files to disappear and "
        "does not verify modeling or solver success."
    ),
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
    "description": (
        "Use this after start-simulation-async to poll until the solver stops or the timeout "
        "expires. running=false proves only that execution stopped; use logs or required result "
        "nodes to determine whether the solve succeeded."
    ),
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
                "default": 3600,
                "examples": [
                    3600
                ]
            },
            "poll_interval_seconds": {
                "type": "number",
                "default": 10,
                "examples": [
                    10
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"capture-3d-view": {
    "category": "project_ops",
    "risk": "filesystem-write",
    "description": (
        "Use this to save the current 3D model sheet as PNG from a documented CST preset or a "
        "Front-relative custom rotation. Use inspect-model-view when the Agent needs the PNG "
        "returned as base64 for visual inspection."
    ),
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
    "description": (
        "Use this when the Agent must visually inspect a documented preset or Front-relative 3D "
        "model view; it writes a PNG and returns its base64 data. Use capture-3d-view when only a "
        "saved screenshot is needed."
    ),
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
from ..lib import solver as _sv
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
    started_wall = time.time()
    # 轮询间隔下限钳制，避免 poll_interval_seconds=0 时 CPU 空转自旋
    effective_poll = max(float(poll_interval_seconds), 0.1)
    # 优先使用 start-simulation-async 落盘的启动时基线，避免求解器在
    # start 与 wait 两次调用之间报错退出时漏检；无 marker 再回退现取基线。
    baseline_result = _sv.load_log_baseline(project_path)
    log_baseline = (
        dict(baseline_result.get("baseline", {}))
        if baseline_result.get("status") == "success"
        else {}
    )
    if not log_baseline:
        fallback = _sv.capture_log_baseline(project_path)
        log_baseline = (
            dict(fallback.get("baseline", {}))
            if fallback.get("status") == "success"
            else {}
        )
    polls = 0
    last_result = None
    while True:
        polls += 1
        last_result = _sim.is_simulation_running(project_path)
        if last_result.get("status") == "error":
            return {**last_result, "polls": polls, "waited_seconds": round(time.monotonic() - started, 3)}
        if not bool(last_result.get("running")):
            diagnostics = _sv.read_solver_errors(
                project_path,
                baseline=log_baseline,
                since=started_wall,
            )
            errors = (
                list(diagnostics.get("errors", []))
                if diagnostics.get("status") == "success"
                else []
            )
            if errors:
                return {
                    "status": "error",
                    "error_type": "solver_stopped_with_error",
                    "message": "求解器已停止并报告错误",
                    "project_path": last_result.get("project_path", project_path),
                    "running": False,
                    "cst_errors": errors,
                    "cst_error_lines": diagnostics.get("error_lines", []),
                    "log_files": diagnostics.get("log_files", []),
                    "polls": polls,
                    "waited_seconds": round(time.monotonic() - started, 3),
                    "runtime_module": "cst_runtime._tools.project_ops",
                }
            return {
                "status": "success",
                "project_path": last_result.get("project_path", project_path),
                "running": False,
                "solver_completed": "unknown",
                "cst_errors": [],
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
        time.sleep(effective_poll)


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


def tool_get_background(args: dict) -> dict:
    return _md.get_background(project_path_from_args(args))


def tool_define_boundary(args: dict) -> dict:
    return _md.define_boundary(**args)


def tool_define_mesh(args: dict) -> dict:
    return _md.define_mesh(**args)


def tool_define_solver(args: dict) -> dict:
    return _md.define_solver(**args)


def tool_define_port(args: dict) -> dict:
    return _md.define_port(**args)


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
