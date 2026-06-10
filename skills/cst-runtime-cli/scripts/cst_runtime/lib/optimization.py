"""CST optimization operations using Optuna.

Usage:
    from cst_runtime.lib.optimization import create_study, ask, tell, best

    # Create an optimization study
    create_study("C:\\studies\\my_study.db",
                 study_name="s11_optimization",
                 parameters={"g": {"type": "float", "min": 20, "max": 30},
                             "patch_w": {"type": "float", "min": 5, "max": 10}})

    # Get next parameter suggestion
    trial = ask("C:\\studies\\my_study.db", "s11_optimization")

    # Report result
    tell("C:\\studies\\my_study.db", "s11_optimization",
         trial_number=trial["trial_number"], value=-18.3)

    # Get best result
    best_result = best("C:\\studies\\my_study.db", "s11_optimization")
"""
from __future__ import annotations

from typing import Any

from ..core.optimizer import create_study as _create_study
from ..core.optimizer import ask_study as _ask_study
from ..core.optimizer import tell_study as _tell_study
from ..core.optimizer import best_study as _best_study


def create_study(
    storage_path: str,
    study_name: str,
    parameters: dict[str, Any],
    direction: str = "minimize",
) -> None:
    """Create an Optuna optimization study.

    Args:
        storage_path: Path to SQLite database file
        study_name: Study name
        parameters: Parameter definitions (e.g., {"g": {"type": "float", "min": 20, "max": 30}})
        direction: Optimization direction ("minimize" or "maximize")

    Raises:
        RuntimeError: If study cannot be created
    """
    import json
    result = _create_study(
        storage_path, study_name,
        json.dumps(parameters),
        direction=direction,
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create study"))


def ask(storage_path: str, study_name: str) -> dict[str, Any]:
    """Get next parameter suggestion from optimizer.

    Args:
        storage_path: Path to SQLite database file
        study_name: Study name

    Returns:
        Dict with trial_number and params

    Raises:
        RuntimeError: If suggestion cannot be obtained
    """
    result = _ask_study(storage_path, study_name)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to get suggestion"))
    return result


def tell(
    storage_path: str,
    study_name: str,
    trial_number: int,
    value: float | None = None,
    values: list[float] | None = None,
) -> None:
    """Report result to optimizer.

    Args:
        storage_path: Path to SQLite database file
        study_name: Study name
        trial_number: Trial number from ask()
        value: Objective value (for single-objective)
        values: Objective values (for multi-objective)

    Raises:
        RuntimeError: If result cannot be reported
    """
    result = _tell_study(
        storage_path, study_name, trial_number,
        value=value, values=values,
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to report result"))


def best(storage_path: str, study_name: str) -> dict[str, Any]:
    """Get best result from optimizer.

    Args:
        storage_path: Path to SQLite database file
        study_name: Study name

    Returns:
        Dict with best_value and best_params

    Raises:
        RuntimeError: If best result cannot be retrieved
    """
    result = _best_study(storage_path, study_name)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to get best result"))
    return result
