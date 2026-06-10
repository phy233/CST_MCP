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

from ..core.modeling import add_to_history as _add_to_history


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
    vba_lines = [
        "With Port",
        "    .Reset",
        f'    .PortNumber "{port_number}"',
        f'    .SetNumberOfStimulatedModes "1"',
        f'    .SetPortType "Waveguide"',
        f'    .Face "{face}"',
    ]
    if width is not None:
        vba_lines.append(f'    .SetWaveguideWidth "{width}"')
    if height is not None:
        vba_lines.append(f'    .SetWaveguideHeight "{height}"')
    vba_lines.extend([
        '    .SetWaveguidePort "True"',
        '    .SetImpedance "50"',
        '    .SetFrequency "10"',
        '    .Create',
        "End With",
    ])
    result = _add_to_history(project_path, "\n".join(vba_lines), f"Define Waveguide Port {port_number}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to define waveguide port"))


def define_floquet(
    project_path: str,
    zmin_modes: int = 1,
    zmax_modes: int = 1,
    zmin_reference_distance: float = 0,
    zmax_reference_distance: float = 0,
    polarization_type: str = "linear",
) -> None:
    """Define Floquet ports for periodic/metasurface simulation.

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
    # NOTE: CST 2026 feature - Floquet port API
    # This implementation is based on CST 2026 VBA syntax
    # For CST 2022 compatibility, additional testing may be needed
    vba = f"""With Port
    .Reset
    .Floquet
    .SetDialogParameter "ZminModes", "{zmin_modes}"
    .SetDialogParameter "ZmaxModes", "{zmax_modes}"
    .SetDialogParameter "ZminReferenceDistance", "{zmin_reference_distance}"
    .SetDialogParameter "ZmaxReferenceDistance", "{zmax_reference_distance}"
    .SetDialogParameter "PolarizationType", "{polarization_type}"
    .CreateFloquetPort
End With"""
    result = _add_to_history(project_path, vba, "Define Floquet Port")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to define Floquet port"))
