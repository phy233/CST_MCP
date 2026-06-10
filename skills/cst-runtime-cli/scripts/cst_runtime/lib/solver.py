"""CST solver control operations.

Usage:
    from cst_runtime.lib.solver import start, is_running, stop, rebuild

    # Start simulation (non-blocking)
    start("C:\\path\\to\\model.cst")

    # Check if running
    running = is_running("C:\\path\\to\\model.cst")

    # Stop simulation
    stop("C:\\path\\to\\model.cst")

    # Rebuild structure after parameter changes
    rebuild("C:\\path\\to\\model.cst")
"""
from __future__ import annotations

import time
from typing import Any

from ..core.simulation import start_simulation as _start_simulation
from ..core.simulation import start_simulation_async as _start_simulation_async
from ..core.simulation import is_simulation_running as _is_simulation_running
from ..core.simulation import stop_simulation as _stop_simulation
from ..core.identity import attach_expected_project


def set_frequency_range(project_path: str, fmin: float, fmax: float) -> None:
    """Set solver frequency range.

    Args:
        project_path: Path to .cst file
        fmin: Minimum frequency in GHz
        fmax: Maximum frequency in GHz

    Raises:
        RuntimeError: If frequency range cannot be set
    """
    from ..core.simulation import _single_vba_pops
    vba = f'Solver.FrequencyRange "{fmin}", "{fmax}"'
    result = _single_vba_pops(project_path, "Set Frequency Range", vba)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set frequency range"))


def start(project_path: str) -> None:
    """Start simulation (blocking).

    Args:
        project_path: Path to .cst file

    Raises:
        RuntimeError: If simulation cannot be started
    """
    result = _start_simulation(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to start simulation"))


def start_async(project_path: str) -> None:
    """Start simulation (non-blocking).

    Args:
        project_path: Path to .cst file

    Raises:
        RuntimeError: If simulation cannot be started
    """
    result = _start_simulation_async(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to start simulation"))


def wait(project_path: str, timeout: int = 3600, interval: int = 10) -> bool:
    """Wait for simulation to complete.

    Args:
        project_path: Path to .cst file
        timeout: Maximum wait time in seconds
        interval: Polling interval in seconds

    Returns:
        True if simulation completed, False if timed out
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not is_running(project_path):
            return True
        time.sleep(interval)
    return False


def is_running(project_path: str) -> bool:
    """Check if simulation is running.

    Args:
        project_path: Path to .cst file

    Returns:
        True if simulation is running
    """
    result = _is_simulation_running(project_path)
    if result.get("status") == "error":
        return False
    return result.get("running", False)


def stop(project_path: str) -> None:
    """Stop simulation.

    Args:
        project_path: Path to .cst file

    Raises:
        RuntimeError: If simulation cannot be stopped
    """
    result = _stop_simulation(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to stop simulation"))


def rebuild(project_path: str) -> None:
    """Rebuild geometry from parameters.

    Args:
        project_path: Path to .cst file

    Raises:
        RuntimeError: If rebuild fails
    """
    from ..core.simulation import _single_vba_pops
    result = _single_vba_pops(project_path, "Rebuild", "Application.Rebuild")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to rebuild structure"))


def delete_results(project_path: str) -> None:
    """Delete all simulation results.

    Args:
        project_path: Path to .cst file

    Raises:
        RuntimeError: If results cannot be deleted
    """
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        raise RuntimeError(status.get("message", "Project not found"))
    try:
        project.model3d.DeleteResults()
    except Exception as e:
        raise RuntimeError(f"Failed to delete results: {e}")


def get_solver_type(project_path: str) -> str:
    """Get solver type.

    Args:
        project_path: Path to .cst file

    Returns:
        Solver type string (e.g., "Frequency", "Time", "Eigenmode")

    Raises:
        RuntimeError: If solver type cannot be determined
    """
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        raise RuntimeError(status.get("message", "Project not found"))
    try:
        return project.model3d.GetSolverType()
    except Exception as e:
        raise RuntimeError(f"Failed to get solver type: {e}")


def _abs_project_path(project_path: str) -> str:
    """Normalize project path to absolute path."""
    from pathlib import Path
    return str(Path(project_path).expanduser().resolve())
