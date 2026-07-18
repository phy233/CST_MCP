"""MCP Tool definitions: CST Farfield operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def export_grid(project_path: str, farfield_name: str, export_dir: str, quantity: str = 'Realized Gain', theta_step_deg: float = 1.0, phi_step_deg: float = 2.0, run_id: int | None = None) -> dict[str, Any]:
    """
    Export farfield grid data.

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
    return call_cst("lib.farfield", "export_grid", project_path=project_path, farfield_name=farfield_name, export_dir=export_dir, quantity=quantity, theta_step_deg=theta_step_deg, phi_step_deg=phi_step_deg, run_id=run_id)

def export_cut(project_path: str, tree_path: str, export_dir: str = '') -> dict[str, Any]:
    """
    Export farfield cut data.

    Args:
        project_path: Path to .cst file
        tree_path: Farfield cut tree path
        export_dir: Export directory

    Returns:
        Dict with export information

    Raises:
        RuntimeError: If export fails
    """
    return call_cst("lib.farfield", "export_cut", project_path=project_path, tree_path=tree_path, export_dir=export_dir)

def list_monitors(project_path: str) -> dict[str, Any]:
    """
    List farfield monitors.

    Args:
        project_path: Path to .cst file

    Returns:
        List of farfield monitor names
    """
    return call_cst("lib.farfield", "list_monitors", project_path=project_path)

FARFIELD_TOOLS = [
    {"name": "export-grid", "handler": export_grid},
    {"name": "export-cut", "handler": export_cut},
    {"name": "list-monitors", "handler": list_monitors},
]
