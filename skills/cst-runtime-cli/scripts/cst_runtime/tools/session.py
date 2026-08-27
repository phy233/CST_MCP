"""session.py — session_manager + process_cleanup 工具定义"""
from . import _register_tool_defs


TOOL_DEFS = {
"create-blank-project": {
    "category": "session_manager",
    "risk": "write",
    "description": (
        "Use this when the user needs a new blank CST project at an explicit .cst path. "
        "It creates the project and session boundary only; define units, geometry, materials, "
        "boundaries, and solver settings with their dedicated tools."
    ),
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
    "description": (
        "Use this to close the expected Runtime-managed CST project, optionally save it and "
        "wait for its lock to clear. Do not close or kill an external Design Environment; "
        "process cleanup remains limited by the Runtime ownership and allowlist rules."
    ),
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
    "description": (
        "Use this when project ownership, process identity, a file lock, or reattach readiness "
        "is unclear. It is a read-only diagnostic gate, not a routine pre-check or post-check "
        "after every successful CST call."
    ),
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
        "Use this to open one explicit existing CST project through the central session manager. "
        "It auto-attaches only to the unique PID created by this call; for an existing or "
        "ambiguous session, first return candidate PIDs and ask the user, then pass both "
        "confirm_existing_session_takeover=true and the confirmed existing_session_pid. "
        "Confirmation permits attachment but does not transfer ownership of an external session."
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
                "description": (
                    "Set true only after the user has seen the candidate PIDs and explicitly "
                    "approved attaching to one existing session."
                )
            },
            "existing_session_pid": {
                "type": ["integer", "null"],
                "minimum": 1,
                "default": None,
                "description": "Design Environment PID that the user explicitly approved for attachment."
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
    "description": (
        "Use this from the human CLI only to quit a Runtime-owned CST Design Environment "
        "identified by the process allowlist and project-lock evidence. Never use it to quit "
        "an external session that was merely attached with user confirmation."
    ),
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
        "Use this only to reattach an already open CST project, not to create or launch one. "
        "The first call returns candidate PIDs; after asking the user, pass both the confirmation "
        "flag and selected PID. Confirmation permits attachment but does not transfer ownership."
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
                "description": (
                    "Set true only after the user explicitly approves attaching to the existing session."
                )
            },
            "existing_session_pid": {
                "type": ["integer", "null"],
                "minimum": 1,
                "default": None,
                "description": "Design Environment PID that the user explicitly approved for attachment."
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
    "description": (
        "Use this to persist changes in the explicitly identified CST working project when "
        "a saved artifact is required. A successful save should not be repeated merely as a check."
    ),
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
