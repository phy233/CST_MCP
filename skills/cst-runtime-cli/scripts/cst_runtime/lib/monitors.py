"""CST monitor management operations.

Usage:
    from cst_runtime.lib.monitors import set_farfield, set_efield, set_probe, delete_monitor

    # Set farfield monitor
    set_farfield("C:\\path\\to\\model.cst",
                 start_freq=8, end_freq=12, step=0.5)

    # Set E-field monitor
    set_efield("C:\\path\\to\\model.cst",
               start_freq=10, end_freq=10, step=1)

    # Set a probe
    set_probe("C:\\path\\to\\model.cst",
              field_type="E",
              position=(0, 0, 5))

    # Delete monitor
    delete_monitor("C:\\path\\to\\model.cst", "farfield (f=10)_1")
"""
from __future__ import annotations

from typing import Any

from ..core.modeling import set_farfield_monitor as _set_farfield_monitor
from ..core.modeling import set_efield_monitor as _set_efield_monitor
from ..core.modeling import set_field_monitor as _set_field_monitor
from ..core.modeling import set_probe as _set_probe
from ..core.modeling import delete_probe_by_id as _delete_probe_by_id
from ..core.modeling import delete_monitor as _delete_monitor


def set_farfield(
    project_path: str,
    start_freq: float,
    end_freq: float,
    step: float = 1,
    subvolume: tuple[float, float, float, float, float, float] | None = None,
    enable_nearfield: bool = True,
) -> None:
    """Set farfield monitor.

    Args:
        project_path: Path to .cst file
        start_freq: Start frequency in GHz
        end_freq: End frequency in GHz
        step: Frequency step in GHz
        subvolume: Optional (xmin, xmax, ymin, ymax, zmin, zmax) subvolume
        enable_nearfield: Whether to enable nearfield calculation

    Raises:
        RuntimeError: If monitor cannot be set
    """
    kwargs = {
        "start_freq": start_freq,
        "end_freq": end_freq,
        "step": step,
        "enable_nearfield": enable_nearfield,
    }
    if subvolume:
        kwargs.update({
            "subvolume_x_min": subvolume[0],
            "subvolume_x_max": subvolume[1],
            "subvolume_y_min": subvolume[2],
            "subvolume_y_max": subvolume[3],
            "subvolume_z_min": subvolume[4],
            "subvolume_z_max": subvolume[5],
        })
    result = _set_farfield_monitor(project_path, **kwargs)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set farfield monitor"))


def set_efield(
    project_path: str,
    start_freq: float,
    end_freq: float,
    step: float = 1,
    dimension: str = "Volume",
    subvolume: tuple[float, float, float, float, float, float] | None = None,
) -> None:
    """Set E-field monitor.

    Args:
        project_path: Path to .cst file
        start_freq: Start frequency in GHz
        end_freq: End frequency in GHz
        step: Frequency step in GHz
        dimension: Dimension type ("Volume", "Surface", etc.)
        subvolume: Optional (xmin, xmax, ymin, ymax, zmin, zmax) subvolume

    Raises:
        RuntimeError: If monitor cannot be set
    """
    kwargs = {
        "start_freq": start_freq,
        "end_freq": end_freq,
        "step": step,
        "dimension": dimension,
    }
    if subvolume:
        kwargs.update({
            "subvolume_x_min": subvolume[0],
            "subvolume_x_max": subvolume[1],
            "subvolume_y_min": subvolume[2],
            "subvolume_y_max": subvolume[3],
            "subvolume_z_min": subvolume[4],
            "subvolume_z_max": subvolume[5],
        })
    result = _set_efield_monitor(project_path, **kwargs)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set E-field monitor"))


def set_field(
    project_path: str,
    field_type: str,
    start_freq: str,
    end_freq: str,
    num_samples: str,
) -> None:
    """Set generic field monitor.

    Args:
        project_path: Path to .cst file
        field_type: Field type ("E", "H", "Power", etc.)
        start_freq: Start frequency
        end_freq: End frequency
        num_samples: Number of samples

    Raises:
        RuntimeError: If monitor cannot be set
    """
    result = _set_field_monitor(project_path, field_type, start_freq, end_freq, num_samples)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set field monitor"))


def set_probe(
    project_path: str,
    field_type: str,
    position: tuple[float, float, float],
) -> None:
    """Set a probe.

    Args:
        project_path: Path to .cst file
        field_type: Field type ("E", "H", "Power", etc.)
        position: (x, y, z) probe position

    Raises:
        RuntimeError: If probe cannot be set
    """
    result = _set_probe(
        project_path, field_type,
        str(position[0]), str(position[1]), str(position[2])
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to set probe"))


def delete_probe(project_path: str, probe_id: str) -> None:
    """Delete a probe.

    Args:
        project_path: Path to .cst file
        probe_id: Probe ID to delete

    Raises:
        RuntimeError: If probe cannot be deleted
    """
    result = _delete_probe_by_id(project_path, probe_id)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to delete probe"))


def delete_monitor(project_path: str, monitor_name: str) -> None:
    """Delete a monitor.

    Args:
        project_path: Path to .cst file
        monitor_name: Monitor name to delete

    Raises:
        RuntimeError: If monitor cannot be deleted
    """
    result = _delete_monitor(project_path, monitor_name)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to delete monitor"))
