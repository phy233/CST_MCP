"""CST geometry modeling operations.

Usage:
    from cst_runtime.lib.geometry import brick, cylinder, boolean_subtract

    # Create a brick
    brick("C:\\path\\to\\model.cst",
          component="component1",
          name="patch",
          material="PEC",
          x_range=(-5, 5), y_range=(-5, 5), z_range=(0, 0.1))

    # Create a cylinder
    cylinder("C:\\path\\to\\model.cst",
             component="component1",
             name="via",
             material="Copper",
             axis="z",
             center=(0, 0),
             radius=0.5,
             z_range=(0, 1))

    # Boolean subtract
    boolean_subtract("C:\\path\\to\\model.cst",
                     target="component1:outer",
                     tool="component1:inner")
"""
from __future__ import annotations

from typing import Any, Sequence

from ..core.modeling import define_brick as _define_brick
from ..core.modeling import define_cylinder as _define_cylinder
from ..core.modeling import define_cone as _define_cone
from ..core.modeling import define_rectangle as _define_rectangle
from ..core.modeling import boolean_subtract as _boolean_subtract
from ..core.modeling import boolean_add as _boolean_add
from ..core.modeling import boolean_intersect as _boolean_intersect
from ..core.modeling import boolean_insert as _boolean_insert
from ..core.modeling import delete_entity as _delete_entity
from ..core.modeling import create_component as _create_component
from ..core.modeling import change_material as _change_material
from ..core.modeling import transform_shape as _transform_shape
from ..core.modeling import add_to_history as _add_to_history


