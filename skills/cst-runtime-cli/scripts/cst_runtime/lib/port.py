"""CST port configuration operations.

Usage:
    from cst_runtime.lib.port import define_waveguide, define_floquet

    # Define a waveguide port
    define_waveguide("C:\\path\\to\\model.cst",
                     port_number=1,
                     face="zmax")

    # Define Floquet ports for periodic/metasurface simulation
    define_floquet("C:\\path\\to\\model.cst",
                   zmin_modes=1,
                   zmax_modes=1,
                   polarization_type="linear")
"""
from __future__ import annotations

from typing import Any

from ..core.em_setup import define_floquet_port as _define_floquet_port
from ..core.modeling import define_waveguide_port as _define_waveguide_port
from ._facade import wrap_public
from .contracts import raise_result_error


def define_waveguide(
    project_path: str,
    port_number: int = 1,
    face: str = "zmax",
    width: float | None = None,
    height: float | None = None,
) -> None:
    """Define a waveguide port.

    Args:
        project_path: Path to .cst file
        port_number: Port number
        face: Port face ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")
        width: Port width (optional, auto-calculated if None)
        height: Port height (optional, auto-calculated if None)

    Raises:
        RuntimeError: If port cannot be defined
    """
    result = _define_waveguide_port(
        project_path,
        port_number=port_number,
        face=face,
        width=width,
        height=height,
    )
    if result.get("status") == "error":
        raise_result_error(result, "Failed to define waveguide port")


def define_floquet(
    project_path: str,
    zmin_modes: int = 1,
    zmax_modes: int = 1,
    zmin_reference_distance: float = 0,
    zmax_reference_distance: float = 0,
    polarization_type: str = "linear",
) -> None:
    """Define Floquet ports for periodic/metasurface simulation.

    兼容映射：两个端口使用 automatic 模式，旧模式数量作为
    modes_considered。显式模式、排序频率和扫描角应调用 em_setup 中的新接口。

    Args:
        project_path: Path to .cst file
        zmin_modes: Number of modes at zmin port
        zmax_modes: Number of modes at zmax port
        zmin_reference_distance: Reference distance at zmin (mm)
        zmax_reference_distance: Reference distance at zmax (mm)
        polarization_type: Polarization type ("linear" or "circular")

    Raises:
        RuntimeError: If Floquet port cannot be defined
    """
    # 旧接口映射为两个 automatic 端口，不再按模式数量猜测固定模式表。
    result = _define_floquet_port(
        project_path,
        ports=[
            {
                "position": "Zmin",
                "mode_strategy": "automatic",
                "modes": [],
                "modes_considered": zmin_modes,
                "reference_distance": zmin_reference_distance,
            },
            {
                "position": "Zmax",
                "mode_strategy": "automatic",
                "modes": [],
                "modes_considered": zmax_modes,
                "reference_distance": zmax_reference_distance,
            },
        ],
        polarization_basis=polarization_type,
    )
    if result.get("status") == "error":
        raise_result_error(result, "Failed to define Floquet port")


define_waveguide = wrap_public(define_waveguide)
define_floquet = wrap_public(define_floquet)
