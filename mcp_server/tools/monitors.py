"""MCP Tool definitions: CST Monitors operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def set_farfield(project_path: str, start_freq: float, end_freq: float, step: float = 1, subvolume: tuple[float, float, float, float, float, float] | None = None, enable_nearfield: bool = True) -> dict[str, Any]:
    """
    Set farfield monitor.

    Args:
        project_path: Path to .cst file
        start_freq: Start frequency in GHz
        end_freq: End frequency in GHz
        step: Frequency step in GHz
        subvolume: Optional (xmin, xmax, ymin, ymax, zmin, zmax) subvolume
        enable_nearfield: Whether to enable nearfield calculation

    Raises:
        RuntimeError: If monitor cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.monitors", "set_farfield", project_path=project_path, start_freq=start_freq, end_freq=end_freq, step=step, subvolume=subvolume, enable_nearfield=enable_nearfield)

def set_efield(project_path: str, start_freq: float, end_freq: float, step: float = 1, dimension: str = 'Volume', subvolume: tuple[float, float, float, float, float, float] | None = None) -> dict[str, Any]:
    """
    Set E-field monitor.

    Args:
        project_path: Path to .cst file
        start_freq: Start frequency in GHz
        end_freq: End frequency in GHz
        step: Frequency step in GHz
        dimension: Dimension type ("Volume", "Surface", etc.)
        subvolume: Optional (xmin, xmax, ymin, ymax, zmin, zmax) subvolume

    Raises:
        RuntimeError: If monitor cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.monitors", "set_efield", project_path=project_path, start_freq=start_freq, end_freq=end_freq, step=step, dimension=dimension, subvolume=subvolume)

def set_field(project_path: str, field_type: str, start_freq: str, end_freq: str, num_samples: str) -> dict[str, Any]:
    """
    Set generic field monitor.

    Args:
        project_path: Path to .cst file
        field_type: Field type ("E", "H", "Power", etc.)
        start_freq: Start frequency
        end_freq: End frequency
        num_samples: Number of samples

    Raises:
        RuntimeError: If monitor cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.monitors", "set_field", project_path=project_path, field_type=field_type, start_freq=start_freq, end_freq=end_freq, num_samples=num_samples)

def set_probe(project_path: str, field_type: str, position: tuple[float, float, float]) -> dict[str, Any]:
    """
    Set a probe.

    Args:
        project_path: Path to .cst file
        field_type: Field type ("E", "H", "Power", etc.)
        position: (x, y, z) probe position

    Raises:
        RuntimeError: If probe cannot be set

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.monitors", "set_probe", project_path=project_path, field_type=field_type, position=position)

def delete_probe(project_path: str, probe_id: str) -> dict[str, Any]:
    """
    Delete a probe.

    Args:
        project_path: Path to .cst file
        probe_id: Probe ID to delete

    Raises:
        RuntimeError: If probe cannot be deleted

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.monitors", "delete_probe", project_path=project_path, probe_id=probe_id)

def delete_monitor(project_path: str, monitor_name: str) -> dict[str, Any]:
    """
    Delete a monitor.

    Args:
        project_path: Path to .cst file
        monitor_name: Monitor name to delete

    Raises:
        RuntimeError: If monitor cannot be deleted

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.monitors", "delete_monitor", project_path=project_path, monitor_name=monitor_name)

MONITORS_TOOLS = [
    {"name": "set-farfield", "handler": set_farfield},
    {"name": "set-efield", "handler": set_efield},
    {"name": "set-field", "handler": set_field},
    {"name": "set-probe", "handler": set_probe},
    {"name": "delete-probe", "handler": delete_probe},
    {"name": "delete-monitor", "handler": delete_monitor},
]
