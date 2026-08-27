from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any


# 复数幅度低于该线性值时 dB 取下限，避免 log(0)。
_MAGNITUDE_FLOOR = 1e-15
_DB_FLOOR = -300.0

# amp_at_freq/phase_at_freq/expression 共用的复数通道视图：
# 以 result_metrics 中保留的 xdata/ydata（inspect_1d_result 序列化格式）为源。


def _wrap_deg(value: float) -> float:
    """把相位角缠绕到 (-180, 180]。"""
    return (float(value) + 180.0) % 360.0 - 180.0


def _normalize_channel_key(path: Any) -> str:
    return str(path or "").strip().replace("/", "\\").casefold()


def _complex_channels_from_metrics(run_output: dict) -> dict[str, dict[str, list]]:
    """从 run_output["result_metrics"] 提取按 result_path 归一化的幅相通道。

    仅当指标同时带有可用 xdata/ydata 时收录；数值型 1D 数据按实数处理。
    """
    channels: dict[str, dict[str, list]] = {}
    metrics = run_output.get("result_metrics")
    if not isinstance(metrics, list):
        return channels
    for metric in metrics:
        if not isinstance(metric, dict):
            continue
        xdata = metric.get("xdata")
        ydata = metric.get("ydata")
        if not isinstance(xdata, list) or not isinstance(ydata, list):
            continue
        freqs: list[float] = []
        db: list[float] = []
        phase_deg: list[float] = []
        usable = True
        for freq_value, value in zip(xdata, ydata):
            real: float
            imag: float
            if isinstance(value, dict) and "real" in value and "imag" in value:
                real, imag = float(value["real"]), float(value["imag"])
            elif isinstance(value, dict) and "abs" in value and "deg" in value:
                magnitude = float(value["abs"])
                angle_rad = math.radians(float(value["deg"]))
                real = magnitude * math.cos(angle_rad)
                imag = magnitude * math.sin(angle_rad)
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                real, imag = float(value), 0.0
            else:
                usable = False
                break
            try:
                freqs.append(float(freq_value))
            except (TypeError, ValueError):
                usable = False
                break
            magnitude = math.hypot(real, imag)
            db.append(
                20.0 * math.log10(magnitude)
                if magnitude > _MAGNITUDE_FLOOR
                else _DB_FLOOR
            )
            phase_deg.append(math.degrees(math.atan2(imag, real)))
        if not usable or not freqs:
            continue
        key = _normalize_channel_key(metric.get("result_path", ""))
        if key and key not in channels:
            channels[key] = {"freq": freqs, "db": db, "phase_deg": phase_deg}
    return channels


def _resolve_channel(
    channels: dict[str, dict[str, list]], result_path: str
) -> tuple[dict[str, list], str]:
    """按精确路径、去后缀子串或唯一通道三种规则解析目标通道。"""
    needle = _normalize_channel_key(result_path)
    if needle and needle in channels:
        return channels[needle], ""
    if needle:
        matched = sorted(item for item in channels.items() if needle in item[0])
        if len(matched) == 1:
            return matched[0][1], ""
        stem = re.sub(r"\\s1,1$", "", needle)
        relaxed = sorted(
            item for item in channels.items() if stem and stem in item[0]
        )
        if len(relaxed) == 1:
            return relaxed[0][1], ""
        return {}, (
            f"result_path={result_path!r} 未匹配到唯一结果通道；"
            f"可用通道: {sorted(channels)}"
        )
    if len(channels) == 1:
        return next(iter(channels.values())), ""
    return {}, (
        "存在多个结果通道时必须提供 result_path；"
        f"可用通道: {sorted(channels)}"
    )


def _nearest_index(channel: dict[str, list], freq: Any) -> int:
    target = float(freq)
    freqs = channel["freq"]
    return min(range(len(freqs)), key=lambda i: abs(freqs[i] - target))


def _resolve_freq(kwargs: dict[str, Any]) -> Any:
    freq = kwargs.get("freq", kwargs.get("freq_ghz"))
    if freq is None:
        raise ValueError("必须提供频点参数 freq (GHz)")
    return freq


