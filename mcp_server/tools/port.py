"""MCP Tool definitions: CST Port operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def define_waveguide(project_path: str, port_number: int = 1, face: str = 'zmax', width: float | None = None, height: float | None = None) -> dict[str, Any]:
    """
    Define a waveguide port.

    Args:
        project_path: Path to .cst file
        port_number: Port number
        face: Port face ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")
        width: Port width (optional, auto-calculated if None)
        height: Port height (optional, auto-calculated if None)

    Raises:
        RuntimeError: If port cannot be defined

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.port", "define_waveguide", project_path=project_path, port_number=port_number, face=face, width=width, height=height)

def define_floquet(project_path: str, zmin_modes: int = 1, zmax_modes: int = 1, zmin_reference_distance: float = 0, zmax_reference_distance: float = 0, polarization_type: str = 'linear') -> dict[str, Any]:
    """
    Define Floquet ports for periodic/metasurface simulation.

    Args:
        project_path: Path to .cst file
        zmin_modes: Number of modes at zmin port
        zmax_modes: Number of modes at zmax port
        zmin_reference_distance: Reference distance at zmin (mm)
        zmax_reference_distance: Reference distance at zmax (mm)
        polarization_type: Polarization type ("linear" or "circular")

    Raises:
        RuntimeError: If Floquet port cannot be defined

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.port", "define_floquet", project_path=project_path, zmin_modes=zmin_modes, zmax_modes=zmax_modes, zmin_reference_distance=zmin_reference_distance, zmax_reference_distance=zmax_reference_distance, polarization_type=polarization_type)

PORT_TOOLS = [
    {"name": "define-waveguide", "handler": define_waveguide},
    {"name": "define-floquet", "handler": define_floquet},
]
