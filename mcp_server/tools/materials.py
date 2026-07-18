"""MCP Tool definitions: CST Materials operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def define(project_path: str, name: str, epsilon: float = 1.0, mue: float = 1.0, tan_d: float = 0.0, tan_d_freq: float = 0.0, transparency: float = 0.0) -> dict[str, Any]:
    """
    Create a material with inline properties.

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

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.materials", "define", project_path=project_path, name=name, epsilon=epsilon, mue=mue, tan_d=tan_d, tan_d_freq=tan_d_freq, transparency=transparency)

def define_from_mtd(project_path: str, material_name: str) -> dict[str, Any]:
    """
    Load material from .mtd file.

    Args:
        project_path: Path to .cst file
        material_name: Material name (without .mtd extension)

    Raises:
        RuntimeError: If material cannot be loaded

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.materials", "define_from_mtd", project_path=project_path, material_name=material_name)

def list_materials(project_path: str) -> dict[str, Any]:
    """
    List available materials.

    Args:
        project_path: Path to .cst file

    Returns:
        List of material names
    """
    return call_cst("lib.materials", "list_materials", project_path=project_path)

def exists(project_path: str, name: str) -> dict[str, Any]:
    """
    Check if material exists.

    Args:
        project_path: Path to .cst file
        name: Material name

    Returns:
        True if material exists
    """
    return call_cst("lib.materials", "exists", project_path=project_path, name=name)

def set_material(project_path: str, entity: str, material: str) -> dict[str, Any]:
    """
    Modify entity material.

    Args:
        project_path: Path to .cst file
        entity: Entity name (component:name)
        material: Material name

    Raises:
        RuntimeError: If material cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.materials", "set_material", project_path=project_path, entity=entity, material=material)

MATERIALS_TOOLS = [
    {"name": "define", "handler": define},
    {"name": "define-from-mtd", "handler": define_from_mtd},
    {"name": "list-materials", "handler": list_materials},
    {"name": "exists", "handler": exists},
    {"name": "set-material", "handler": set_material},
]
