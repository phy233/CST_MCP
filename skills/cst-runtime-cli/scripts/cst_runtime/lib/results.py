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
import re
from pathlib import Path
from typing import Any

from ..core.results import get_1d_result as _get_1d_result
from ..core.results import get_2d_result as _get_2d_result
from ..core.results import list_result_items as _list_result_items
from ..core.results import list_run_ids as _list_run_ids
from ..core.results import get_parameter_combination as _get_parameter_combination
from ..core.results import list_sparameter_results as _list_sparameter_results
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


def get_sparam(
    project_path: str,
    treepath: str,
    run_id: int = 0,
    export_path: str = "",
    allow_interactive: bool = True,
) -> OperationResult:
    """Read S-parameter data.

    allow_interactive=True 时允许工程同时在 CST 中打开，读取最近保存到
    磁盘的工程状态（与 list-sparameter-results 契约一致）；求解器已把
    新 Run 写入磁盘，因此扫描流程可在模型会话保持打开时读取最新结果。

    Args:
        project_path: Path to .cst file
        treepath: Result tree path (e.g., "1D Results\\S-Parameters\\S1,1")
        run_id: Run ID (0 for default)

    Returns:
        Dict with xdata, ydata, and metadata

    Raises:
        RuntimeError: If result cannot be read
    """
    result = call_core(
        _get_1d_result,
        project_path,
        treepath,
        run_id=run_id,
        export_path=export_path,
        allow_interactive=allow_interactive,
    )
    if result.get("status") == "error":
        return result
    return _hydrate_sparam_export(result)


def get_sparam_at_freq(
    project_path: str,
    treepath: str,
    freq_ghz: float,
    run_id: int = 0,
    allow_interactive: bool = True,
) -> OperationResult:
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
    result = get_sparam(
        project_path,
        treepath,
        run_id=run_id,
        allow_interactive=allow_interactive,
    )
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


_SPARAM_NAME = re.compile(
    r"^S(?P<response>[^,()]+)(?:\((?P<response_mode>\d+)\))?,"
    r"(?P<excitation>[^,()]+)(?:\((?P<excitation_mode>\d+)\))?$",
    re.IGNORECASE,
)


def _parse_sparameter_name(name: str) -> dict[str, Any]:
    """解析 CST 2022 普通端口和 Floquet 示例使用的 S 参数名称。"""
    matched = _SPARAM_NAME.fullmatch(name.strip())
    if matched is None:
        return {}
    values = matched.groupdict()
    return {
        "response_port": values["response"],
        "excitation_port": values["excitation"],
        "response_mode": (
            int(values["response_mode"]) if values["response_mode"] else None
        ),
        "excitation_mode": (
            int(values["excitation_mode"]) if values["excitation_mode"] else None
        ),
    }


def list_sparameter_results(project_path: str) -> OperationResult:
    """枚举实际 ResultTree 中的 S 参数节点，不生成模型相关路径。"""
    result = call_core(_list_sparameter_results, project_path)
    if result.get("status") == "error":
        return result
    enriched = []
    for item in result.get("results", []):
        enriched.append({**item, **_parse_sparameter_name(str(item.get("name", "")))})
    return success_result(
        project_path=result.get("project_path", project_path),
        count=len(enriched),
        results=enriched,
    )


def _select_sparameter_path(
    results: list[dict[str, Any]],
    *,
    result_path: str,
    response_port: str,
    excitation_port: str,
    response_mode: int | None,
    excitation_mode: int | None,
) -> OperationResult:
    selector_used = any(
        value not in (None, "")
        for value in (response_port, excitation_port, response_mode, excitation_mode)
    )
    if result_path and selector_used:
        return error_result(
            "conflicting_result_selector",
            "result_path 与端口/模式选择器只能使用一种",
        )
    if result_path:
        matched = [
            item for item in results
            if str(item.get("result_path", "")).casefold() == result_path.casefold()
        ]
    else:
        if not response_port or not excitation_port:
            return error_result(
                "sparameter_selector_missing",
                "必须提供 result_path，或同时提供 response_port 和 excitation_port",
            )
        if (response_mode is None) != (excitation_mode is None):
            return error_result(
                "incomplete_mode_selector",
                "模式化结果必须同时提供 response_mode 和 excitation_mode",
            )
        matched = [
            item for item in results
            if str(item.get("response_port", "")).casefold() == response_port.casefold()
            and str(item.get("excitation_port", "")).casefold() == excitation_port.casefold()
            and item.get("response_mode") == response_mode
            and item.get("excitation_mode") == excitation_mode
        ]
    candidates = [str(item.get("result_path", "")) for item in matched]
    if not matched:
        return error_result(
            "sparameter_result_not_found",
            "实际 ResultTree 中没有匹配的 S 参数节点",
            candidates=[str(item.get("result_path", "")) for item in results],
        )
    if len(matched) != 1:
        return error_result(
            "sparameter_result_ambiguous",
            "S 参数选择器匹配到多个节点，请改用完整 result_path",
            candidates=candidates,
        )
    return success_result(selected=matched[0])


