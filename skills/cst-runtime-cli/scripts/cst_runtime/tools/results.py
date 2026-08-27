"""results.py — results 工具定义"""
from . import _register_tool_defs


TOOL_DEFS = {
"list-sparameter-results": {
    "category": "results",
    "risk": "read",
    "description": (
        "Use this after saved results exist to enumerate exact regular-port and Floquet "
        "S-parameter ResultTree paths with available Run IDs. It discovers nodes only; "
        "use export-sparameter or get-1d-result to read data, and an open project yields "
        "its latest saved disk state."
    ),
    "handler": "tool_list_sparameter_results",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "minLength": 1
            }
        },
        "required": ["project_path"],
        "additionalProperties": False
    },
},

"export-sparameter": {
    "category": "results",
    "risk": "filesystem-write",
    "description": (
        "Use this to export one saved S-parameter curve to JSON by exact result_path or "
        "explicit response/excitation port and optional mode identifiers. It writes one "
        "channel, not a full network matrix; use list-sparameter-results only when the "
        "node or Run ID is unknown."
    ),
    "handler": "tool_export_sparameter",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string", "minLength": 1},
            "run_id": {"type": "integer", "minimum": 0},
            "output_path": {"type": "string", "minLength": 1},
            "result_path": {"type": "string", "default": ""},
            "response_port": {"type": "string", "default": ""},
            "excitation_port": {"type": "string", "default": ""},
            "response_mode": {"type": ["integer", "null"], "minimum": 1, "default": None},
            "excitation_mode": {"type": ["integer", "null"], "minimum": 1, "default": None}
        },
        "required": ["project_path", "run_id", "output_path"],
        "additionalProperties": False
    },
},

"export-touchstone": {
    "category": "results",
    "risk": "filesystem-write",
    "description": (
        "Use this to export the complete saved S-, Y-, or Z-parameter network matrix "
        "through the CST 2022 TOUCHSTONE object. Unlike export-sparameter, it writes the "
        "full network; read the generated header for the actual port and mode order."
    ),
    "handler": "tool_export_touchstone",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string", "minLength": 1},
            "output_base_path": {"type": "string", "minLength": 1},
            "parameter_type": {"type": "string", "enum": ["S", "Y", "Z"], "default": "S"},
            "data_format": {"type": "string", "enum": ["MA", "DB", "RI"], "default": "MA"},
            "frequency_range": {"type": "string", "enum": ["Full", "Limited"], "default": "Full"},
            "fmin": {"type": ["number", "null"], "default": None},
            "fmax": {"type": ["number", "null"], "default": None},
            "impedance": {"type": "number", "exclusiveMinimum": 0, "default": 50.0},
            "renormalize": {"type": "boolean", "default": True},
            "sample_count": {"type": "integer", "minimum": 0, "default": 0},
            "use_ar_results": {"type": "boolean", "default": False}
        },
        "required": ["project_path", "output_base_path"],
        "additionalProperties": False
    },
},

"generate-report": {
    "category": "results",
    "risk": "filesystem-write",
    "description": (
        "Use this to build a modular HTML report from already exported S-parameter, "
        "farfield, and audit files. It does not run CST or discover and export ResultTree data."
    ),
    "handler": "tool_generate_report",
    "json_schema": {
        "type": "object",
        "properties": {
            "data_dir": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001"
                ]
            },
            "output_html": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\exports\\report.html"
                ]
            },
            "page_title": {
                "type": "string",
                "examples": [
                    "Electromagnetic Simulation Report"
                ]
            },
            "modules": {
                "type": "string",
                "examples": [
                    "s11,farfield3d,timeline"
                ]
            },
            "split": {
                "type": "boolean",
                "examples": [
                    False
                ]
            }
        },
        "required": [
            "data_dir",
            "output_html",
            "page_title",
            "modules",
            "split"
        ]
    },
},

