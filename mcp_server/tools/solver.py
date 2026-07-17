"""MCP Tool definitions: CST Solver operations."""
from typing import Any

from ..proxy import call_cst


def set_frequency_range(project_path: str, fmin: float, fmax: float) -> dict[str, Any]:
    """[WRITE] Set the solver frequency range.

    Args:
        project_path: Absolute path to the .cst file.
        fmin: Minimum frequency (e.g. in GHz based on project units).
        fmax: Maximum frequency.
    """
    return call_cst("lib.solver", "set_frequency_range", project_path=project_path, fmin=fmin, fmax=fmax)

def rebuild_structure(project_path: str) -> dict[str, Any]:
    """[WRITE] Rebuild the 3D structure (e.g. after parameter changes).

    Args:
        project_path: Absolute path to the .cst file.
    """
    return call_cst("lib.solver", "rebuild", project_path=project_path)

def start_simulation(project_path: str) -> dict[str, Any]:
    """[SESSION] Start the solver (runs non-blocking in the background).

    After calling this, use 'sim-status' to poll whether the simulation
    has finished. Do NOT block waiting — simulations can take hours.

    Args:
        project_path: Absolute path to the .cst file.
    """
    return call_cst("lib.solver", "start_async", project_path=project_path)

def sim_status(project_path: str) -> dict[str, Any]:
    """[READ] Check whether a simulation is currently running.

    Use this to poll simulation progress after calling 'start-simulation'.

    Args:
        project_path: Absolute path to the .cst file.

    Returns:
        Dict with 'running' (bool) indicating if the simulation is still active.
    """
    return call_cst("lib.solver", "is_running", project_path=project_path)

SOLVER_TOOLS = [
    {"name": "define-frequency-range", "handler": set_frequency_range},
    {"name": "rebuild-structure", "handler": rebuild_structure},
    {"name": "start-simulation", "handler": start_simulation},
    {"name": "sim-status", "handler": sim_status},
]
