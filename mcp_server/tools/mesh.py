"""MCP Tool definitions: CST Mesh operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def settings(project_path: str, steps_per_wave_near: int = 5, steps_per_wave_far: int = 5, steps_per_box_near: int = 5, steps_per_box_far: int = 1, edge_refinement_ratio: int = 2, edge_refinement_buffer_lines: int = 3, ratio_limit_geometry: int = 10, equilibrate_value: float = 1.5, use_gpu: bool = True) -> dict[str, Any]:
    """
    Configure mesh settings.

    Args:
        project_path: Path to .cst file
        steps_per_wave_near: Steps per wavelength near field
        steps_per_wave_far: Steps per wavelength far field
        steps_per_box_near: Steps per box near field
        steps_per_box_far: Steps per box far field
        edge_refinement_ratio: Edge refinement ratio
        edge_refinement_buffer_lines: Edge refinement buffer lines
        ratio_limit_geometry: Geometry ratio limit
        equilibrate_value: Equilibrate value
        use_gpu: Whether to use GPU

    Raises:
        RuntimeError: If mesh settings cannot be configured

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.mesh", "settings", project_path=project_path, steps_per_wave_near=steps_per_wave_near, steps_per_wave_far=steps_per_wave_far, steps_per_box_near=steps_per_box_near, steps_per_box_far=steps_per_box_far, edge_refinement_ratio=edge_refinement_ratio, edge_refinement_buffer_lines=edge_refinement_buffer_lines, ratio_limit_geometry=ratio_limit_geometry, equilibrate_value=equilibrate_value, use_gpu=use_gpu)

def acceleration(project_path: str, use_parallelization: bool = True, max_threads: int = 1024, max_cpu_devices: int = 2, use_distributed: bool = False, max_distributed_ports: int = 64, hardware_accel: bool = True, max_gpus: int = 4) -> dict[str, Any]:
    """
    Configure solver acceleration.

    Args:
        project_path: Path to .cst file
        use_parallelization: Whether to use parallelization
        max_threads: Maximum number of threads
        max_cpu_devices: Maximum number of CPU devices
        use_distributed: Whether to use distributed computing
        max_distributed_ports: Maximum distributed computing ports
        hardware_accel: Whether to use hardware acceleration
        max_gpus: Maximum number of GPUs

    Raises:
        RuntimeError: If acceleration cannot be configured

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.mesh", "acceleration", project_path=project_path, use_parallelization=use_parallelization, max_threads=max_threads, max_cpu_devices=max_cpu_devices, use_distributed=use_distributed, max_distributed_ports=max_distributed_ports, hardware_accel=hardware_accel, max_gpus=max_gpus)

def set_fpbavoid_nonreg_unite(project_path: str, enable: bool = True) -> dict[str, Any]:
    """
    Set FPBA avoid non-reg unite option.

    Args:
        project_path: Path to .cst file
        enable: Whether to enable

    Raises:
        RuntimeError: If option cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.mesh", "set_fpbavoid_nonreg_unite", project_path=project_path, enable=enable)

def set_minimum_step_number(project_path: str, num_steps: int = 5) -> dict[str, Any]:
    """
    Set minimum step number.

    Args:
        project_path: Path to .cst file
        num_steps: Minimum number of steps

    Raises:
        RuntimeError: If option cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.mesh", "set_minimum_step_number", project_path=project_path, num_steps=num_steps)

MESH_TOOLS = [
    {"name": "settings", "handler": settings},
    {"name": "acceleration", "handler": acceleration},
    {"name": "set-fpbavoid-nonreg-unite", "handler": set_fpbavoid_nonreg_unite},
    {"name": "set-minimum-step-number", "handler": set_minimum_step_number},
]