"get-1d-result": {
    "category": "results",
    "risk": "filesystem-write",
    "description": (
        "Use this to read one exact saved 0D or 1D ResultTree path through cst.results and "
        "serialize its data to JSON. Unlike export-sparameter, it is generic; use "
        "list-result-items or a specialized list tool only when the path is unknown."
    ),
    "handler": "tool_get_1d_result",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "treepath": {
                "type": "string",
                "examples": [
                    "1D Results\\S-Parameters\\S1,1"
                ]
            },
            "module_type": {
                "type": "string",
                "examples": [
                    "3d"
                ]
            },
            "run_id": {
                "type": "integer",
                "description": (
                    "Run ID 0 selects the latest result by default and may also be the only "
                    "actual Run ID for a nonparametric simulation."
                ),
                "examples": [
                    1
                ]
            },
            "load_impedances": {
                "type": "boolean",
                "examples": [
                    True
                ]
            },
            "export_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\exports\\s11_run1.json"
                ]
            },
            "allow_interactive": {
                "type": "boolean",
                "description": "If true, CST returns only the last saved project state",
                "examples": [
                    False
                ]
            }
        },
        "required": [
            "project_path",
            "treepath",
            "module_type",
            "run_id",
            "load_impedances",
            "export_path",
            "allow_interactive"
        ]
    },
},

"get-2d-result": {
    "category": "results",
    "risk": "filesystem-write",
    "description": (
        "Use this only when the installed cst.results API exposes get_result2d_item to "
        "serialize a 2D result to JSON. CST 2022 does not document that method; otherwise "
        "use a supported field-export tool rather than approximating."
    ),
    "handler": "tool_get_2d_result",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "treepath": {
                "type": "string",
                "examples": [
                    "2D/3D Results\\example"
                ]
            },
            "module_type": {
                "type": "string",
                "examples": [
                    "3d"
                ]
            },
            "export_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\exports\\result_2d.json"
                ]
            },
            "allow_interactive": {
                "type": "boolean",
                "examples": [
                    False
                ]
            },
            "subproject_treepath": {
                "type": "string",
                "examples": [
                    ""
                ]
            },
            "include_data": {
                "type": "boolean",
                "examples": [
                    False
                ]
            }
        },
        "required": [
            "project_path",
            "treepath",
            "module_type",
            "export_path",
            "allow_interactive",
            "subproject_treepath",
            "include_data"
        ]
    },
},

"get-parameter-combination": {
    "category": "results",
    "risk": "read",
    "description": (
        "Use this to read the CST parameter combination associated with one known result "
        "Run ID. It does not read result values or validate solver completion."
    ),
    "handler": "tool_get_parameter_combination",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "run_id": {
                "type": "integer",
                "description": (
                    "Run ID 0 returns the latest parameter combination and may also be the "
                    "only actual Run ID for a nonparametric simulation."
                ),
                "examples": [
                    1
                ]
            },
            "module_type": {
                "type": "string",
                "examples": [
                    "3d"
                ]
            },
            "allow_interactive": {
                "type": "boolean",
                "examples": [
                    False
                ]
            }
        },
        "required": [
            "project_path",
            "run_id",
            "module_type",
            "allow_interactive"
        ]
    },
},

"get-version-info": {
    "category": "results",
    "risk": "read",
    "description": (
        "Use this only to inspect the installed cst.results version when diagnosing "
        "compatibility. It does not inspect a project or its results."
    ),
    "handler": "tool_get_version_info",
    "json_schema": {
        "type": "object",
        "properties": {},
        "required": []
    },
},

"list-result-items": {
    "category": "results",
    "risk": "read",
    "description": (
        "Use this to discover saved ResultTree item paths, optionally filtered by module, "
        "result type, or subproject. It lists nodes only; use get-1d-result, get-2d-result, "
        "or an export tool for data."
    ),
    "handler": "tool_list_result_items",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "module_type": {
                "type": "string",
                "examples": [
                    "3d"
                ]
            },
            "filter_type": {
                "type": "string",
                "examples": [
                    "0D/1D"
                ]
            },
            "allow_interactive": {
                "type": "boolean",
                "examples": [
                    False
                ]
            },
            "subproject_treepath": {
                "type": "string",
                "examples": [
                    ""
                ]
            }
        },
        "required": [
            "project_path",
            "module_type",
            "filter_type",
            "allow_interactive",
            "subproject_treepath"
        ]
    },
},

