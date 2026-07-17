"""MCP Tool definitions: CST Geometry operations."""
from typing import Any

from ..proxy import call_cst


def define_brick(
    project_path: str, component: str, name: str, material: str,
    x_range: tuple[float, float], y_range: tuple[float, float], z_range: tuple[float, float]
) -> dict[str, Any]:
    """[WRITE] Create a 3D brick solid.

    Args:
        project_path: Absolute path to the .cst file.
        component: Target component folder name (e.g. 'component1').
        name: Name of the new solid.
        material: Material name.
        x_range: A tuple of (xmin, xmax).
        y_range: A tuple of (ymin, ymax).
        z_range: A tuple of (zmin, zmax).
    """
    return call_cst(
        "lib.geometry", "brick",
        project_path=project_path, component=component, name=name,
        material=material, xrange=x_range, yrange=y_range, zrange=z_range
    )

def boolean_add(project_path: str, shape1: str, shape2: str) -> dict[str, Any]:
    """[WRITE] Boolean Add two solids.

    Args:
        project_path: Absolute path to the .cst file.
        shape1: Name of the first solid (Format: 'Component:Shape').
        shape2: Name of the second solid to add.
    """
    return call_cst("lib.geometry", "boolean_add", project_path=project_path, shape1=shape1, shape2=shape2)

def boolean_subtract(project_path: str, target: str, tool: str) -> dict[str, Any]:
    """[WRITE] Boolean Subtract one solid from another.

    Args:
        project_path: Absolute path to the .cst file.
        target: Name of the solid to subtract FROM (Format: 'Component:Shape').
        tool: Name of the solid to subtract.
    """
    return call_cst("lib.geometry", "boolean_subtract", project_path=project_path, target=target, tool=tool)

GEOMETRY_TOOLS = [
    {"name": "define-brick", "handler": define_brick},
    {"name": "boolean-add", "handler": boolean_add},
    {"name": "boolean-subtract", "handler": boolean_subtract},
]
