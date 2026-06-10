"""CST material management.

Usage:
    from cst_runtime.lib.materials import define, define_from_mtd, list_materials

    # Define a material
    define("C:\\path\\to\\model.cst",
           name="FR4",
           epsilon=4.3,
           mue=1.0,
           tan_d=0.02)

    # Load material from .mtd file
    define_from_mtd("C:\\path\\to\\model.cst",
                    "Copper (pure)")

    # List available materials
    materials = list_materials("C:\\path\\to\\model.cst")
"""
from __future__ import annotations

from typing import Any

from ..core.modeling import define_material_from_mtd as _define_material_from_mtd
from ..core.modeling import change_material as _change_material
from ..core.modeling import add_to_history as _add_to_history
from ..core.identity import attach_expected_project


def define(
    project_path: str,
    name: str,
    epsilon: float = 1.0,
    mue: float = 1.0,
    tan_d: float = 0.0,
    tan_d_freq: float = 0.0,
    transparency: float = 0.0,
) -> None:
    """Create a material with inline properties.

    Args:
        project_path: Path to .cst file
        name: Material name
        epsilon: Relative permittivity
        mue: Relative permeability
        tan_d: Dielectric loss tangent
        tan_d_freq: Frequency for loss tangent (GHz)
        transparency: Transparency (0-1)

    Raises:
        RuntimeError: If material cannot be defined
    """
    vba = f"""With Material
    .Reset
    .Name "{name}"
    .Epsilon {epsilon}
    .Mue {mue}
    .TanD {tan_d}
    .TanDFreq {tan_d_freq}
    .TanDGiven "True"
    .Transparency {transparency}
    .Create
End With"""
    result = _add_to_history(project_path, vba, f"Define Material: {name}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to define material"))


def define_from_mtd(project_path: str, material_name: str) -> None:
    """Load material from .mtd file.

    Args:
        project_path: Path to .cst file
        material_name: Material name (without .mtd extension)

    Raises:
        RuntimeError: If material cannot be loaded
    """
    result = _define_material_from_mtd(project_path, material_name)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to load material from MTD"))


def list_materials(project_path: str) -> list[str]:
    """List available materials.

    Args:
        project_path: Path to .cst file

    Returns:
        List of material names
    """
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return []
    try:
        # CST does not have a direct API to list all materials
        # We can get materials from the tree items
        tree_items = project.modeler.get_tree_items()
        materials = []
        for item in tree_items:
            if str(item).startswith("Materials\\"):
                mat_name = str(item).split("\\")[-1]
                if mat_name not in materials:
                    materials.append(mat_name)
        return materials
    except Exception:
        return []


def exists(project_path: str, name: str) -> bool:
    """Check if material exists.

    Args:
        project_path: Path to .cst file
        name: Material name

    Returns:
        True if material exists
    """
    # NOTE: CST 2026 feature - Material.Exists() may not be available in CST 2022
    # Fallback: check if material is in the list
    try:
        materials = list_materials(project_path)
        return name in materials
    except Exception:
        return False


def set_material(project_path: str, entity: str, material: str) -> None:
    """Modify entity material.

    Args:
        project_path: Path to .cst file
        entity: Entity name (component:name)
        material: Material name

    Raises:
        RuntimeError: If material cannot be set
    """
    result = _change_material(project_path, entity, material)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set material"))


def _abs_project_path(project_path: str) -> str:
    """Normalize project path to absolute path."""
    from pathlib import Path
    return str(Path(project_path).expanduser().resolve())
