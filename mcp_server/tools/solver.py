from typing import Any
from cst_runtime.core.proxy import call_cst

async def set_frequency_range(project_path: str, fmin: float, fmax: float) -> dict[str, Any]:
    """[WRITE] Set the solver frequency range.

    Args:
        project_path: Absolute path to the .cst file.
        fmin: Minimum frequency (e.g. in GHz based on project units).
        fmax: Maximum frequency.
    """
    return call_cst("lib.solver", "set_frequency_range", project_path=project_path, fmin=fmin, fmax=fmax)

async def rebuild_structure(project_path: str) -> dict[str, Any]:
    """[WRITE] Rebuild the 3D structure (e.g. after parameter changes).

    Args:
        project_path: Absolute path to the .cst file.
    """
    return call_cst("lib.solver", "rebuild", project_path=project_path)

async def start_simulation(project_path: str) -> dict[str, Any]:
    """[SESSION] Start the solver (runs non-blocking in the background).

    Args:
        project_path: Absolute path to the .cst file.
    """
    return call_cst("lib.solver", "start_async", project_path=project_path)

async def wait_simulation(project_path: str, timeout_seconds: int = 3600) -> dict[str, Any]:
    """[LONG-RUNNING] Block and wait for a running simulation to complete.

    Args:
        project_path: Absolute path to the .cst file.
        timeout_seconds: Maximum time to wait in seconds.
    """
    return call_cst("lib.solver", "wait", project_path=project_path, timeout=timeout_seconds)

SOLVER_TOOLS = [
    {"name": "define-frequency-range", "handler": set_frequency_range},
    {"name": "rebuild-structure", "handler": rebuild_structure},
    {"name": "start-simulation", "handler": start_simulation},
    {"name": "wait-simulation", "handler": wait_simulation},
]
