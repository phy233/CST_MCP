"""CST array modeling operations.

Usage:
    from cst_runtime.lib.array import build_coding_array, fast_array

    # Build a coding metasurface array
    build_coding_array("C:\\path\\to\\model.cst",
                       coding_matrix=[[0, 1], [1, 0]],
                       unit_type="c_ring",
                       dx=10, dy=10)

    # Fast array using template copy
    fast_array("C:\\path\\to\\model.cst",
               template_component="unit_cell",
               positions=[(0, 0, 0), (10, 0, 0), (0, 10, 0), (10, 10, 0)])
"""
from __future__ import annotations

from typing import Any, Sequence

from ..core.modeling import add_to_history as _add_to_history
from .geometry import translate as _translate
from .geometry import activate_wcs as _activate_wcs
from .geometry import deactivate_wcs as _deactivate_wcs


def build_coding_array(
    project_path: str,
    coding_matrix: list[list[int]],
    unit_type: str,
    dx: float,
    dy: float,
    layer_distance: float = 0,
    template_name: str = "unit",
) -> None:
    """Build a coding metasurface array from a coding matrix.

    Args:
        project_path: Path to .cst file
        coding_matrix: 2D matrix of unit cell codes (e.g., [[0,1],[1,0]])
        unit_type: Unit cell geometry type ("c_ring", "cross", "custom")
        dx: Unit cell spacing X (mm)
        dy: Unit cell spacing Y (mm)
        layer_distance: Z offset between layers (mm)
        template_name: Template component name

    Raises:
        RuntimeError: If array cannot be built
    """
    if not coding_matrix or not coding_matrix[0]:
        raise ValueError("coding_matrix cannot be empty")

    rows = len(coding_matrix)
    cols = len(coding_matrix[0])

    # NOTE: This is a simplified implementation
    # For full array modeling, use the unit_cells module
    for i in range(rows):
        for j in range(cols):
            code = coding_matrix[i][j]
            x = j * dx
            y = i * dy
            z = 0

            # Create unit cell at position
            # This is a placeholder - actual implementation depends on unit_type
            vba = f"""' Array unit ({i},{j}), code={code}
' Position: ({x}, {y}, {z})
' Unit type: {unit_type}"""
            _add_to_history(project_path, vba, f"Array unit ({i},{j})")


def fast_array(
    project_path: str,
    template_component: str,
    positions: Sequence[tuple[float, float, float]],
    destination_component: str = "",
) -> None:
    """Create array by copying a template to multiple positions.

    Args:
        project_path: Path to .cst file
        template_component: Template component name to copy
        positions: List of (x, y, z) positions for copies
        destination_component: Destination component (default: same as template)

    Raises:
        RuntimeError: If array cannot be created
    """
    if not positions:
        raise ValueError("positions cannot be empty")

    for idx, (x, y, z) in enumerate(positions):
        # Use Transform.Translate to copy template
        _translate(
            project_path,
            name=f"{template_component}:*",
            vector=(x, y, z),
            multiple_objects=True,
            repetitions=1,
            destination=destination_component or template_component,
        )


def build_rectangular_array(
    project_path: str,
    template_component: str,
    nx: int,
    ny: int,
    dx: float,
    dy: float,
    origin: tuple[float, float, float] = (0, 0, 0),
) -> None:
    """Build a rectangular array from a template.

    Args:
        project_path: Path to .cst file
        template_component: Template component name
        nx: Number of elements in X
        ny: Number of elements in Y
        dx: Spacing in X (mm)
        dy: Spacing in Y (mm)
        origin: Array origin (x, y, z)

    Raises:
        RuntimeError: If array cannot be built
    """
    positions = []
    for i in range(ny):
        for j in range(nx):
            x = origin[0] + j * dx
            y = origin[1] + i * dy
            z = origin[2]
            positions.append((x, y, z))

    fast_array(project_path, template_component, positions)
