"""CST farfield operations.

Usage:
    from cst_runtime.lib.farfield import export_grid, export_cut, list_monitors

    # Export farfield grid data
    result = export_grid("C:\\path\\to\\model.cst",
                         farfield_name="farfield (f=10)_1",
                         export_dir="C:\\exports")

    # Export farfield cut data
    result = export_cut("C:\\path\\to\\model.cst",
                        tree_path="Farfields\\farfield (f=10)_1\\Phi=0")

    # List farfield monitors
    monitors = list_monitors("C:\\path\\to\\model.cst")
"""
from __future__ import annotations

from typing import Any

from ..core.farfield import export_farfield_grid as _export_farfield_grid
from ..core.farfield import discover_farfield_monitors as _discover_farfield_monitors
from ..core import farfield as _core_farfield
from ._facade import call_core, wrap_core
from .contracts import OperationResult, success_result


def export_grid(
    project_path: str,
    farfield_name: str,
    export_dir: str,
    quantity: str = "Realized Gain",
    theta_step_deg: float = 1.0,
    phi_step_deg: float = 2.0,
    run_id: int | None = None,
) -> OperationResult:
    """Export farfield grid data.

    Args:
        project_path: Path to .cst file
        farfield_name: Farfield monitor name
        export_dir: Export directory
        quantity: Quantity to export ("Realized Gain", "Gain", "Directivity")
        theta_step_deg: Theta step in degrees
        phi_step_deg: Phi step in degrees
        run_id: Optional run ID

    Returns:
        Dict with export information

    Raises:
        RuntimeError: If export fails
    """
    return call_core(
        _export_farfield_grid,
        project_path, farfield_name, export_dir,
        quantity=quantity,
        theta_step_deg=theta_step_deg,
        phi_step_deg=phi_step_deg,
        run_id=run_id,
    )


def export_cut(
    project_path: str,
    tree_path: str,
    export_dir: str = "",
) -> OperationResult:
    """Export farfield cut data.

    Args:
        project_path: Path to .cst file
        tree_path: Farfield cut tree path
        export_dir: Export directory

    Returns:
        Dict with export information

    Raises:
        RuntimeError: If export fails
    """
    return call_core(
        _core_farfield.export_farfield_cut,
        project_path=project_path,
        tree_path=tree_path,
        export_dir=export_dir,
    )


def list_monitors(project_path: str) -> OperationResult:
    """List farfield monitors.

    Args:
        project_path: Path to .cst file

    Returns:
        List of farfield monitor names
    """
    return call_core(_discover_farfield_monitors, project_path)


discover_farfield_monitors = wrap_core(_core_farfield.discover_farfield_monitors)
export_farfield_grid = wrap_core(_core_farfield.export_farfield_grid)
export_farfield_cut = wrap_core(_core_farfield.export_farfield_cut)
calculate_farfield_neighborhood_flatness = wrap_core(
    _core_farfield.calculate_farfield_neighborhood_flatness
)
