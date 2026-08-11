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

from ..core.modeling import define_floquet_port as _define_floquet_port
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

    待完善：当前实现仅覆盖部分初始化和历史需求，尚未完整核对 CST 2022
    的高级极化、模式列表、参考面与扫描角组合。调用成功不代表完整的
    Floquet 配置已经完成；高级需求应由用户在 CST 图形界面中手动设置。

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
    result = _define_floquet_port(
        project_path,
        zmin_modes=zmin_modes,
        zmax_modes=zmax_modes,
        zmin_reference_distance=zmin_reference_distance,
        zmax_reference_distance=zmax_reference_distance,
        polarization_type=polarization_type,
    )
    if result.get("status") == "error":
        raise_result_error(result, "Failed to define Floquet port")


define_waveguide = wrap_public(define_waveguide)
define_floquet = wrap_public(define_floquet)
