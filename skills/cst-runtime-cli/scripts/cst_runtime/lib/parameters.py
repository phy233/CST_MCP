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
from ._facade import call_core
from .contracts import OperationResult, error_result, invalid_arguments, success_result


def list_params(project_path: str) -> OperationResult:
    """List all parameters and their current values.

    Args:
        project_path: Path to .cst file

    Returns:
        Dict mapping parameter names to values

    Raises:
        RuntimeError: If parameters cannot be listed
    """
    result = call_core(_list_parameters, project_path)
    if result.get("status") == "success":
        result["values"] = {
            name: entry.get("value") if isinstance(entry, dict) else entry
            for name, entry in result.get("parameters", {}).items()
        }
    return result


def get_param(project_path: str, name: str) -> OperationResult:
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
    if not str(name).strip():
        return invalid_arguments("name 不能为空")
    result = list_params(project_path)
    if result.get("status") == "error":
        return result
    values = result.get("values", {})
    if name not in values:
        return error_result(
            "parameter_not_found",
            f"参数不存在: {name}",
            parameter=name,
            available_parameters=sorted(values),
        )
    return success_result(
        project_path=project_path,
        parameter=name,
        value=values[name],
    )


def set_param(project_path: str, name: str, value: float) -> OperationResult:
    """Set a parameter value.

    After modification, call solver.rebuild() or close+reopen to apply.

    Args:
        project_path: Path to .cst file
        name: Parameter name
        value: New value

    Raises:
        RuntimeError: If parameter cannot be set
    """
    if not str(name).strip():
        return invalid_arguments("name 不能为空")
    return call_core(_change_parameter, project_path, name=name, value=value)


def set_params(project_path: str, params: dict[str, float]) -> OperationResult:
    """Set multiple parameters at once.

    Args:
        project_path: Path to .cst file
        params: Dict mapping parameter names to values

    Raises:
        RuntimeError: If parameters cannot be set
    """
    if not isinstance(params, dict) or not params:
        return invalid_arguments("params 必须是非空字典")
    names = list(params.keys())
    values = [str(v) for v in params.values()]
    return call_core(_define_parameters, project_path, names, values)


def param_exists(project_path: str, name: str) -> OperationResult:
    """Check if a parameter exists.

    Args:
        project_path: Path to .cst file
        name: Parameter name

    Returns:
        True if parameter exists
    """
    result = list_params(project_path)
    if result.get("status") == "error":
        return result
    return success_result(
        project_path=project_path,
        parameter=name,
        exists=name in result.get("values", {}),
    )
