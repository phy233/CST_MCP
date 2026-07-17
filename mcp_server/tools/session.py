from typing import Any
from cst_runtime.core.proxy import call_cst

async def open_project(project_path: str) -> dict[str, Any]:
    """[SESSION] Open an existing CST project.

    Args:
        project_path: Absolute path to the .cst file.
    """
    return call_cst("lib.session", "open_project", project_path=project_path)

async def create_blank_project(project_path: str) -> dict[str, Any]:
    """[SESSION] Create a new blank CST project.

    Args:
        project_path: Absolute path to the new .cst file.
    """
    return call_cst("lib.session", "create_blank_project", project_path=project_path)

async def close_project(project_path: str, save: bool = False) -> dict[str, Any]:
    """[SESSION] Close a CST project.

    Args:
        project_path: Absolute path to the .cst file.
        save: Whether to save changes before closing.
    """
    return call_cst("lib.session", "close_project", project_path=project_path, save=save)

async def inspect_session(project_path: str = "") -> dict[str, Any]:
    """[READ] Inspect the state of the CST environment.

    Args:
        project_path: (Optional) Path to a specific project. Leave empty for global state.
    """
    return call_cst("lib.session", "inspect", project_path=project_path)

async def save_project(project_path: str) -> dict[str, Any]:
    """[WRITE] Save the current CST project.

    Args:
        project_path: Absolute path to the .cst file.
    """
    return call_cst("lib.session", "save_project", project_path=project_path)

async def quit_cst(project_path: str = "") -> dict[str, Any]:
    """[SESSION] Quit the CST Design Environment completely.

    Args:
        project_path: (Optional) Path to the current project context.
    """
    return call_cst("lib.session", "quit_cst", project_path=project_path)

async def list_open_projects() -> dict[str, Any]:
    """[READ] List all currently open CST projects.
    
    Returns the raw list directly from proxy.
    """
    return call_cst("lib.session", "list_open")

async def is_project_locked(project_path: str) -> dict[str, Any]:
    """[READ] Check if a CST project is locked (running or crashed).

    Args:
        project_path: Absolute path to the .cst file.
    """
    return call_cst("lib.session", "is_locked", project_path=project_path)

SESSION_TOOLS = [
    {"name": "open-project", "handler": open_project},
    {"name": "create-blank-project", "handler": create_blank_project},
    {"name": "close-project", "handler": close_project},
    {"name": "save-project", "handler": save_project},
    {"name": "inspect-session", "handler": inspect_session},
    {"name": "quit-cst", "handler": quit_cst},
    {"name": "list-open-projects", "handler": list_open_projects},
    {"name": "is-project-locked", "handler": is_project_locked},
]
