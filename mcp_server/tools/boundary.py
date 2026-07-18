"""MCP Tool definitions: CST Boundary operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def set_all(project_path: str, boundary_type: str = 'expanded open') -> dict[str, Any]:
    """
    Set all faces to same boundary type.

    Args:
        project_path: Path to .cst file
        boundary_type: Boundary type (e.g., "expanded open", "electric", "magnetic")

    Raises:
        RuntimeError: If boundary cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.boundary", "set_all", project_path=project_path, boundary_type=boundary_type)

def set_per_face(project_path: str, xmin: str = 'unit cell', xmax: str = 'unit cell', ymin: str = 'unit cell', ymax: str = 'unit cell', zmin: str = 'open', zmax: str = 'open', periodic_angle: float = 0) -> dict[str, Any]:
    """
    Set boundary conditions per face for unit cell / periodic simulations.

    Args:
        project_path: Path to .cst file
        xmin: Xmin face boundary type
        xmax: Xmax face boundary type
        ymin: Ymin face boundary type
        ymax: Ymax face boundary type
        zmin: Zmin face boundary type
        zmax: Zmax face boundary type
        periodic_angle: Periodic phase angle in degrees

    Raises:
        RuntimeError: If boundary cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.boundary", "set_per_face", project_path=project_path, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, zmin=zmin, zmax=zmax, periodic_angle=periodic_angle)

def set_unit_cell(project_path: str, periodic_angle: float = 0) -> dict[str, Any]:
    """
    Set unit cell boundary for periodic simulation.

    Args:
        project_path: Path to .cst file
        periodic_angle: Periodic phase angle in degrees

    Raises:
        RuntimeError: If boundary cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.boundary", "set_unit_cell", project_path=project_path, periodic_angle=periodic_angle)

BOUNDARY_TOOLS = [
    {"name": "set-all", "handler": set_all},
    {"name": "set-per-face", "handler": set_per_face},
    {"name": "set-unit-cell", "handler": set_unit_cell},
]
