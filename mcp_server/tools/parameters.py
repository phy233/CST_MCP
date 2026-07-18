"""MCP Tool definitions: CST Parameters operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def list_params(project_path: str) -> dict[str, Any]:
    """
    List all parameters and their current values.

    Args:
        project_path: Path to .cst file

    Returns:
        Dict mapping parameter names to values

    Raises:
        RuntimeError: If parameters cannot be listed
    """
    return call_cst("lib.parameters", "list_params", project_path=project_path)

def get_param(project_path: str, name: str) -> dict[str, Any]:
    """
    Get a single parameter value.

    Args:
        project_path: Path to .cst file
        name: Parameter name

    Returns:
        Parameter value

    Raises:
        KeyError: If parameter not found
        RuntimeError: If parameter cannot be read
    """
    return call_cst("lib.parameters", "get_param", project_path=project_path, name=name)

def set_param(project_path: str, name: str, value: float) -> dict[str, Any]:
    """
    Set a parameter value.

    After modification, call solver.rebuild() or close+reopen to apply.

    Args:
        project_path: Path to .cst file
        name: Parameter name
        value: New value

    Raises:
        RuntimeError: If parameter cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.parameters", "set_param", project_path=project_path, name=name, value=value)

def set_params(project_path: str, params: dict[str, float]) -> dict[str, Any]:
    """
    Set multiple parameters at once.

    Args:
        project_path: Path to .cst file
        params: Dict mapping parameter names to values

    Raises:
        RuntimeError: If parameters cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.parameters", "set_params", project_path=project_path, params=params)

def param_exists(project_path: str, name: str) -> dict[str, Any]:
    """
    Check if a parameter exists.

    Args:
        project_path: Path to .cst file
        name: Parameter name

    Returns:
        True if parameter exists
    """
    return call_cst("lib.parameters", "param_exists", project_path=project_path, name=name)

PARAMETERS_TOOLS = [
    {"name": "list-params", "handler": list_params},
    {"name": "get-param", "handler": get_param},
    {"name": "set-param", "handler": set_param},
    {"name": "set-params", "handler": set_params},
    {"name": "param-exists", "handler": param_exists},
]
