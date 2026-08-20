"""session.py — session_manager + process_cleanup 工具定义"""
from . import _register_tool_defs


TOOL_DEFS = {
"create-blank-project": {
    "category": "session_manager",
    "risk": "write",
    "description": "Create a new blank CST project at the specified path.",
    "handler": "tool_create_blank_project",
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

"cst-session-close": {
    "category": "session_manager",
    "risk": "session",
    "description": "Close the expected CST project, optionally wait for locks to clear, then inspect the environment.",
    "handler": "tool_cst_session_close",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "save": {
                "type": "boolean",
                "examples": [
                    False
                ]
            },
            "wait_unlock": {
                "type": "boolean",
                "examples": [
                    True
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
            },
            "kill_processes": {
                "type": "boolean",
                "default": False
            }
        },
        "required": [
            "project_path",
            "save",
            "wait_unlock",
            "timeout_seconds",
            "poll_interval_seconds"
        ]
    },
},

"cst-session-inspect": {
    "category": "session_manager",
    "risk": "read",
    "description": "Central session/process gate: inspect processes, locks, open projects, and reattach readiness.",
    "handler": "tool_cst_session_inspect",
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

"cst-session-open": {
    "category": "session_manager",
    "risk": "session",
    "description": (
        "通过中央会话管理器打开 CST 工程。默认只自动接管本次启动后唯一新增的 PID；"
        "若需要接管已有或归属不明确的会话，首次调用会返回候选 PID，调用方必须先询问用户，"
        "再同时提供 confirm_existing_session_takeover=true 与用户确认的 existing_session_pid。"
    ),
    "handler": "tool_cst_session_open",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "confirm_existing_session_takeover": {
                "type": "boolean",
                "default": False,
                "description": "仅在用户看到候选 PID 并明确同意接管后设为 true。"
            },
            "existing_session_pid": {
                "type": ["integer", "null"],
                "minimum": 1,
                "default": None,
                "description": "用户明确确认允许接管的 Design Environment PID。"
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"cst-session-quit": {
    "category": "session_manager",
    "risk": "process-control",
    "description": "Quit CST through the central session manager using only the process allowlist and lock evidence.",
    "handler": "tool_cst_session_quit",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "dry_run": {
                "type": "boolean",
                "examples": [
                    False
                ]
            },
            "settle_seconds": {
                "type": "number",
                "examples": [
                    0.5
                ]
            },
            "force_global_cleanup": {
                "type": "boolean",
                "default": False
            }
        },
        "required": [
            "project_path",
            "dry_run",
            "settle_seconds"
        ]
    },
},

"cst-session-reattach": {
    "category": "session_manager",
    "risk": "session",
    "description": (
        "重新附着已打开的 CST 工程。首次调用只返回候选 PID；"
        "调用方询问用户后，必须同时传入确认标志和用户选择的 PID。"
    ),
    "handler": "tool_cst_session_reattach",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "confirm_existing_session_takeover": {
                "type": "boolean",
                "default": False,
                "description": "仅在用户明确同意接管已有会话后设为 true。"
            },
            "existing_session_pid": {
                "type": ["integer", "null"],
                "minimum": 1,
                "default": None,
                "description": "用户明确确认允许接管的 Design Environment PID。"
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"save-project": {
    "category": "session_manager",
    "risk": "filesystem-write",
    "description": "Save the verified CST working project.",
    "handler": "tool_save_project",
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
}


# --- Handlers ---

from ..lib import session as _sm
from ._arguments import project_path_from_args


def tool_create_blank_project(args: dict) -> dict:
    return _sm.create_blank_project(project_path_from_args(args))


def tool_cst_session_close(args: dict) -> dict:
    return _sm.close_project(
        project_path=project_path_from_args(args),
        save=bool(args.get("save", False)),
        wait_unlock=bool(args.get("wait_unlock", True)),
        timeout_seconds=float(args.get("timeout_seconds", 30.0)),
        poll_interval_seconds=float(args.get("poll_interval_seconds", 0.5)),
        kill_processes=bool(args.get("kill_processes", False)),
    )


def tool_cst_session_inspect(args: dict) -> dict:
    return _sm.inspect(project_path=str(args.get("project_path") or ""))


def tool_cst_session_open(args: dict) -> dict:
    return _sm.open_project(
        project_path_from_args(args),
        confirm_existing_session_takeover=args.get(
            "confirm_existing_session_takeover",
            False,
        ),
        existing_session_pid=args.get("existing_session_pid"),
    )


def tool_cst_session_quit(args: dict) -> dict:
    return _sm.quit_cst(
        project_path=str(args.get("project_path") or ""),
        dry_run=bool(args.get("dry_run", False)),
        settle_seconds=float(args.get("settle_seconds", 0.5)),
        force_global_cleanup=bool(args.get("force_global_cleanup", False)),
    )


def tool_cst_session_reattach(args: dict) -> dict:
    return _sm.reattach_project(
        project_path_from_args(args),
        confirm_existing_session_takeover=args.get(
            "confirm_existing_session_takeover",
            False,
        ),
        existing_session_pid=args.get("existing_session_pid"),
    )


def tool_save_project(args: dict) -> dict:
    return _sm.save_project(project_path_from_args(args))


_register_tool_defs(TOOL_DEFS)
