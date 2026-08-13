"""完全离线的超表面多通道 S 参数分析。"""
from __future__ import annotations

import cmath
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

from .errors import error_response, success_response


def _finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} 必须是有限数值") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} 必须是有限数值")
    return number


def _phase_deg(value: complex) -> float:
    return math.degrees(math.atan2(value.imag, value.real))


def _phase_error(actual_deg: float, target_deg: float) -> float:
    return (actual_deg - target_deg + 180.0) % 360.0 - 180.0


def _unwrap(phases: Sequence[float]) -> list[float]:
    if not phases:
        return []
    result = [phases[0]]
    for phase in phases[1:]:
        previous_wrapped = (result[-1] + 180.0) % 360.0 - 180.0
        delta = (phase - previous_wrapped + 180.0) % 360.0 - 180.0
        result.append(result[-1] + delta)
    return result


def _point_frequency(point: dict[str, Any], path: Path, index: int) -> float:
    if "frequency_ghz" in point:
        return _finite(point["frequency_ghz"], f"{path}: points[{index}].frequency_ghz")
    if "frequency" in point:
        return _finite(point["frequency"], f"{path}: points[{index}].frequency")
    raise ValueError(f"{path}: points[{index}] 缺少 frequency 或 frequency_ghz")


def _read_channel(spec: dict[str, Any]) -> dict[str, Any]:
    name = str(spec.get("name", "")).strip()
    if not name:
        raise ValueError("channel.name 不得为空")
    path = Path(str(spec.get("file_path", ""))).expanduser().resolve()
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValueError(f"通道 {name} 的输入文件不存在或为空：{path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"通道 {name} 无法读取 JSON：{exc}") from exc
    run_id = payload.get("run_id")
    if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id < 0:
        raise ValueError(f"通道 {name} 的 run_id 必须是非负整数")
    raw_points = payload.get("points")
    if not isinstance(raw_points, list) or not raw_points:
        raise ValueError(f"通道 {name} 的 points 不得为空")
    frequencies: list[float] = []
    values: list[complex] = []
    for index, point in enumerate(raw_points):
        if not isinstance(point, dict):
            raise ValueError(f"通道 {name} 的 points[{index}] 必须是对象")
        frequency = _point_frequency(point, path, index)
        real = _finite(point.get("real"), f"{path}: points[{index}].real")
        imag = _finite(point.get("imag"), f"{path}: points[{index}].imag")
        if frequencies and frequency <= frequencies[-1]:
            raise ValueError(f"通道 {name} 的频率网格必须严格递增")
        frequencies.append(frequency)
        values.append(complex(real, imag))
    kind = str(spec.get("kind", "")).strip().casefold()
    polarization = str(spec.get("polarization", "")).strip().casefold()
    if kind not in {"reflection", "transmission"}:
        raise ValueError(f"通道 {name} 的 kind 仅允许 reflection 或 transmission")
    if polarization not in {"co", "cross"}:
        raise ValueError(f"通道 {name} 的 polarization 仅允许 co 或 cross")
    include = spec.get("include_in_total_power", True)
    if not isinstance(include, bool):
        raise ValueError(f"通道 {name} 的 include_in_total_power 必须是布尔值")
    return {
        "name": name,
        "file_path": str(path),
        "run_id": run_id,
        "kind": kind,
        "polarization": polarization,
        "include_in_total_power": include,
        "frequencies": frequencies,
        "values": values,
    }


def _interpolate_complex(frequencies: Sequence[float], values: Sequence[complex], target: float) -> complex:
    if target < frequencies[0] or target > frequencies[-1]:
        raise ValueError("目标频率超出通道频率范围")
    for index, frequency in enumerate(frequencies):
        if math.isclose(target, frequency, rel_tol=0.0, abs_tol=1e-12):
            return values[index]
        if frequency > target:
            left = index - 1
            ratio = (target - frequencies[left]) / (frequency - frequencies[left])
            return values[left] + ratio * (values[index] - values[left])
    return values[-1]


def _channel_points(channel: dict[str, Any]) -> list[dict[str, float]]:
    wrapped = [_phase_deg(value) for value in channel["values"]]
    unwrapped = _unwrap(wrapped)
    result: list[dict[str, float]] = []
    for frequency, value, phase, unwrapped_phase in zip(
        channel["frequencies"], channel["values"], wrapped, unwrapped
    ):
        magnitude = abs(value)
        result.append(
            {
                "frequency_ghz": frequency,
                "real": value.real,
                "imag": value.imag,
                "magnitude": magnitude,
                "magnitude_db": 20.0 * math.log10(max(magnitude, 1e-30)),
                "phase_deg": phase,
                "unwrapped_phase_deg": unwrapped_phase,
            }
        )
    return result


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        temporary.replace(path)
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def analyze_metasurface_sparameters(
    *,
    channels: Sequence[dict[str, Any]],
    output_path: str,
    target_phases: Sequence[dict[str, Any]] | None = None,
    passivity_tolerance: Any = 1e-6,
) -> dict[str, Any]:
    """分析多个 export-sparameter JSON，不连接或启动 CST。"""
    target = Path(str(output_path)).expanduser().resolve()
    if target.suffix.casefold() != ".json":
        return error_response("invalid_output_path", "output_path 必须以 .json 结尾", phase="validation", output_path=str(target))
    try:
        tolerance = _finite(passivity_tolerance, "passivity_tolerance")
        if tolerance < 0:
            raise ValueError("passivity_tolerance 不得小于零")
        if not isinstance(channels, Sequence) or isinstance(channels, (str, bytes)) or not channels:
            raise ValueError("channels 必须是非空数组")
        normalized_channels = [_read_channel(item) for item in channels]
        names = [item["name"] for item in normalized_channels]
        if len(names) != len(set(names)):
            raise ValueError("channel.name 必须唯一")
        run_ids = {item["run_id"] for item in normalized_channels}
        if len(run_ids) != 1:
            raise ValueError("所有通道必须具有相同 run_id")
        grid = normalized_channels[0]["frequencies"]
        for item in normalized_channels[1:]:
            if item["frequencies"] != grid:
                raise ValueError("所有通道必须使用完全一致的频率网格；工具不会隐式重采样")

        channel_outputs: list[dict[str, Any]] = []
        for item in normalized_channels:
            channel_outputs.append(
                {
                    "name": item["name"],
                    "source_file": item["file_path"],
                    "kind": item["kind"],
                    "polarization": item["polarization"],
                    "include_in_total_power": item["include_in_total_power"],
                    "points": _channel_points(item),
                }
            )

        frequency_metrics: list[dict[str, Any]] = []
        passivity_violations: list[dict[str, Any]] = []
        for index, frequency in enumerate(grid):
            powers = {"R_co": 0.0, "R_cross": 0.0, "T_co": 0.0, "T_cross": 0.0}
            for item in normalized_channels:
                if not item["include_in_total_power"]:
                    continue
                prefix = "R" if item["kind"] == "reflection" else "T"
                powers[f"{prefix}_{item['polarization']}"] += abs(item["values"][index]) ** 2
            r_total = powers["R_co"] + powers["R_cross"]
            t_total = powers["T_co"] + powers["T_cross"]
            absorption = 1.0 - r_total - t_total
            reflected_denominator = r_total
            transmitted_denominator = t_total
            passive = r_total + t_total <= 1.0 + tolerance
            metric = {
                "frequency_ghz": frequency,
                **powers,
                "R_total": r_total,
                "T_total": t_total,
                "A": absorption,
                "reflection_pcr": None if reflected_denominator == 0.0 else powers["R_cross"] / reflected_denominator,
                "transmission_pcr": None if transmitted_denominator == 0.0 else powers["T_cross"] / transmitted_denominator,
                "passive": passive,
                "passivity_excess": max(0.0, r_total + t_total - 1.0),
            }
            frequency_metrics.append(metric)
            if not passive:
                passivity_violations.append({"frequency_ghz": frequency, "R_plus_T": r_total + t_total, "excess": r_total + t_total - 1.0})

        by_name = {item["name"]: item for item in normalized_channels}
        phase_errors: list[dict[str, Any]] = []
        for index, raw_target in enumerate(target_phases or []):
            if not isinstance(raw_target, dict):
                raise ValueError(f"target_phases[{index}] 必须是对象")
            channel_name = str(raw_target.get("channel", "")).strip()
            if channel_name not in by_name:
                raise ValueError(f"target_phases[{index}].channel 不存在：{channel_name}")
            frequency = _finite(raw_target.get("frequency_ghz"), f"target_phases[{index}].frequency_ghz")
            target_phase = _finite(raw_target.get("phase_deg"), f"target_phases[{index}].phase_deg")
            channel = by_name[channel_name]
            interpolated = _interpolate_complex(channel["frequencies"], channel["values"], frequency)
            actual_phase = _phase_deg(interpolated)
            error = _phase_error(actual_phase, target_phase)
            phase_errors.append(
                {
                    "channel": channel_name,
                    "frequency_ghz": frequency,
                    "target_phase_deg": target_phase,
                    "interpolated_real": interpolated.real,
                    "interpolated_imag": interpolated.imag,
                    "actual_phase_deg": actual_phase,
                    "phase_error_deg": error,
                    "absolute_phase_error_deg": abs(error),
                }
            )

        absorptions = [item["A"] for item in frequency_metrics]
        reflection_pcr = [item["reflection_pcr"] for item in frequency_metrics if item["reflection_pcr"] is not None]
        transmission_pcr = [item["transmission_pcr"] for item in frequency_metrics if item["transmission_pcr"] is not None]
        absolute_phase_errors = [item["absolute_phase_error_deg"] for item in phase_errors]
        summary = {
            "min_absorption": min(absorptions),
            "max_absorption": max(absorptions),
            "max_R_total": max(item["R_total"] for item in frequency_metrics),
            "max_T_total": max(item["T_total"] for item in frequency_metrics),
            "max_reflection_pcr": max(reflection_pcr) if reflection_pcr else None,
            "max_transmission_pcr": max(transmission_pcr) if transmission_pcr else None,
            "max_absolute_phase_error_deg": max(absolute_phase_errors) if absolute_phase_errors else None,
            "passivity_violation_count": len(passivity_violations),
        }
        payload = {
            "analysis_type": "metasurface_sparameters",
            "run_id": next(iter(run_ids)),
            "frequency_unit": "GHz",
            "frequency_range_ghz": [grid[0], grid[-1]],
            "frequency_count": len(grid),
            "passivity_tolerance": tolerance,
            "channels": channel_outputs,
            "frequency_metrics": frequency_metrics,
            "target_phase_errors": phase_errors,
            "passivity_violations": passivity_violations,
            "summary": summary,
        }
        _write_json_atomic(target, payload)
        if not target.is_file() or target.stat().st_size <= 0:
            raise OSError("分析输出文件不存在或为空")
        return success_response(
            output_path=str(target),
            file_size=target.stat().st_size,
            run_id=payload["run_id"],
            frequency_range_ghz=payload["frequency_range_ghz"],
            frequency_count=len(grid),
            channel_count=len(normalized_channels),
            summary=summary,
            warning_count=len(passivity_violations),
            warnings=passivity_violations,
            verification="non_empty_json_written",
        )
    except (OSError, TypeError, ValueError) as exc:
        return error_response(
            "metasurface_analysis_failed",
            str(exc),
            phase="analysis",
            output_path=str(target),
        )


__all__ = ["analyze_metasurface_sparameters"]