def _s11_from_export(run_output: dict) -> dict[str, Any] | None:
    """Parse S11 from pipeline_run_experiment output."""
    s11_metric = run_output.get("s11_metric")
    if s11_metric and isinstance(s11_metric, dict):
        return s11_metric
    s11_path = run_output.get("s11_export_path", "")
    if not s11_path or not Path(s11_path).is_file():
        return None
    try:
        payload = json.loads(Path(s11_path).read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    xdata = payload.get("xdata") or []
    ydata = payload.get("ydata") or []
    if not xdata or not ydata:
        return None
    db_values = []
    for item in ydata:
        if isinstance(item, dict):
            real, imag = float(item.get("real", 0.0)), float(item.get("imag", 0.0))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            real, imag = float(item[0]), float(item[1])
        elif isinstance(item, (int, float)):
            real, imag = float(item), 0.0
        else:
            real, imag = 0.0, 0.0
        mag = math.hypot(real, imag)
        db = 20.0 * math.log10(mag) if mag > 1e-15 else -300.0
        db_values.append(db)
    if not db_values:
        return None
    min_idx = db_values.index(min(db_values))
    return {
        "run_id": payload.get("run_id"),
        "min_db": min(db_values),
        "best_freq": xdata[min_idx] if min_idx < len(xdata) else None,
        "point_count": len(db_values),
        "all_db": db_values,
        "all_freq": xdata,
    }


def _s11_min_db(run_output: dict) -> dict[str, Any]:
    parsed = _s11_from_export(run_output)
    if parsed is None:
        return {"value": 0.0, "error": "no_s11_data"}
    return {"value": parsed["min_db"], "details": parsed}


def _s11_at_freq(run_output: dict, freq: float) -> dict[str, Any]:
    parsed = _s11_from_export(run_output)
    if parsed is None:
        return {"value": 0.0, "error": "no_s11_data"}
    all_freq = parsed.get("all_freq", [])
    all_db = parsed.get("all_db", [])
    if not all_freq or not all_db:
        # s11_from_export returned partial data (s11_metric from pipeline).
        # Try reading the raw S11 file to get full frequency sweep.
        s11_path = run_output.get("s11_export_path", "")
        if s11_path and Path(s11_path).is_file():
            try:
                payload = json.loads(Path(s11_path).read_text(encoding="utf-8-sig"))
                all_freq = payload.get("xdata", [])
                ydata = payload.get("ydata", [])
                all_db = [
                    20.0 * math.log10(max(math.hypot(
                        float(d["real"]), float(d["imag"])), 1e-15))
                    for d in ydata
                ] if ydata and isinstance(ydata[0], dict) else []
            except Exception:
                pass
        if not all_freq or not all_db:
            return {"value": 0.0, "error": "no_frequency_data"}
    idx = min(range(len(all_freq)), key=lambda i: abs(float(all_freq[i]) - freq))
    return {"value": all_db[idx], "details": {"at_freq": all_freq[idx], "source": "s11"}}


def _amp_at_freq(
    run_output: dict,
    result_path: str = "",
    freq: Any = None,
    freq_ghz: Any = None,
) -> dict[str, Any]:
    resolved_freq = freq if freq is not None else freq_ghz
    try:
        resolved_freq = _resolve_freq({"freq": resolved_freq})
    except ValueError as exc:
        return {"value": 0.0, "error": str(exc)}
    channels = _complex_channels_from_metrics(run_output)
    channel, error = _resolve_channel(channels, result_path)
    if error:
        return {"value": 0.0, "error": error}
    idx = _nearest_index(channel, resolved_freq)
    return {
        "value": channel["db"][idx],
        "details": {
            "freq_ghz": channel["freq"][idx],
            "requested_freq_ghz": float(resolved_freq),
        },
    }


def _phase_at_freq(
    run_output: dict,
    result_path: str = "",
    freq: Any = None,
    freq_ghz: Any = None,
    target_deg: Any = 0.0,
) -> dict[str, Any]:
    resolved_freq = freq if freq is not None else freq_ghz
    try:
        resolved_freq = _resolve_freq({"freq": resolved_freq})
    except ValueError as exc:
        return {"value": 0.0, "error": str(exc)}
    channels = _complex_channels_from_metrics(run_output)
    channel, error = _resolve_channel(channels, result_path)
    if error:
        return {"value": 0.0, "error": error}
    idx = _nearest_index(channel, resolved_freq)
    raw_phase_deg = channel["phase_deg"][idx]
    target = float(target_deg or 0.0)
    wrapped_error = abs(_wrap_deg(raw_phase_deg - target))
    return {
        "value": wrapped_error,
        "details": {
            "freq_ghz": channel["freq"][idx],
            "requested_freq_ghz": float(resolved_freq),
            "raw_phase_deg": raw_phase_deg,
            "target_deg": target,
        },
    }


def _gain_max(run_output: dict) -> dict[str, Any]:
    farfield_files = run_output.get("farfield_exported", [])
    if not farfield_files:
        return {"value": 0.0, "error": "no_farfield_data"}
    best_gain = -1e9
    best_file = ""
    for fpath in farfield_files:
        fpath = str(fpath)
        m = re.search(r"_(\d+\.?\d*)dBi", fpath)
        if m:
            val = float(m.group(1))
            if val > best_gain:
                best_gain = val
                best_file = fpath
    if best_gain > -1e8:
        return {"value": best_gain, "details": {"source_file": str(best_file)}}
    return {"value": best_gain, "details": {}}


def _bandwidth(run_output: dict, below_db: float = -10.0) -> dict[str, Any]:
    parsed = _s11_from_export(run_output)
    if parsed is None:
        return {"value": 0.0, "error": "no_s11_data"}
    all_freq = parsed.get("all_freq", [])
    all_db = parsed.get("all_db", [])
    if not all_freq or not all_db:
        return {"value": 0.0, "error": "no_freq_data"}
    below = [f for f, d in zip(all_freq, all_db) if d <= below_db]
    if len(below) >= 2:
        return {
            "value": max(below) - min(below),
            "details": {"below_db": below_db, "passband_edges": [min(below), max(below)]},
        }
    return {"value": 0.0, "details": {"below_db": below_db, "note": "no passband found"}}


_REGISTRY = {
    "s11_min_db": {"fn": lambda r, **kw: _s11_min_db(r), "params": [], "direction": "minimize"},
    "s11_at_freq": {"fn": lambda r, **kw: _s11_at_freq(r, **kw), "params": ["freq"], "direction": "minimize"},
    "gain_max": {"fn": lambda r, **kw: _gain_max(r), "params": [], "direction": "maximize"},
    "bandwidth": {"fn": lambda r, **kw: _bandwidth(r, **kw), "params": ["below_db"], "direction": "maximize"},
    "amp_at_freq": {
        "fn": lambda r, **kw: _amp_at_freq(r, **kw),
        "params": ["result_path", "freq", "freq_ghz"],
        "direction": "minimize",
    },
    "phase_at_freq": {
        "fn": lambda r, **kw: _phase_at_freq(r, **kw),
        "params": ["result_path", "freq", "freq_ghz", "target_deg"],
        "direction": "minimize",
    },
}


def compute_objective(objective_spec: dict, run_output: dict) -> dict[str, Any]:
    obj_type = objective_spec.get("type", "s11_min_db")
    if obj_type == "expression":
        return _compute_expression(objective_spec.get("expr", ""), run_output)
    entry = _REGISTRY.get(obj_type)
    if entry is None:
        return {"value": 0.0, "error": f"unknown objective type: {obj_type}"}
    kwargs = {k: objective_spec.get(k) for k in entry["params"] if k in objective_spec}
    result = entry["fn"](run_output, **kwargs)
    result["type"] = obj_type
    result["direction"] = objective_spec.get("direction", entry["direction"])
    return result


def _expression_environment(run_output: dict) -> tuple[dict[str, Any], str | None]:
    """构建受限表达式环境；数据不足时返回错误说明。"""
    channels = _complex_channels_from_metrics(run_output)

    def resolve(name: Any) -> dict[str, list]:
        channel, error = _resolve_channel(channels, str(name or ""))
        if error:
            raise ValueError(error)
        return channel

    def amp_db(result_path: str, freq: Any) -> float:
        channel = resolve(result_path)
        return channel["db"][_nearest_index(channel, freq)]

    def phase_deg(result_path: str, freq: Any) -> float:
        channel = resolve(result_path)
        return channel["phase_deg"][_nearest_index(channel, freq)]

    parsed = _s11_from_export(run_output)
    if not channels and parsed is None:
        return {}, "no_s11_data"
    env: dict[str, Any] = {
        "min": min,
        "max": max,
        "len": len,
        "abs": abs,
        "wrap": _wrap_deg,
        "amp_db": amp_db,
        "phase_deg": phase_deg,
        "channels": {key: dict(values) for key, values in channels.items()},
    }
    if parsed is not None:
        env["s11_db"] = parsed.get("all_db", [])
        env["s11_freq"] = parsed.get("all_freq", [])
    return env, None


def _compute_expression(expr: str, run_output: dict) -> dict[str, Any]:
    env, error = _expression_environment(run_output)
    if error:
        return {"value": 0.0, "error": error, "type": "expression"}
    try:
        value = eval(expr, {"__builtins__": {}}, env)
        return {"value": float(value), "type": "expression", "details": {"expr": expr}}
    except Exception as e:
        return {"value": 0.0, "error": f"expression eval failed: {e}", "type": "expression"}
