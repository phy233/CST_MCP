"""results.py — results 工具定义"""
from . import _register_tool_defs


TOOL_DEFS = {
"list-sparameter-results": {
    "category": "results",
    "risk": "read",
    "description": (
        "枚举实际 ResultTree 中的普通端口与 Floquet S 参数节点及可用 Run ID。"
        "允许工程同时在 CST 中打开；此时读取最近保存到磁盘的工程状态。"
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
        "按真实 ResultTree 节点导出一条 S 参数曲线。可直接指定 result_path，或使用响应端口、"
        "激励端口及可选模式；支持 S1,1 和 SZmin(1),Zmax(1) 等 CST 2022 名称。"
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
        "使用 CST 2022 TOUCHSTONE Object 导出完整 S/Y/Z 网络矩阵；端口模式顺序由 CST 文件头给出。"
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
    "description": "Generate a modular HTML report from exported S11, farfield, and audit files. Supports --modules and --split.",
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
                    "电磁仿真报告"
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
    "description": "Read an exact 0D/1D result-tree path with cst.results and serialize its saved data to JSON.",
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
                "description": "run_id=0（默认）选择最新结果；非参数化仿真中 0 也可能是唯一真实 Run ID",
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
    "description": "Serialize 2D data only when the installed cst.results API exposes get_result2d_item; CST 2022 does not document it.",
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
    "description": "Read the parameter combination for a result run ID.",
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
                "description": "run_id=0 返回最新参数组合；非参数化仿真中 0 也可能是唯一真实 Run ID",
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
    "description": "Read cst.results version information.",
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
    "description": "List result tree items from a project path.",
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
    "description": "List CST result run IDs from a project path.",
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
    "description": "List subprojects from a CST results project by explicit project_path.",
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
    "description": "Validate that cst.results can open a project path.",
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
    "description": "Render an exported JSON result or CST farfield ASCII/TXT file to an HTML preview.",
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