def brick(
    project_path: str,
    component: str,
    name: str,
    material: str,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    z_range: tuple[float, float],
) -> None:
    """Create a brick solid.

    Args:
        project_path: Path to .cst file
        component: Component name
        name: Solid name
        material: Material name
        x_range: (min, max) x coordinates
        y_range: (min, max) y coordinates
        z_range: (min, max) z coordinates

    Raises:
        RuntimeError: If brick cannot be created
    """
    result = _define_brick(
        project_path, name, component, material,
        x_range[0], x_range[1], y_range[0], y_range[1], z_range[0], z_range[1]
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create brick"))


def cylinder(
    project_path: str,
    component: str,
    name: str,
    material: str,
    axis: str,
    center: tuple[float, float],
    radius: float,
    z_range: tuple[float, float],
    inner_radius: float = 0.0,
) -> None:
    """Create a cylinder solid.

    Args:
        project_path: Path to .cst file
        component: Component name
        name: Solid name
        material: Material name
        axis: Axis direction ("x", "y", or "z")
        center: (x, y) center coordinates
        radius: Outer radius
        z_range: (min, max) range along axis
        inner_radius: Inner radius (default 0 for solid)

    Raises:
        RuntimeError: If cylinder cannot be created
    """
    result = _define_cylinder(
        project_path, name, component, material,
        radius, inner_radius, axis,
        z_range[0], z_range[1], center[0], center[1]
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create cylinder"))


def cone(
    project_path: str,
    component: str,
    name: str,
    material: str,
    axis: str,
    center: tuple[float, float],
    bottom_radius: float,
    top_radius: float,
    z_range: tuple[float, float],
) -> None:
    """Create a cone solid.

    Args:
        project_path: Path to .cst file
        component: Component name
        name: Solid name
        material: Material name
        axis: Axis direction ("x", "y", or "z")
        center: (x, y) center coordinates
        bottom_radius: Bottom radius
        top_radius: Top radius
        z_range: (min, max) range along axis

    Raises:
        RuntimeError: If cone cannot be created
    """
    result = _define_cone(
        project_path, name, component, material,
        bottom_radius, top_radius, axis,
        z_range[0], z_range[1], center[0], center[1]
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create cone"))


def rectangle(
    project_path: str,
    curve: str,
    name: str,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
) -> None:
    """Create a rectangle curve.

    Args:
        project_path: Path to .cst file
        curve: Curve name
        name: Rectangle name
        x_range: (min, max) x coordinates
        y_range: (min, max) y coordinates

    Raises:
        RuntimeError: If rectangle cannot be created
    """
    result = _define_rectangle(
        project_path, name, curve,
        x_range[0], x_range[1], y_range[0], y_range[1]
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create rectangle"))


def boolean_add(project_path: str, shape1: str, shape2: str) -> None:
    """Boolean add two solids.

    Args:
        project_path: Path to .cst file
        shape1: First shape (component:name)
        shape2: Second shape (component:name)

    Raises:
        RuntimeError: If boolean operation fails
    """
    result = _boolean_add(project_path, shape1, shape2)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to boolean add"))


def boolean_subtract(project_path: str, target: str, tool: str) -> None:
    """Boolean subtract.

    Args:
        project_path: Path to .cst file
        target: Target shape (component:name)
        tool: Tool shape to subtract (component:name)

    Raises:
        RuntimeError: If boolean operation fails
    """
    result = _boolean_subtract(project_path, target, tool)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to boolean subtract"))


def boolean_intersect(project_path: str, shape1: str, shape2: str) -> None:
    """Boolean intersect two solids.

    Args:
        project_path: Path to .cst file
        shape1: First shape (component:name)
        shape2: Second shape (component:name)

    Raises:
        RuntimeError: If boolean operation fails
    """
    result = _boolean_intersect(project_path, shape1, shape2)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to boolean intersect"))


def delete_entity(project_path: str, name: str, component: str = "") -> None:
    """Delete a solid entity.

    Args:
        project_path: Path to .cst file
        name: Solid name
        component: Component name (optional, can include in name as "component:name")

    Raises:
        RuntimeError: If entity cannot be deleted
    """
    if component:
        full_name = f"{component}:{name}"
    else:
        full_name = name
    result = _delete_entity(project_path, component or "", name)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to delete entity"))


def delete_component(project_path: str, component: str) -> None:
    """Delete an entire component folder and all solids within it.

    Args:
        project_path: Path to .cst file
        component: Component name to delete

    Raises:
        RuntimeError: If component cannot be deleted
    """
    vba = f'Component.Delete "{component}"'
    result = _add_to_history(project_path, vba, f"Delete component: {component}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to delete component"))


def rotate(
    project_path: str,
    name: str,
    center: tuple[float, float, float] = (0, 0, 0),
    angle: tuple[float, float, float] = (0, 0, 0),
    multiple_objects: bool = True,
    repetitions: int = 1,
) -> None:
    """Rotate a solid.

    Args:
        project_path: Path to .cst file
        name: Solid name
        center: (x, y, z) rotation center
        angle: (x, y, z) rotation angles in degrees
        multiple_objects: Whether to copy objects
        repetitions: Number of copies

    Raises:
        RuntimeError: If rotation fails
    """
    result = _transform_shape(
        project_path, name, "rotate",
        center_x=str(center[0]), center_y=str(center[1]), center_z=str(center[2]),
        angle_x=str(angle[0]), angle_y=str(angle[1]), angle_z=str(angle[2]),
        multiple_objects=multiple_objects, repetitions=repetitions
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to rotate"))


def translate(
    project_path: str,
    name: str,
    vector: tuple[float, float, float],
    multiple_objects: bool = True,
    repetitions: int = 1,
    destination: str = "",
) -> None:
    """Translate (move) a solid.

    Args:
        project_path: Path to .cst file
        name: Solid name
        vector: (x, y, z) translation vector
        multiple_objects: Whether to copy objects
        repetitions: Number of copies
        destination: Destination component

    Raises:
        RuntimeError: If translation fails
    """
    # NOTE: CST 2026 feature - transform_shape needs to be extended to support "translate"
    # Currently this is a placeholder that constructs VBA directly
    vba = [
        "With Transform",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Vector "{vector[0]}", "{vector[1]}", "{vector[2]}"',
        f'    .MultipleObjects "{"True" if multiple_objects else "False"}"',
        f'    .Repetitions "{repetitions}"',
        f'    .Destination "{destination}"',
        '    .Transform "Shape", "Translate"',
        "End With",
    ]
    result = _add_to_history(project_path, "\n".join(vba), f"Translate: {name}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to translate"))


def mirror(
    project_path: str,
    name: str,
    plane_normal: tuple[float, float, float] = (0, 1, 0),
    center: tuple[float, float, float] = (0, 0, 0),
) -> None:
    """Mirror a solid.

    Args:
        project_path: Path to .cst file
        name: Solid name
        plane_normal: (x, y, z) mirror plane normal
        center: (x, y, z) mirror center

    Raises:
        RuntimeError: If mirroring fails
    """
    result = _transform_shape(
        project_path, name, "mirror",
        center_x=str(center[0]), center_y=str(center[1]), center_z=str(center[2]),
        plane_normal_x=str(plane_normal[0]), plane_normal_y=str(plane_normal[1]),
        plane_normal_z=str(plane_normal[2])
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to mirror"))


def activate_wcs(
    project_path: str,
    name: str,
    origin: tuple[float, float, float],
    normal: tuple[float, float, float] = (0, 0, 1),
    uvector: tuple[float, float, float] = (1, 0, 0),
) -> None:
    """Activate a local working coordinate system (WCS).

    Args:
        project_path: Path to .cst file
        name: WCS name
        origin: (x, y, z) WCS origin
        normal: (x, y, z) WCS normal direction
        uvector: (x, y, z) WCS U-vector direction

    Raises:
        RuntimeError: If WCS cannot be activated
    """
    vba = f"""With WCS
    .ActivateWCS "local"
    .SetOrigin {origin[0]}, {origin[1]}, {origin[2]}
    .SetNormal {normal[0]}, {normal[1]}, {normal[2]}
    .SetUVector {uvector[0]}, {uvector[1]}, {uvector[2]}
    .SetName "{name}"
End With"""
    result = _add_to_history(project_path, vba, f"Activate WCS: {name}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to activate WCS"))


def deactivate_wcs(project_path: str) -> None:
    """Switch back to global WCS.

    Args:
        project_path: Path to .cst file

    Raises:
        RuntimeError: If WCS cannot be deactivated
    """
    vba = 'WCS.ActivateWCS "global"'
    result = _add_to_history(project_path, vba, "Deactivate WCS")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to deactivate WCS"))


def arc(
    project_path: str,
    name: str,
    center: tuple[float, float, float],
    radius: float,
    start_angle: float,
    end_angle: float,
    segments: int = 0,
    component: str = "component1",
) -> None:
    """Create an arc curve.

    Args:
        project_path: Path to .cst file
        name: Curve name
        center: (x, y, z) arc center
        radius: Arc radius
        start_angle: Start angle in degrees
        end_angle: End angle in degrees
        segments: Number of segments (0 for auto)
        component: Component name

    Raises:
        RuntimeError: If arc cannot be created
    """
    vba = f"""With Arc
    .Reset
    .Name "{name}"
    .Curve "{component}"
    .Center {center[0]}, {center[1]}, {center[2]}
    .Radius {radius}
    .StartAngle {start_angle}
    .EndAngle {end_angle}
    .Segments {segments}
    .Create
End With"""
    result = _add_to_history(project_path, vba, f"Define Arc: {name}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create arc"))


def polygon(
    project_path: str,
    name: str,
    component: str,
    material: str,
    vertices: Sequence[tuple[float, float]],
    z_range: tuple[float, float],
) -> None:
    """Create a polygon solid from vertices.

    Args:
        project_path: Path to .cst file
        name: Solid name
        component: Component name
        material: Material name
        vertices: List of (x, y) vertex coordinates
        z_range: (min, max) z coordinates

    Raises:
        RuntimeError: If polygon cannot be created
    """
    if len(vertices) < 3:
        raise ValueError("Polygon requires at least 3 vertices")

    vba_lines = [
        "With Polygon3D",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Component "{component}"',
        f'    .Material "{material}"',
    ]
    for i, (x, y) in enumerate(vertices):
        vba_lines.append(f'    .Point {x}, {y}, {z_range[0]}')
    for i, (x, y) in enumerate(reversed(vertices)):
        vba_lines.append(f'    .Point {x}, {y}, {z_range[1]}')
    vba_lines.extend([
        "    .Create",
        "End With",
    ])
    result = _add_to_history(project_path, "\n".join(vba_lines), f"Define Polygon: {name}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create polygon"))
