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
    delete_monitor("C:\\path\\to\\model.cst", "farfield (f=10)")
"""
from __future__ import annotations

from typing import Any

from ..core.modeling import set_farfield_monitor as _set_farfield_monitor
from ..core.modeling import set_efield_monitor as _set_efield_monitor
from ..core.modeling import set_field_monitor as _set_field_monitor
from ..core.modeling import set_probe as _set_probe
from ..core.modeling import delete_probe_by_id as _delete_probe_by_id
from ..core.modeling import delete_monitor as _delete_monitor
from ._facade import wrap_public
from .contracts import raise_result_error


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
        raise_result_error(result, "Failed to set farfield monitor")


def set_efield(
    project_path: str,
    start_freq: float,
    end_freq: float,
    step: float = 1,
    dimension: str = "Volume",
    subvolume: tuple[float, float, float, float, float, float] | None = None,
) -> None:
    """Set E-field monitor.

    CST 2022 的 E-field 监视器只支持单频，因此该版本下
    ``start_freq`` 与 ``end_freq`` 必须相同。

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
        raise_result_error(result, "Failed to set E-field monitor")


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
        field_type: 场类型，只允许 "E" 或 "H"
        start_freq: 起始频率；CST 2022 将其作为单一监视频率
        end_freq: 结束频率；CST 2022 要求它与 ``start_freq`` 相同
        num_samples: 样本数；CST 2022 要求为 1

    Raises:
        RuntimeError: If monitor cannot be set
    """
    result = _set_field_monitor(project_path, field_type, start_freq, end_freq, num_samples)
    if result.get("status") == "error":
        raise_result_error(result, "Failed to set field monitor")


def set_probe(
    project_path: str,
    field_type: str,
    position: tuple[float, float, float],
) -> None:
    """Set a probe.

    Args:
        project_path: Path to .cst file
        field_type: 场类型，只允许 "E" 或 "H"
        position: (x, y, z) probe position

    Raises:
        RuntimeError: If probe cannot be set
    """
    result = _set_probe(
        project_path, field_type,
        str(position[0]), str(position[1]), str(position[2])
    )
    if result.get("status") == "error":
        raise_result_error(result, "Failed to set probe")


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
        raise_result_error(result, "Failed to delete probe")


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
        raise_result_error(result, "Failed to delete monitor")


for _public_name in (
    "set_farfield", "set_efield", "set_field", "set_probe",
    "delete_probe", "delete_monitor",
):
    globals()[_public_name] = wrap_public(globals()[_public_name])