"list-run-ids": {
    "category": "results",
    "risk": "read",
    "description": (
        "Use this to list available Run IDs for one exact saved ResultTree path, with "
        "optional nonparametric or mesh-pass filtering. It does not read the result data."
    ),
    "handler": "tool_list_run_ids",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "treepath": {
                "type": "string",
                "examples": [
                    "1D Results\\S-Parameters\\S1,1"
                ]
            },
            "module_type": {
                "type": "string",
                "examples": [
                    "3d"
                ]
            },
            "allow_interactive": {
                "type": "boolean",
                "examples": [
                    False
                ]
            },
            "skip_nonparametric": {
                "type": "boolean",
                "examples": [
                    False
                ]
            },
            "max_mesh_passes_only": {
                "type": "boolean",
                "examples": [
                    False
                ]
            }
        },
        "required": [
            "project_path",
            "treepath",
            "module_type",
            "allow_interactive",
            "skip_nonparametric",
            "max_mesh_passes_only"
        ]
    },
},

"list-subprojects": {
    "category": "results",
    "risk": "read",
    "description": (
        "Use this to list result subprojects from one explicit CST project path before "
        "subproject-scoped discovery. It does not list result items or data."
    ),
    "handler": "tool_list_subprojects",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "allow_interactive": {
                "type": "boolean",
                "examples": [
                    False
                ]
            }
        },
        "required": [
            "project_path",
            "allow_interactive"
        ]
    },
},

"open-results-project": {
    "category": "results",
    "risk": "read",
    "description": (
        "Use this only to verify that cst.results can open an explicit project or "
        "subproject path. It does not enumerate nodes, Run IDs, or data and is not a "
        "routine pre-check."
    ),
    "handler": "tool_open_results_project",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "allow_interactive": {
                "type": "boolean",
                "examples": [
                    False
                ]
            },
            "subproject_treepath": {
                "type": "string",
                "examples": [
                    ""
                ]
            }
        },
        "required": [
            "project_path",
            "allow_interactive",
            "subproject_treepath"
        ]
    },
},

"plot-exported-file": {
    "category": "results",
    "risk": "filesystem-write",
    "description": (
        "Use this to render an already exported JSON result or CST farfield ASCII/TXT "
        "file into an HTML preview. It does not read CST ResultTree data or perform a new export."
    ),
    "handler": "tool_plot_exported_file",
    "json_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\exports\\s11_run1.json"
                ]
            },
            "output_html": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\exports\\result_preview.html"
                ]
            },
            "page_title": {
                "type": "string",
                "examples": [
                    "CST Result Preview"
                ]
            }
        },
        "required": [
            "file_path",
            "output_html",
            "page_title"
        ]
    },
},
}


# --- Handlers ---

from ..lib import results as _res
from ._arguments import project_path_from_args, run_id_from_args


def tool_open_results_project(args: dict) -> dict:
    return _res.open_project(
        project_path=project_path_from_args(args),
        allow_interactive=bool(args.get("allow_interactive", False)),
        subproject_treepath=str(args.get("subproject_treepath", "")),
    )


def tool_list_subprojects(args: dict) -> dict:
    return _res.list_subprojects(
        project_path=project_path_from_args(args),
        allow_interactive=bool(args.get("allow_interactive", False)),
    )


def tool_get_version_info(args: dict) -> dict:
    return _res.get_version_info()


def tool_list_result_items(args: dict) -> dict:
    return _res.list_result_items(
        project_path=project_path_from_args(args),
        module_type=str(args.get("module_type", "3d")),
        filter_type=str(args.get("filter_type", "0D/1D")),
        allow_interactive=bool(args.get("allow_interactive", False)),
        subproject_treepath=str(args.get("subproject_treepath", "")),
    )


