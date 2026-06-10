"""CST boundary condition operations.

Usage:
    from cst_runtime.lib.boundary import set_all, set_per_face, set_unit_cell

    # Set all faces to same boundary type
    set_all("C:\\path\\to\\model.cst", boundary_type="expanded open")

    # Set boundary per face for unit cell simulation
    set_per_face("C:\\path\\to\\model.cst",
                 xmin="unit cell", xmax="unit cell",
                 ymin="unit cell", ymax="unit cell",
                 zmin="open", zmax="open")

    # Set unit cell boundary
    set_unit_cell("C:\\path\\to\\model.cst", periodic_angle=0)
"""
from __future__ import annotations

from typing import Any

from ..core.modeling import define_boundary as _define_boundary
from ..core.modeling import add_to_history as _add_to_history


def set_all(project_path: str, boundary_type: str = "expanded open") -> None:
    """Set all faces to same boundary type.

    Args:
        project_path: Path to .cst file
        boundary_type: Boundary type (e.g., "expanded open", "electric", "magnetic")

    Raises:
        RuntimeError: If boundary cannot be set
    """
    result = _define_boundary(project_path, face_type=boundary_type)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set boundary"))


def set_per_face(
    project_path: str,
    xmin: str = "unit cell",
    xmax: str = "unit cell",
    ymin: str = "unit cell",
    ymax: str = "unit cell",
    zmin: str = "open",
    zmax: str = "open",
    periodic_angle: float = 0,
) -> None:
    """Set boundary conditions per face for unit cell / periodic simulations.

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
    """
    vba = f"""With Boundary
    .Xmin "{xmin}"
    .Xmax "{xmax}"
    .Ymin "{ymin}"
    .Ymax "{ymax}"
    .Zmin "{zmin}"
    .Zmax "{zmax}"
    .ApplyInAllDirections "False"
    .PeriodicUsePrimitive "False"
    .SetPeriodicShiftAngle "True", "{periodic_angle}"
End With"""
    result = _add_to_history(project_path, vba, "Define Boundary Per Face")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set boundary per face"))


def set_unit_cell(project_path: str, periodic_angle: float = 0) -> None:
    """Set unit cell boundary for periodic simulation.

    Args:
        project_path: Path to .cst file
        periodic_angle: Periodic phase angle in degrees

    Raises:
        RuntimeError: If boundary cannot be set
    """
    set_per_face(
        project_path,
        xmin="unit cell",
        xmax="unit cell",
        ymin="unit cell",
        ymax="unit cell",
        zmin="open",
        zmax="open",
        periodic_angle=periodic_angle,
    )
