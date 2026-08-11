"""CST simulation results reading.

Usage:
    from cst_runtime.lib.results import get_sparam, list_items, list_runs

    # Read S-parameter data
    result = get_sparam("C:\\path\\to\\model.cst",
                       "1D Results\\S-Parameters\\S1,1")

    # List available result items
    items = list_items("C:\\path\\to\\model.cst")

    # List simulation run IDs
    runs = list_runs("C:\\path\\to\\model.cst")
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from ..core.results import get_1d_result as _get_1d_result
from ..core.results import get_2d_result as _get_2d_result
from ..core.results import list_result_items as _list_result_items
from ..core.results import list_run_ids as _list_run_ids
from ..core.results import get_parameter_combination as _get_parameter_combination
from ..core.results import export_run_results as _export_run_results
from ..core.results import result_item_exists as _result_item_exists
from ..core import results as _core_results
from ._facade import call_core, wrap_core
from .contracts import OperationResult, error_result, success_result


def _finite_number(value: Any, *, field: str, index: int) -> float:
    """把结果 JSON 中的标量转换为有限浮点数。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field}[{index}] 不是数值")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{field}[{index}] 不是有限数值")
    return normalized


def _complex_parts(value: Any, *, index: int) -> tuple[float, float]:
    """解析 core.serialize_value 写出的复数或实数结果。"""
    if isinstance(value, dict):
        if "real" not in value or "imag" not in value:
            raise ValueError(f"ydata[{index}] 缺少 real/imag")
        return (
            _finite_number(value["real"], field="ydata.real", index=index),
            _finite_number(value["imag"], field="ydata.imag", index=index),
        )
    return _finite_number(value, field="ydata", index=index), 0.0


