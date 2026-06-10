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


def export_grid(
    project_path: str,
    farfield_name: str,
    export_dir: str,
    quantity: str = "Realized Gain",
    theta_step_deg: float = 1.0,
    phi_step_deg: float = 2.0,
    run_id: int | None = None,
) -> dict[str, Any]:
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
    result = _export_farfield_grid(
        project_path, farfield_name, export_dir,
        quantity=quantity,
        theta_step_deg=theta_step_deg,
        phi_step_deg=phi_step_deg,
        run_id=run_id,
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to export farfield grid"))
    return result


def export_cut(
    project_path: str,
    tree_path: str,
    export_dir: str = "",
) -> dict[str, Any]:
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
    # NOTE: This is a simplified implementation
    # For full cut export, use the core farfield module directly
    from ..core.farfield import _build_farfield_cut_export_command
    from ..core.modeling import add_to_history

    if not export_dir:
        from pathlib import Path
        export_dir = str(Path(project_path).parent.parent / "exports")

    from pathlib import Path
    output_file = str(Path(export_dir) / "farfield_cut.txt")

    vba = _build_farfield_cut_export_command(tree_path, output_file)
    result = add_to_history(project_path, vba, f"Export farfield cut: {tree_path}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to export farfield cut"))

    return {
        "status": "success",
        "tree_path": tree_path,
        "output_file": output_file,
    }


def list_monitors(project_path: str) -> list[str]:
    """List farfield monitors.

    Args:
        project_path: Path to .cst file

    Returns:
        List of farfield monitor names
    """
    result = _discover_farfield_monitors(project_path)
    if result.get("status") == "error":
        return []
    return result.get("farfield_names", [])
