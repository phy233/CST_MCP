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
from ..core.results import result_item_exists as _result_item_exists
from ..core import results as _core_results
from ._facade import call_core, wrap_core
from .contracts import OperationResult, error_result, success_result


def get_sparam(project_path: str, treepath: str, run_id: int = 0) -> OperationResult:
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
    return call_core(_get_1d_result, project_path, treepath, run_id=run_id)


def get_sparam_at_freq(project_path: str, treepath: str, freq_ghz: float, run_id: int = 0) -> OperationResult:
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
    if result.get("status") == "error":
        return result
    ydata = result.get("ydata", [])
    if not ydata:
        return error_result("result_data_empty", "结果中没有数据点", treepath=treepath)

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

    return success_result(
        frequency_ghz=freq_ghz,
        real=re_interp,
        imag=im_interp,
        magnitude=mag,
        magnitude_db=float(20 * np.log10(max(mag, 1e-30))),
        phase_rad=phase,
        phase_deg=float(np.degrees(phase)),
    )


def get_2d_field(project_path: str, treepath: str) -> OperationResult:
    """Read 2D field data.

    Args:
        project_path: Path to .cst file
        treepath: Result tree path

    Returns:
        Dict with field data

    Raises:
        RuntimeError: If result cannot be read
    """
    return call_core(_get_2d_result, project_path, treepath)


def list_items(project_path: str, filter_type: str = "0D/1D") -> OperationResult:
    """List available result items.

    Args:
        project_path: Path to .cst file
        filter_type: Filter type (e.g., "0D/1D", "2D", "all")

    Returns:
        List of result tree paths
    """
    return call_core(_list_result_items, project_path, filter_type=filter_type)


def list_sparams(project_path: str) -> OperationResult:
    """List available S-parameters.

    Args:
        project_path: Path to .cst file

    Returns:
        List of S-parameter tree paths
    """
    result = list_items(project_path, filter_type="0D/1D")
    if result.get("status") == "error":
        return result
    items = [item for item in result.get("items", []) if "S-Parameters" in item]
    return success_result(project_path=project_path, items=items, count=len(items))


def sparam_exists(project_path: str, treepath: str) -> OperationResult:
    """Check if S-parameter exists.

    Args:
        project_path: Path to .cst file
        treepath: Result tree path

    Returns:
        True if S-parameter exists
    """
    return call_core(_result_item_exists, project_path, treepath)


def list_runs(project_path: str) -> OperationResult:
    """List simulation run IDs.

    Args:
        project_path: Path to .cst file

    Returns:
        List of run IDs
    """
    return call_core(_list_run_ids, project_path)


def get_param_combo(project_path: str, run_id: int) -> OperationResult:
    """Get parameter combination for a run.

    Args:
        project_path: Path to .cst file
        run_id: Run ID

    Returns:
        Dict with parameter names and values

    Raises:
        RuntimeError: If parameter combination cannot be retrieved
    """
    return call_core(_get_parameter_combination, project_path, run_id)


def export_all(project_path: str, **kwargs) -> OperationResult:
    """Export all results for a run.

    Args:
        project_path: Path to .cst file
        **kwargs: Additional arguments for export

    Returns:
        Dict with exported files

    Raises:
        RuntimeError: If export fails
    """
    return call_core(_export_run_results, project_path, **kwargs)


# 工具协议使用的原子业务名称；统一经过同一 lib 边界。
open_project = wrap_core(_core_results.open_project)
list_subprojects = wrap_core(_core_results.list_subprojects)
get_version_info = wrap_core(_core_results.get_version_info)
list_result_items = wrap_core(_core_results.list_result_items)
list_run_ids = wrap_core(_core_results.list_run_ids)
get_parameter_combination = wrap_core(_core_results.get_parameter_combination)
get_1d_result = wrap_core(_core_results.get_1d_result)
get_2d_result = wrap_core(_core_results.get_2d_result)
export_run_results = wrap_core(_core_results.export_run_results)
generate_report = wrap_core(_core_results.generate_report)
plot_exported_file = wrap_core(_core_results.plot_exported_file)


def _abs_project_path(project_path: str) -> str:
    """Normalize project path to absolute path."""
    from pathlib import Path
    return str(Path(project_path).expanduser().resolve())