def tool_list_run_ids(args: dict) -> dict:
    return _res.list_run_ids(
        project_path=project_path_from_args(args),
        treepath=str(args.get("treepath", "")),
        module_type=str(args.get("module_type", "3d")),
        allow_interactive=bool(args.get("allow_interactive", False)),
        subproject_treepath=str(args.get("subproject_treepath", "")),
        skip_nonparametric=bool(args.get("skip_nonparametric", False)),
        max_mesh_passes_only=bool(args.get("max_mesh_passes_only", True)),
    )


def tool_get_parameter_combination(args: dict) -> dict:
    return _res.get_parameter_combination(
        project_path=project_path_from_args(args),
        run_id=run_id_from_args(args),
        module_type=str(args.get("module_type", "3d")),
        allow_interactive=bool(args.get("allow_interactive", False)),
        subproject_treepath=str(args.get("subproject_treepath", "")),
    )


def tool_get_1d_result(args: dict) -> dict:
    return _res.get_1d_result(
        project_path=project_path_from_args(args),
        treepath=str(args.get("treepath", "")),
        module_type=str(args.get("module_type", "3d")),
        run_id=run_id_from_args(args),
        load_impedances=bool(args.get("load_impedances", True)),
        export_path=str(args.get("export_path", "")),
        allow_interactive=bool(args.get("allow_interactive", False)),
        subproject_treepath=str(args.get("subproject_treepath", "")),
    )


def tool_get_2d_result(args: dict) -> dict:
    return _res.get_2d_result(
        project_path=project_path_from_args(args),
        treepath=str(args.get("treepath", "")),
        module_type=str(args.get("module_type", "3d")),
        export_path=str(args.get("export_path", "")),
        allow_interactive=bool(args.get("allow_interactive", False)),
        subproject_treepath=str(args.get("subproject_treepath", "")),
        include_data=bool(args.get("include_data", False)),
    )


def tool_list_sparameter_results(args: dict) -> dict:
    return _res.list_sparameter_results(project_path_from_args(args))


def tool_export_sparameter(args: dict) -> dict:
    return _res.export_sparameter(
        project_path=project_path_from_args(args),
        run_id=run_id_from_args(args),
        output_path=str(args.get("output_path", "")),
        result_path=str(args.get("result_path", "")),
        response_port=str(args.get("response_port", "")),
        excitation_port=str(args.get("excitation_port", "")),
        response_mode=args.get("response_mode"),
        excitation_mode=args.get("excitation_mode"),
    )


def tool_export_touchstone(args: dict) -> dict:
    return _res.export_touchstone(
        project_path=project_path_from_args(args),
        output_base_path=str(args.get("output_base_path", "")),
        parameter_type=str(args.get("parameter_type", "S")),
        data_format=str(args.get("data_format", "MA")),
        frequency_range=str(args.get("frequency_range", "Full")),
        fmin=args.get("fmin"),
        fmax=args.get("fmax"),
        impedance=float(args.get("impedance", 50.0)),
        renormalize=bool(args.get("renormalize", True)),
        sample_count=int(args.get("sample_count", 0)),
        use_ar_results=bool(args.get("use_ar_results", False)),
    )


def tool_generate_report(args: dict) -> dict:
    return _res.generate_report(
        data_dir=str(args.get("data_dir", "")),
        output_html=str(args.get("output_html", "")),
        page_title=str(args.get("page_title", "")),
        modules=str(args.get("modules", "")),
        split=bool(args.get("split", False)),
    )


def tool_plot_exported_file(args: dict) -> dict:
    file_path = args.get("file_path") or args.get("export_path") or args.get("output_file")
    return _res.plot_exported_file(
        file_path=str(file_path or ""),
        output_html=str(args.get("output_html", "")),
        page_title=str(args.get("page_title", "")),
    )


_register_tool_defs(TOOL_DEFS)
