"""CST project parameter operations.

Usage:
    from cst_runtime.lib.parameters import list_params, get_param, set_param

    # List all parameters
    params = list_params("C:\\path\\to\\model.cst")

    # Get single parameter
    g = get_param("C:\\path\\to\\model.cst", "g")

    # Set parameter
    set_param("C:\\path\\to\\model.cst", "g", 24.0)
"""
from __future__ import annotations

from typing import Any

from ..core.project import list_parameters as _list_parameters
from ..core.project import change_parameter as _change_parameter
from ..core.project import define_parameters as _define_parameters


def list_params(project_path: str) -> dict[str, float]:
    """List all parameters and their current values.

    Args:
        project_path: Path to .cst file

    Returns:
        Dict mapping parameter names to values

    Raises:
        RuntimeError: If parameters cannot be listed
    """
    result = _list_parameters(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to list parameters"))
    return {k: v["value"] for k, v in result["parameters"].items()}


def get_param(project_path: str, name: str) -> float:
    """Get a single parameter value.

    Args:
        project_path: Path to .cst file
        name: Parameter name

    Returns:
        Parameter value

    Raises:
        KeyError: If parameter not found
        RuntimeError: If parameter cannot be read
    """
    params = list_params(project_path)
    if name not in params:
        raise KeyError(f"Parameter '{name}' not found. Available: {list(params.keys())}")
    return params[name]


def set_param(project_path: str, name: str, value: float) -> None:
    """Set a parameter value.

    After modification, call solver.rebuild() or close+reopen to apply.

    Args:
        project_path: Path to .cst file
        name: Parameter name
        value: New value

    Raises:
        RuntimeError: If parameter cannot be set
    """
    result = _change_parameter(project_path, name=name, value=value)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set parameter"))


def set_params(project_path: str, params: dict[str, float]) -> None:
    """Set multiple parameters at once.

    Args:
        project_path: Path to .cst file
        params: Dict mapping parameter names to values

    Raises:
        RuntimeError: If parameters cannot be set
    """
    names = list(params.keys())
    values = [str(v) for v in params.values()]
    result = _define_parameters(project_path, names, values)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set parameters"))


def param_exists(project_path: str, name: str) -> bool:
    """Check if a parameter exists.

    Args:
        project_path: Path to .cst file
        name: Parameter name

    Returns:
        True if parameter exists
    """
    try:
        params = list_params(project_path)
        return name in params
    except Exception:
        return False
