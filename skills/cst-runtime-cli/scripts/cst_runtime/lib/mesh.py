"""CST mesh settings operations.

Usage:
    from cst_runtime.lib.mesh import settings, acceleration

    # Configure mesh settings
    settings("C:\\path\\to\\model.cst",
             steps_per_wave_near=10,
             steps_per_wave_far=5)

    # Configure solver acceleration
    acceleration("C:\\path\\to\\model.cst",
                 use_parallelization=True,
                 max_threads=16)
"""
from __future__ import annotations

from typing import Any

from ..core.modeling import define_mesh as _define_mesh
from ..core.simulation import set_solver_acceleration as _set_solver_acceleration
from ..core.simulation import set_mesh_fpbavoid_nonreg_unite as _set_mesh_fpbavoid_nonreg_unite
from ..core.simulation import set_mesh_minimum_step_number as _set_mesh_minimum_step_number


def settings(
    project_path: str,
    steps_per_wave_near: int = 5,
    steps_per_wave_far: int = 5,
    steps_per_box_near: int = 5,
    steps_per_box_far: int = 1,
    edge_refinement_ratio: int = 2,
    edge_refinement_buffer_lines: int = 3,
    ratio_limit_geometry: int = 10,
    equilibrate_value: float = 1.5,
    use_gpu: bool = True,
) -> None:
    """Configure mesh settings.

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
    """
    result = _define_mesh(
        project_path,
        steps_per_wave_near=steps_per_wave_near,
        steps_per_wave_far=steps_per_wave_far,
        steps_per_box_near=steps_per_box_near,
        steps_per_box_far=steps_per_box_far,
        edge_refinement_ratio=edge_refinement_ratio,
        edge_refinement_buffer_lines=edge_refinement_buffer_lines,
        ratio_limit_geometry=ratio_limit_geometry,
        equilibrate_value=equilibrate_value,
        use_gpu=use_gpu,
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to configure mesh settings"))


def acceleration(
    project_path: str,
    use_parallelization: bool = True,
    max_threads: int = 1024,
    max_cpu_devices: int = 2,
    use_distributed: bool = False,
    max_distributed_ports: int = 64,
    hardware_accel: bool = True,
    max_gpus: int = 4,
) -> None:
    """Configure solver acceleration.

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
    """
    result = _set_solver_acceleration(
        project_path,
        use_parallelization=use_parallelization,
        max_threads=max_threads,
        max_cpu_devices=max_cpu_devices,
        use_distributed=use_distributed,
        max_distributed_ports=max_distributed_ports,
        hardware_accel=hardware_accel,
        max_gpus=max_gpus,
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to configure acceleration"))


def set_fpbavoid_nonreg_unite(project_path: str, enable: bool = True) -> None:
    """Set FPBA avoid non-reg unite option.

    Args:
        project_path: Path to .cst file
        enable: Whether to enable

    Raises:
        RuntimeError: If option cannot be set
    """
    result = _set_mesh_fpbavoid_nonreg_unite(project_path, enable)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set FPBA option"))


def set_minimum_step_number(project_path: str, num_steps: int = 5) -> None:
    """Set minimum step number.

    Args:
        project_path: Path to .cst file
        num_steps: Minimum number of steps

    Raises:
        RuntimeError: If option cannot be set
    """
    result = _set_mesh_minimum_step_number(project_path, num_steps)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set minimum step number"))
