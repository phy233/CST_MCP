"""workspace.py — workspace + run 工具定义"""
from . import _register_tool_defs


TOOL_DEFS = {
"get-run-context": {
    "category": "run",
    "risk": "read",
    "description": (
        "Use this to read an existing standard run context by task path and Run ID. It does "
        "not create a run, modify CST, or prove that modeling or simulation has completed."
    ),
    "handler": "tool_get_run_context",
    "json_schema": {
        "type": "object",
        "properties": {
            "task_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx"
                ]
            },
            "run_id": {
                "type": "string",
                "examples": [
                    ""
                ]
            }
        },
        "required": [
            "task_path",
            "run_id"
        ]
    },
},

"health-check": {
    "category": "workspace",
    "risk": "read",
    "description": (
        "Use this at initial setup, after an environment change, or when imports fail to "
        "inspect Python, workspace, and CST-library availability. It is read-only, is not a "
        "routine pre-check, and does not prove real CST compatibility."
    ),
    "handler": "tool_health_check",
    "json_schema": {
        "type": "object",
        "properties": {
            "workspace": {
                "type": "string",
                "examples": [
                    ""
                ]
            }
        },
        "required": ["workspace"],
        "additionalProperties": False
    },
},

"health-repair": {
    "category": "workspace",
    "risk": "filesystem-write",
    "description": (
        "Use this from the human CLI only to apply explicitly requested automatic repairs "
        "reported by health-check. It is not exposed to the Agent and does not install CST itself."
    ),
    "handler": "tool_health_repair",
    "json_schema": {
        "type": "object",
        "properties": {
            "workspace": {"type": "string", "examples": [""]}
        },
        "required": ["workspace"],
        "additionalProperties": False
    },
},

"init-task": {
    "category": "workspace",
    "risk": "filesystem-write",
    "description": (
        "Use this after init-workspace to create task.json and a runs directory for one "
        "human-defined goal and explicit source project. It establishes traceable Runtime "
        "metadata only and does not open, model, or simulate the CST project."
    ),
    "handler": "tool_init_task",
    "json_schema": {
        "type": "object",
        "properties": {
            "workspace": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\empty_workspace"
                ]
            },
            "task_id": {
                "type": "string",
                "examples": [
                    "task_001_demo"
                ]
            },
            "source_project": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\model.cst"
                ]
            },
            "goal": {
                "type": "string",
                "examples": [
                    "demo"
                ]
            },
            "title": {
                "type": "string",
                "examples": [
                    ""
                ]
            },
            "force": {
                "type": "boolean",
                "examples": [
                    False
                ]
            }
        },
        "required": [
            "workspace",
            "task_id",
            "source_project",
            "goal",
            "title",
            "force"
        ]
    },
},

"init-workspace": {
    "category": "workspace",
    "risk": "filesystem-write",
    "description": (
        "Use this to initialize the minimal CST Runtime directory structure in an explicit "
        "empty or existing directory. It does not install CST or validate a real CST session."
    ),
    "handler": "tool_init_workspace",
    "json_schema": {
        "type": "object",
        "properties": {
            "workspace": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\empty_workspace"
                ]
            }
        },
        "required": [
            "workspace"
        ]
    },
},

"install-cst-libraries": {
    "category": "workspace",
    "risk": "filesystem-write",
    "description": (
        "Use this from the human CLI only to install or verify cst, cst.results, and "
        "cst.interface in the uv-managed environment. It is not exposed to the Agent and "
        "does not validate a real CST modeling or solver workflow."
    ),
    "handler": "tool_install_cst_libraries",
    "json_schema": {
        "type": "object",
        "properties": {
            "cst_path": {
                "type": "string",
                "examples": [
                    "C:\\Program Files\\CST Studio Suite 2026\\AMD64\\python_cst_libraries"
                ]
            },
            "dry_run": {
                "type": "boolean",
                "examples": [
                    True
                ]
            }
        },
        "required": [
            "cst_path",
            "dry_run"
        ]
    },
},

"prepare-run": {
    "category": "run",
    "risk": "filesystem-write",
    "description": (
        "Use this to create the standard directory and metadata for a new run inside an "
        "existing Runtime task. It does not open CST, change a model, or start a simulation."
    ),
    "handler": "tool_prepare_run",
    "json_schema": {
        "type": "object",
        "properties": {
            "task_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx"
                ]
            }
        },
        "required": [
            "task_path"
        ]
    },
},
}


# --- Handlers ---

from ..lib import workspace as _ws
from ..lib import workspace as _rw
from ..lib import environment as _ce


def tool_init_workspace(args: dict) -> dict:
    result = _ws.init_workspace(str(args.get("workspace") or ""))
    if result.get("status") == "success":
        ws_root = result.get("workspace_root", "")
        cst_result = _ce.auto_register_cst(ws_root)
        result["cst_auto_registered"] = cst_result.get("cst_registered", False)
    return result


def tool_init_task(args: dict) -> dict:
    return _ws.init_task(
        workspace=str(args.get("workspace") or ""),
        task_id=str(args.get("task_id") or ""),
        source_project=str(args.get("source_project") or ""),
        goal=str(args.get("goal") or ""),
        title=str(args.get("title") or ""),
        force=bool(args.get("force", False)),
    )


def tool_prepare_run(args: dict) -> dict:
    return _rw.prepare_new_run(**args)


def tool_get_run_context(args: dict) -> dict:
    return _rw.get_run_context(**args)


def tool_install_cst_libraries(args: dict) -> dict:
    return _ce.install_cst_libraries(
        cst_path=str(args.get("cst_path", "")),
        dry_run=bool(args.get("dry_run", False)),
    )


def tool_health_check(args: dict) -> dict:
    return _ce.health_check(workspace=str(args.get("workspace", "")))


def tool_health_repair(args: dict) -> dict:
    return _ce.health_repair(workspace=str(args.get("workspace", "")))


_register_tool_defs(TOOL_DEFS)