def export_sparameter(
    project_path: str,
    run_id: int,
    output_path: str,
    *,
    result_path: str = "",
    response_port: str = "",
    excitation_port: str = "",
    response_mode: int | None = None,
    excitation_mode: int | None = None,
) -> OperationResult:
    """导出任意普通端口或 Floquet S 参数曲线。"""
    if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id < 0:
        return error_result("invalid_run_id", "run_id 必须是非负整数")
    target = Path(output_path).expanduser()
    if target.suffix.casefold() != ".json":
        return error_result("invalid_export_extension", "output_path 必须使用 .json 扩展名")
    listed = list_sparameter_results(project_path)
    if listed.get("status") == "error":
        return listed
    selected_result = _select_sparameter_path(
        list(listed.get("results", [])),
        result_path=result_path.strip(),
        response_port=response_port.strip(),
        excitation_port=excitation_port.strip(),
        response_mode=response_mode,
        excitation_mode=excitation_mode,
    )
    if selected_result.get("status") == "error":
        return selected_result
    selected = dict(selected_result["selected"])
    available_run_ids = [int(item) for item in selected.get("run_ids", [])]
    if run_id == 0 and any(item != 0 for item in available_run_ids):
        return error_result(
            "ambiguous_run_id_zero",
            "该节点含多个 Run ID；请传入 run-experiment 返回的具体非零 Run ID",
            run_ids=available_run_ids,
        )
    if run_id not in available_run_ids:
        return error_result(
            "run_id_not_available",
            "指定 Run ID 不属于所选结果节点",
            run_id=run_id,
            run_ids=available_run_ids,
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target = target.resolve()
    result = get_sparam(
        project_path,
        str(selected["result_path"]),
        run_id=run_id,
        export_path=str(target),
    )
    if result.get("status") == "error":
        return result
    points = []
    for point in result["ydata"]:
        magnitude = math.hypot(point["real"], point["imag"])
        points.append(
            {
                **point,
                "magnitude": magnitude,
                "magnitude_db": 20.0 * math.log10(max(magnitude, 1e-30)),
                "phase_deg": math.degrees(math.atan2(point["imag"], point["real"])),
            }
        )
    minimum = min(points, key=lambda item: item["magnitude_db"])
    metric = {
        "result_path": selected["result_path"],
        "run_id": run_id,
        "point_count": len(points),
        "min_db": minimum["magnitude_db"],
        "best_freq": minimum["frequency"],
    }
    payload = {
        "result_path": selected["result_path"],
        "result_name": selected["name"],
        "run_id": run_id,
        "selector": {key: selected.get(key) for key in (
            "response_port", "excitation_port", "response_mode", "excitation_mode"
        )},
        "point_count": len(points),
        "points": points,
        "result_metric": metric,
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if not target.is_file() or target.stat().st_size == 0:
        return error_result("empty_export_file", "S 参数导出文件不存在或为空")
    return success_result(
        project_path=str(Path(project_path).expanduser().resolve()),
        result_path=selected["result_path"],
        run_id=run_id,
        output_path=str(target),
        point_count=len(points),
        result_metric=metric,
        s11_metric=metric if str(selected["name"]).casefold() == "s1,1" else None,
    )


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


# 工具协议使用的原子业务名称；统一经过同一 lib 边界。
open_project = wrap_core(_core_results.open_project)
list_subprojects = wrap_core(_core_results.list_subprojects)
get_version_info = wrap_core(_core_results.get_version_info)
list_result_items = wrap_core(_core_results.list_result_items)
list_run_ids = wrap_core(_core_results.list_run_ids)
get_parameter_combination = wrap_core(_core_results.get_parameter_combination)
get_1d_result = wrap_core(_core_results.get_1d_result)
inspect_1d_result = wrap_core(_core_results.inspect_1d_result)
export_touchstone = wrap_core(_core_results.export_touchstone)
get_2d_result = wrap_core(_core_results.get_2d_result)
generate_report = wrap_core(_core_results.generate_report)
plot_exported_file = wrap_core(_core_results.plot_exported_file)


def _abs_project_path(project_path: str) -> str:
    """Normalize project path to absolute path."""
    from pathlib import Path
    return str(Path(project_path).expanduser().resolve())
