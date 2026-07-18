"""MCP Tool definitions: CST Results operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def get_sparam(project_path: str, treepath: str, run_id: int = 0) -> dict[str, Any]:
    """
    Read S-parameter data (offline, no CST needed).

    Args:
        project_path: Path to .cst file
        treepath: Result tree path (e.g., "1D Results\S-Parameters\S1,1")
        run_id: Run ID (0 for default)

    Returns:
        Dict with xdata, ydata, and metadata

    Raises:
        RuntimeError: If result cannot be read
    """
    return call_cst("lib.results", "get_sparam", project_path=project_path, treepath=treepath, run_id=run_id)

def get_sparam_at_freq(project_path: str, treepath: str, freq_ghz: float, run_id: int = 0) -> dict[str, Any]:
    """
    Get S-parameter at specific frequency (linear interpolation).

    Args:
        project_path: Path to .cst file
        treepath: Result tree path
        freq_ghz: Target frequency in GHz
        run_id: Run ID (0 for default)

    Returns:
        Dict with interpolated real, imag, magnitude, phase values

    Raises:
        RuntimeError: If result cannot be read or interpolated
    """
    return call_cst("lib.results", "get_sparam_at_freq", project_path=project_path, treepath=treepath, freq_ghz=freq_ghz, run_id=run_id)

def get_2d_field(project_path: str, treepath: str) -> dict[str, Any]:
    """
    Read 2D field data.

    Args:
        project_path: Path to .cst file
        treepath: Result tree path

    Returns:
        Dict with field data

    Raises:
        RuntimeError: If result cannot be read
    """
    return call_cst("lib.results", "get_2d_field", project_path=project_path, treepath=treepath)

def list_items(project_path: str, filter_type: str = '0D/1D') -> dict[str, Any]:
    """
    List available result items.

    Args:
        project_path: Path to .cst file
        filter_type: Filter type (e.g., "0D/1D", "2D", "all")

    Returns:
        List of result tree paths
    """
    return call_cst("lib.results", "list_items", project_path=project_path, filter_type=filter_type)

def list_sparams(project_path: str) -> dict[str, Any]:
    """
    List available S-parameters.

    Args:
        project_path: Path to .cst file

    Returns:
        List of S-parameter tree paths
    """
    return call_cst("lib.results", "list_sparams", project_path=project_path)

def sparam_exists(project_path: str, treepath: str) -> dict[str, Any]:
    """
    Check if S-parameter exists.

    Args:
        project_path: Path to .cst file
        treepath: Result tree path

    Returns:
        True if S-parameter exists
    """
    return call_cst("lib.results", "sparam_exists", project_path=project_path, treepath=treepath)

def list_runs(project_path: str) -> dict[str, Any]:
    """
    List simulation run IDs.

    Args:
        project_path: Path to .cst file

    Returns:
        List of run IDs
    """
    return call_cst("lib.results", "list_runs", project_path=project_path)

def get_param_combo(project_path: str, run_id: int) -> dict[str, Any]:
    """
    Get parameter combination for a run.

    Args:
        project_path: Path to .cst file
        run_id: Run ID

    Returns:
        Dict with parameter names and values

    Raises:
        RuntimeError: If parameter combination cannot be retrieved
    """
    return call_cst("lib.results", "get_param_combo", project_path=project_path, run_id=run_id)

def export_all(project_path: str, kwargs: Any) -> dict[str, Any]:
    """
    Export all results for a run.

    Args:
        project_path: Path to .cst file
        **kwargs: Additional arguments for export

    Returns:
        Dict with exported files

    Raises:
        RuntimeError: If export fails
    """
    return call_cst("lib.results", "export_all", project_path=project_path, kwargs=kwargs)

RESULTS_TOOLS = [
    {"name": "get-sparam", "handler": get_sparam},
    {"name": "get-sparam-at-freq", "handler": get_sparam_at_freq},
    {"name": "get-2d-field", "handler": get_2d_field},
    {"name": "list-items", "handler": list_items},
    {"name": "list-sparams", "handler": list_sparams},
    {"name": "sparam-exists", "handler": sparam_exists},
    {"name": "list-runs", "handler": list_runs},
    {"name": "get-param-combo", "handler": get_param_combo},
    {"name": "export-all", "handler": export_all},
]
