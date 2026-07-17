from typing import Any
from cst_runtime.core.proxy import call_cst

async def list_parameters(project_path: str) -> dict[str, Any]:
    """[READ] List all global parameters and their current values.

    Args:
        project_path: Absolute path to the .cst file.
    """
    return call_cst("lib.parameters", "list_params", project_path=project_path)

async def get_parameter(project_path: str, name: str) -> dict[str, Any]:
    """[READ] Get the value of a single parameter.

    Args:
        project_path: Absolute path to the .cst file.
        name: The name of the parameter.
    """
    return call_cst("lib.parameters", "get_param", project_path=project_path, name=name)

async def set_parameter(project_path: str, name: str, value: float) -> dict[str, Any]:
    """[WRITE] Set the value of a parameter.

    Note: After modification, call rebuild-structure to apply.

    Args:
        project_path: Absolute path to the .cst file.
        name: The name of the parameter to change.
        value: The new numerical value.
    """
    return call_cst("lib.parameters", "set_param", project_path=project_path, name=name, value=value)

async def set_parameters(project_path: str, params: dict[str, float]) -> dict[str, Any]:
    """[WRITE] Set multiple parameters at once.

    Args:
        project_path: Absolute path to the .cst file.
        params: A dictionary mapping parameter names to their new numerical values.
    """
    return call_cst("lib.parameters", "set_params", project_path=project_path, params=params)

async def parameter_exists(project_path: str, name: str) -> dict[str, Any]:
    """[READ] Check if a specific parameter exists in the project.

    Args:
        project_path: Absolute path to the .cst file.
        name: The name of the parameter to check.
    """
    return call_cst("lib.parameters", "param_exists", project_path=project_path, name=name)

PARAMETERS_TOOLS = [
    {"name": "list-parameters", "handler": list_parameters},
    {"name": "get-parameter", "handler": get_parameter},
    {"name": "set-parameter", "handler": set_parameter},
    {"name": "set-parameters", "handler": set_parameters},
    {"name": "parameter-exists", "handler": parameter_exists},
]
