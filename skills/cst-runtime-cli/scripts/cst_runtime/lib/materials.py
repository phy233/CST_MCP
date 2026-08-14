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
from ..core.project import list_materials as _list_materials
from ._facade import call_core
from .contracts import OperationResult, success_result


def define(
    project_path: str,
    name: str,
    epsilon: float = 1.0,
    mue: float = 1.0,
    tan_d: float = 0.0,
    tan_d_freq: float = 0.0,
    transparency: float = 0.0,
) -> OperationResult:
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
    .Mu {mue}
    .TanD {tan_d}
    .TanDFreq {tan_d_freq}
    .TanDGiven "True"
    .Transparency {transparency}
    .Create
End With"""
    return call_core(_add_to_history, project_path, vba, f"Define Material: {name}")


def define_from_mtd(project_path: str, material_name: str) -> OperationResult:
    """Load material from .mtd file.

    Args:
        project_path: Path to .cst file
        material_name: Material name (without .mtd extension)

    Raises:
        RuntimeError: If material cannot be loaded
    """
    return call_core(_define_material_from_mtd, project_path, material_name)


def list_materials(project_path: str) -> OperationResult:
    """List available materials.

    Args:
        project_path: Path to .cst file

    Returns:
        List of material names
    """
    return call_core(_list_materials, project_path)


def exists(project_path: str, name: str) -> OperationResult:
    """Check if material exists.

    Args:
        project_path: Path to .cst file
        name: Material name

    Returns:
        True if material exists
    """
    # NOTE: CST 2026 feature - Material.Exists() may not be available in CST 2022
    # Fallback: check if material is in the list
    result = list_materials(project_path)
    if result.get("status") == "error":
        return result
    return success_result(
        project_path=project_path,
        material=name,
        exists=name in result.get("items", []),
    )


def set_material(project_path: str, entity: str, material: str) -> OperationResult:
    """Modify entity material.

    Args:
        project_path: Path to .cst file
        entity: Entity name (component:name)
        material: Material name

    Raises:
        RuntimeError: If material cannot be set
    """
    return call_core(_change_material, project_path, entity, material)


def _abs_project_path(project_path: str) -> str:
    """Normalize project path to absolute path."""
    from pathlib import Path
    return str(Path(project_path).expanduser().resolve())
