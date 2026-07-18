"""MCP Tool definitions: CST Optimization operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def create_study(storage_path: str, study_name: str, parameters: dict[str, Any], direction: str = 'minimize') -> dict[str, Any]:
    """
    Create an Optuna optimization study.

    Args:
        storage_path: Path to SQLite database file
        study_name: Study name
        parameters: Parameter definitions (e.g., {"g": {"type": "float", "min": 20, "max": 30}})
        direction: Optimization direction ("minimize" or "maximize")

    Raises:
        RuntimeError: If study cannot be created

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.optimization", "create_study", storage_path=storage_path, study_name=study_name, parameters=parameters, direction=direction)

def ask(storage_path: str, study_name: str) -> dict[str, Any]:
    """
    Get next parameter suggestion from optimizer.

    Args:
        storage_path: Path to SQLite database file
        study_name: Study name

    Returns:
        Dict with trial_number and params

    Raises:
        RuntimeError: If suggestion cannot be obtained
    """
    return call_cst("lib.optimization", "ask", storage_path=storage_path, study_name=study_name)

def tell(storage_path: str, study_name: str, trial_number: int, value: float | None = None, values: list[float] | None = None) -> dict[str, Any]:
    """
    Report result to optimizer.

    Args:
        storage_path: Path to SQLite database file
        study_name: Study name
        trial_number: Trial number from ask()
        value: Objective value (for single-objective)
        values: Objective values (for multi-objective)

    Raises:
        RuntimeError: If result cannot be reported

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.optimization", "tell", storage_path=storage_path, study_name=study_name, trial_number=trial_number, value=value, values=values)

def best(storage_path: str, study_name: str) -> dict[str, Any]:
    """
    Get best result from optimizer.

    Args:
        storage_path: Path to SQLite database file
        study_name: Study name

    Returns:
        Dict with best_value and best_params

    Raises:
        RuntimeError: If best result cannot be retrieved
    """
    return call_cst("lib.optimization", "best", storage_path=storage_path, study_name=study_name)

OPTIMIZATION_TOOLS = [
    {"name": "create-study", "handler": create_study},
    {"name": "ask", "handler": ask},
    {"name": "tell", "handler": tell},
    {"name": "best", "handler": best},
]
