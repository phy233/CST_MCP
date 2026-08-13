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
from ..core.em_setup import define_unit_cell_boundary as _define_unit_cell_boundary
from ..core.modeling import set_boundary_per_face as _set_boundary_per_face
from ._facade import wrap_public
from .contracts import raise_result_error


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
        raise_result_error(result, "Failed to set boundary")


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
    result = _set_boundary_per_face(
        project_path,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        zmin=zmin,
        zmax=zmax,
        periodic_angle=periodic_angle,
    )
    if result.get("status") == "error":
        raise_result_error(result, "Failed to set boundary per face")


def set_unit_cell(project_path: str, periodic_angle: float = 0) -> None:
    """Set unit cell boundary for periodic simulation.

    兼容映射：periodic_angle 作为 theta，phi=0，direction=outward。
    新代码需要独立 theta/phi 或传播方向时，应调用 em_setup 中的新接口。

    Args:
        project_path: Path to .cst file
        periodic_angle: Periodic phase angle in degrees

    Raises:
        RuntimeError: If boundary cannot be set
    """
    # 旧 periodic_angle 明确映射为 theta，phi 与方向使用兼容默认值。
    result = _define_unit_cell_boundary(
        project_path,
        xmin="unit cell",
        xmax="unit cell",
        ymin="unit cell",
        ymax="unit cell",
        zmin="open",
        zmax="open",
        theta=periodic_angle,
        phi=0.0,
        direction="outward",
    )
    if result.get("status") == "error":
        raise_result_error(result, "Failed to set unit cell boundary")


set_all = wrap_public(set_all)
set_per_face = wrap_public(set_per_face)
set_unit_cell = wrap_public(set_unit_cell)