def _hydrate_sparam_export(result: OperationResult) -> OperationResult:
    """读取 get-1d-result 的本地 JSON，并恢复工作流需要的复数数据。"""
    export_path = result.get("export_path")
    if not isinstance(export_path, str) or not export_path.strip():
        return error_result(
            "result_export_missing",
            "get-1d-result 未返回有效的 export_path",
            treepath=result.get("treepath"),
        )
    export_file = Path(export_path)
    try:
        payload = json.loads(export_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return error_result(
            "result_export_invalid",
            f"无法读取结果 JSON: {exc}",
            export_path=str(export_file),
            treepath=result.get("treepath"),
        )

    xdata = payload.get("xdata")
    ydata = payload.get("ydata")
    if not isinstance(xdata, list) or not isinstance(ydata, list):
        return error_result(
            "result_data_invalid",
            "S 参数结果的 xdata/ydata 必须是数组",
            export_path=str(export_file),
            treepath=result.get("treepath"),
        )
    if not xdata or not ydata:
        return error_result(
            "result_data_empty",
            "S 参数结果中没有数据点",
            export_path=str(export_file),
            treepath=result.get("treepath"),
        )
    if len(xdata) != len(ydata):
        return error_result(
            "result_data_length_mismatch",
            "S 参数结果的频率与复数数据点数量不一致",
            x_count=len(xdata),
            y_count=len(ydata),
            export_path=str(export_file),
            treepath=result.get("treepath"),
        )

    try:
        points = []
        for index, (frequency, value) in enumerate(zip(xdata, ydata)):
            real, imag = _complex_parts(value, index=index)
            points.append(
                {
                    "frequency": _finite_number(
                        frequency,
                        field="xdata",
                        index=index,
                    ),
                    "real": real,
                    "imag": imag,
                }
            )
    except ValueError as exc:
        return error_result(
            "result_data_invalid",
            str(exc),
            export_path=str(export_file),
            treepath=result.get("treepath"),
        )

    points.sort(key=lambda point: point["frequency"])
    duplicate = next(
        (
            points[index]["frequency"]
            for index in range(1, len(points))
            if points[index]["frequency"] == points[index - 1]["frequency"]
        ),
        None,
    )
    if duplicate is not None:
        return error_result(
            "duplicate_result_frequency",
            f"S 参数结果包含重复频点: {duplicate}",
            frequency=duplicate,
            export_path=str(export_file),
            treepath=result.get("treepath"),
        )

    hydrated = OperationResult(result)
    hydrated["xdata"] = [point["frequency"] for point in points]
    hydrated["ydata"] = points
    hydrated["point_count"] = len(points)
    return hydrated


def get_sparam(project_path: str, treepath: str, run_id: int = 0) -> OperationResult:
    """Read S-parameter data (offline, no CST needed).

    Args:
        project_path: Path to .cst file
        treepath: Result tree path (e.g., "1D Results\\S-Parameters\\S1,1")
        run_id: Run ID (0 for default)

    Returns:
        Dict with xdata, ydata, and metadata

    Raises:
        RuntimeError: If result cannot be read
    """
    result = call_core(_get_1d_result, project_path, treepath, run_id=run_id)
    if result.get("status") == "error":
        return result
    return _hydrate_sparam_export(result)


def get_sparam_at_freq(project_path: str, treepath: str, freq_ghz: float, run_id: int = 0) -> OperationResult:
    """Get S-parameter at specific frequency (linear interpolation).

    Args:
        project_path: Path to .cst file
        treepath: Result tree path
        freq_ghz: Target frequency in GHz
        run_id: Run ID (0 for default)

    Returns:
        Dict with interpolated real, imag, magnitude, phase values

    Raises:
        RuntimeError: If result cannot be read or interpolated
    """
    result = get_sparam(project_path, treepath, run_id=run_id)
    if result.get("status") == "error":
        return result
    if isinstance(freq_ghz, bool):
        return error_result("invalid_frequency", "目标频率必须是有限数值")
    try:
        target = float(freq_ghz)
    except (TypeError, ValueError):
        return error_result("invalid_frequency", "目标频率必须是有限数值")
    if not math.isfinite(target):
        return error_result("invalid_frequency", "目标频率必须是有限数值")

    ydata = result["ydata"]
    frequencies = [point["frequency"] for point in ydata]
    lower = frequencies[0]
    upper = frequencies[-1]
    if target < lower or target > upper:
        return error_result(
            "frequency_out_of_range",
            f"目标频率 {target} GHz 超出结果范围 [{lower}, {upper}] GHz",
            frequency_ghz=target,
            min_frequency_ghz=lower,
            max_frequency_ghz=upper,
            treepath=treepath,
        )

    upper_index = next(
        (index for index, frequency in enumerate(frequencies) if frequency >= target),
        len(frequencies) - 1,
    )
    if frequencies[upper_index] == target or upper_index == 0:
        re_interp = ydata[upper_index]["real"]
        im_interp = ydata[upper_index]["imag"]
    else:
        lower_point = ydata[upper_index - 1]
        upper_point = ydata[upper_index]
        ratio = (
            (target - lower_point["frequency"])
            / (upper_point["frequency"] - lower_point["frequency"])
        )
        re_interp = lower_point["real"] + ratio * (
            upper_point["real"] - lower_point["real"]
        )
        im_interp = lower_point["imag"] + ratio * (
            upper_point["imag"] - lower_point["imag"]
        )
    mag = math.hypot(re_interp, im_interp)
    phase = math.atan2(im_interp, re_interp)

    return success_result(
        frequency_ghz=target,
        real=re_interp,
        imag=im_interp,
        magnitude=mag,
        magnitude_db=float(20 * math.log10(max(mag, 1e-30))),
        phase_rad=phase,
        phase_deg=float(math.degrees(phase)),
    )


def get_2d_field(project_path: str, treepath: str) -> OperationResult:
    """Read 2D field data.

    Args:
        project_path: Path to .cst file
        treepath: Result tree path

    Returns:
        Dict with field data

    Raises:
        RuntimeError: If result cannot be read
    """
    return call_core(_get_2d_result, project_path, treepath)


def list_items(project_path: str, filter_type: str = "0D/1D") -> OperationResult:
    """List available result items.

    Args:
        project_path: Path to .cst file
        filter_type: Filter type (e.g., "0D/1D", "2D", "all")

    Returns:
        List of result tree paths
    """
    return call_core(_list_result_items, project_path, filter_type=filter_type)


def list_sparams(project_path: str) -> OperationResult:
    """List available S-parameters.

    Args:
        project_path: Path to .cst file

    Returns:
        List of S-parameter tree paths
    """
    result = list_items(project_path, filter_type="0D/1D")
    if result.get("status") == "error":
        return result
    items = [item for item in result.get("items", []) if "S-Parameters" in item]
    return success_result(project_path=project_path, items=items, count=len(items))


def sparam_exists(project_path: str, treepath: str) -> OperationResult:
    """Check if S-parameter exists.

    Args:
        project_path: Path to .cst file
        treepath: Result tree path

    Returns:
        True if S-parameter exists
    """
    return call_core(_result_item_exists, project_path, treepath)


def list_runs(project_path: str) -> OperationResult:
    """List simulation run IDs.

    Args:
        project_path: Path to .cst file

    Returns:
        List of run IDs
    """
    return call_core(_list_run_ids, project_path)


def get_param_combo(project_path: str, run_id: int) -> OperationResult:
    """Get parameter combination for a run.

    Args:
        project_path: Path to .cst file
        run_id: Run ID

    Returns:
        Dict with parameter names and values

    Raises:
        RuntimeError: If parameter combination cannot be retrieved
    """
    return call_core(_get_parameter_combination, project_path, run_id)


def export_all(project_path: str, **kwargs) -> OperationResult:
    """Export all results for a run.

    Args:
        project_path: Path to .cst file
        **kwargs: Additional arguments for export

    Returns:
        Dict with exported files

    Raises:
        RuntimeError: If export fails
    """
    return call_core(_export_run_results, project_path, **kwargs)


# 工具协议使用的原子业务名称；统一经过同一 lib 边界。
open_project = wrap_core(_core_results.open_project)
list_subprojects = wrap_core(_core_results.list_subprojects)
get_version_info = wrap_core(_core_results.get_version_info)
list_result_items = wrap_core(_core_results.list_result_items)
list_run_ids = wrap_core(_core_results.list_run_ids)
get_parameter_combination = wrap_core(_core_results.get_parameter_combination)
get_1d_result = wrap_core(_core_results.get_1d_result)
get_2d_result = wrap_core(_core_results.get_2d_result)
export_run_results = wrap_core(_core_results.export_run_results)
generate_report = wrap_core(_core_results.generate_report)
plot_exported_file = wrap_core(_core_results.plot_exported_file)


def _abs_project_path(project_path: str) -> str:
    """Normalize project path to absolute path."""
    from pathlib import Path
    return str(Path(project_path).expanduser().resolve())
