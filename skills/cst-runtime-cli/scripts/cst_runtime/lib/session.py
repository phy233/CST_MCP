"""CST project session management.

Usage:
    from cst_runtime.lib.session import open_project, close_project, inspect

    # Open a CST project
    open_project("C:\\path\\to\\model.cst")

    # Check environment status
    status = inspect("C:\\path\\to\\model.cst")

    # Close project
    close_project("C:\\path\\to\\model.cst", save=True)
"""
from __future__ import annotations

from typing import Any

from ..core.session import open_project as _open_project
from ..core.session import close_project as _close_project
from ..core.session import inspect as _inspect
from ..core.session import quit_cst as _quit_cst
from ..core.identity import list_open_projects as _list_open_projects


def open_project(project_path: str) -> dict[str, Any]:
    """Open a CST project.

    Args:
        project_path: Path to .cst file

    Returns:
        Dict with status and project info

    Raises:
        RuntimeError: If project cannot be opened
    """
    result = _open_project(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to open project"))
    return result


def close_project(project_path: str, save: bool = False) -> dict[str, Any]:
    """Close a CST project.

    Args:
        project_path: Path to .cst file
        save: Whether to save before closing

    Returns:
        Dict with status

    Raises:
        RuntimeError: If project cannot be closed
    """
    result = _close_project(project_path, save=save)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to close project"))
    return result


def inspect(project_path: str = "") -> dict[str, Any]:
    """Inspect CST environment state.

    Args:
        project_path: Optional path to specific project

    Returns:
        Dict with environment status information
    """
    return _inspect(project_path)


def quit_cst(project_path: str = "") -> dict[str, Any]:
    """Quit CST Design Environment.

    Args:
        project_path: Optional path to specific project

    Returns:
        Dict with status

    Raises:
        RuntimeError: If CST cannot be quit
    """
    result = _quit_cst(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to quit CST"))
    return result


def list_open() -> list[str]:
    """List all open CST project paths.

    Returns:
        List of project file paths
    """
    result = _list_open_projects()
    if result.get("status") == "error":
        return []
    return result.get("projects", [])


def is_locked(project_path: str) -> bool:
    """Check if a CST project is locked.

    Args:
        project_path: Path to .cst file

    Returns:
        True if project is locked
    """
    import pathlib
    lock_file = pathlib.Path(project_path).with_suffix(".cst.lock")
    return lock_file.exists()
