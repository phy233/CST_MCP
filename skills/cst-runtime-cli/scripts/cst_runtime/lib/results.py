"""CST simulation results reading.

Usage:
    from cst_runtime.lib.results import get_sparam, list_items, list_runs

    # Read S-parameter data
    result = get_sparam("C:\\path\\to\\model.cst",
                       "1D Results\\S-Parameters\\S1,1")

    # List available result items
    items = list_items("C:\\path\\to\\model.cst")

    # List simulation run IDs
    runs = list_runs("C:\\path\\to\\model.cst")
"""
from __future__ import annotations

from typing import Any

from ..core.results import get_1d_result as _get_1d_result
from ..core.results import get_2d_result as _get_2d_result
from ..core.results import list_result_items as _list_result_items
from ..core.results import list_run_ids as _list_run_ids
from ..core.results import get_parameter_combination as _get_parameter_combination
from ..core.results import export_run_results as _export_run_results
from ..core.identity import attach_expected_project


def get_sparam(project_path: str, treepath: str, run_id: int = 0) -> dict[str, Any]:
    """Read S-parameter data (offline, no CST needed).

    Args:
        project_path: Path to .cst file
        treepath: Result tree path (e.g., "1D Results\\S-Parameters\\S1,1")
        run_id: Run ID (0 for default)

    Returns:
        Dict with xdata, ydata, and metadata

    Raises:
        RuntimeError: If result cannot be read
    """
    result = _get_1d_result(project_path, treepath, run_id=run_id)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to read S-parameter"))
    return result


def get_sparam_at_freq(project_path: str, treepath: str, freq_ghz: float, run_id: int = 0) -> dict[str, Any]:
    """Get S-parameter at specific frequency (linear interpolation).

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
    result = get_sparam(project_path, treepath, run_id=run_id)
    ydata = result.get("ydata", [])
    if not ydata:
        raise RuntimeError("No data points found")

    # Extract frequency and S-parameter data
    freqs = [d.get("frequency", 0) for d in ydata]
    reals = [d.get("real", 0) for d in ydata]
    imags = [d.get("imag", 0) for d in ydata]

    # Linear interpolation
    import numpy as np
    re_interp = float(np.interp(freq_ghz, freqs, reals))
    im_interp = float(np.interp(freq_ghz, freqs, imags))
    mag = float(np.sqrt(re_interp**2 + im_interp**2))
    phase = float(np.arctan2(im_interp, re_interp))

    return {
        "status": "success",
        "frequency_ghz": freq_ghz,
        "real": re_interp,
        "imag": im_interp,
        "magnitude": mag,
        "magnitude_db": float(20 * np.log10(max(mag, 1e-30))),
        "phase_rad": phase,
        "phase_deg": float(np.degrees(phase)),
    }


def get_2d_field(project_path: str, treepath: str) -> dict[str, Any]:
    """Read 2D field data.

    Args:
        project_path: Path to .cst file
        treepath: Result tree path

    Returns:
        Dict with field data

    Raises:
        RuntimeError: If result cannot be read
    """
    result = _get_2d_result(project_path, treepath)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to read 2D field"))
    return result


def list_items(project_path: str, filter_type: str = "0D/1D") -> list[str]:
    """List available result items.

    Args:
        project_path: Path to .cst file
        filter_type: Filter type (e.g., "0D/1D", "2D", "all")

    Returns:
        List of result tree paths
    """
    result = _list_result_items(project_path, filter_type=filter_type)
    if result.get("status") == "error":
        return []
    return result.get("items", [])


def list_sparams(project_path: str) -> list[str]:
    """List available S-parameters.

    Args:
        project_path: Path to .cst file

    Returns:
        List of S-parameter tree paths
    """
    all_items = list_items(project_path, filter_type="0D/1D")
    return [item for item in all_items if "S-Parameters" in item]


def sparam_exists(project_path: str, treepath: str) -> bool:
    """Check if S-parameter exists.

    Args:
        project_path: Path to .cst file
        treepath: Result tree path

    Returns:
        True if S-parameter exists
    """
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return False
    try:
        return project.model3d.ResultTree.DoesTreeItemExist(treepath)
    except Exception:
        return False


def list_runs(project_path: str) -> list[int]:
    """List simulation run IDs.

    Args:
        project_path: Path to .cst file

    Returns:
        List of run IDs
    """
    result = _list_run_ids(project_path)
    if result.get("status") == "error":
        return []
    return result.get("run_ids", [])


def get_param_combo(project_path: str, run_id: int) -> dict[str, Any]:
    """Get parameter combination for a run.

    Args:
        project_path: Path to .cst file
        run_id: Run ID

    Returns:
        Dict with parameter names and values

    Raises:
        RuntimeError: If parameter combination cannot be retrieved
    """
    result = _get_parameter_combination(project_path, run_id)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to get parameter combination"))
    return result.get("parameters", {})


def export_all(project_path: str, **kwargs) -> dict[str, Any]:
    """Export all results for a run.

    Args:
        project_path: Path to .cst file
        **kwargs: Additional arguments for export

    Returns:
        Dict with exported files

    Raises:
        RuntimeError: If export fails
    """
    result = _export_run_results(project_path, **kwargs)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to export results"))
    return result


def _abs_project_path(project_path: str) -> str:
    """Normalize project path to absolute path."""
    from pathlib import Path
    return str(Path(project_path).expanduser().resolve())
