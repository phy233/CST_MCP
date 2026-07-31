"""由多个原子能力组成的可靠实验动作。"""
from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path
from typing import Any

from ._pipeline_support import safe_log_db
from .contracts import OperationResult, error_result, success_result
from .results import export_run_results
from .session import close_project, open_project
from .simulation import is_simulation_running, start_simulation_async


def _max_exported_run_id(project_path: str) -> int:
    exports_dir = Path(project_path).expanduser().resolve().parent.parent / "exports"
    maximum = 0
    if exports_dir.is_dir():
        for path in exports_dir.glob("s11_run*.json"):
            matched = re.search(r"s11_run(\d+)\.json$", path.name, re.IGNORECASE)
            if matched:
                maximum = max(maximum, int(matched.group(1)))
    return maximum


def _parse_s11_json(file_path: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(Path(file_path).read_text(encoding="utf-8-sig"))
        xdata = payload.get("xdata") or []
        ydata = payload.get("ydata") or []
        if not xdata or not ydata:
            return None
        db_values: list[float] = []
        for item in ydata:
            if isinstance(item, dict):
                real = float(item.get("real", 0.0))
                imag = float(item.get("imag", 0.0))
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                real, imag = float(item[0]), float(item[1])
            else:
                real, imag = float(item), 0.0
            db_values.append(safe_log_db(math.hypot(real, imag)))
        minimum_index = db_values.index(min(db_values))
        return {
            "run_id": payload.get("run_id"),
            "min_db": min(db_values),
            "best_freq": xdata[minimum_index] if minimum_index < len(xdata) else None,
            "point_count": len(db_values),
            "file": Path(file_path).name,
        }
    except Exception:
        return None


def run_experiment(
    project_path: str,
    farfield_names: list[str] | None = None,
    farfield_plot_mode: str = "Realized Gain",
    farfield_theta_step: float = 2.0,
    farfield_phi_step: float = 2.0,
    timeout_seconds: int = 3600,
    poll_interval_seconds: float = 10.0,
) -> OperationResult:
    """启动仿真、等待完成并导出同一轮结果。"""
    maximum_before = _max_exported_run_id(project_path)
    opened = open_project(project_path)
    if opened.get("status") == "error":
        return error_result("pipeline_open_failed", opened.get("message", "打开工程失败"))

    started = start_simulation_async(project_path)
    if started.get("status") == "error":
        close_project(project_path, save=False)
        return error_result("pipeline_sim_start_failed", started.get("message", "启动仿真失败"))

    polls = 0
    waited = 0.0
    while True:
        time.sleep(poll_interval_seconds)
        polls += 1
        waited += poll_interval_seconds
        running = is_simulation_running(project_path)
        if running.get("status") == "error":
            close_project(project_path, save=False)
            return error_result(
                "pipeline_sim_check_failed",
                running.get("message", "读取仿真状态失败"),
                polls=polls,
                waited_seconds=waited,
            )
        if not running.get("running", True):
            break
        if waited >= timeout_seconds:
            close_project(project_path, save=False)
            return error_result(
                "pipeline_sim_timeout",
                "等待仿真完成超时",
                polls=polls,
                timeout_seconds=timeout_seconds,
            )

    closed = close_project(project_path, save=False)
    if closed.get("status") == "error":
        return error_result("pipeline_close_failed", closed.get("message", "关闭工程失败"))

    exported = export_run_results(
        project_path=project_path,
        farfield_names=farfield_names,
        farfield_plot_mode=farfield_plot_mode,
        farfield_theta_step=farfield_theta_step,
        farfield_phi_step=farfield_phi_step,
    )
    if exported.get("status") == "error":
        return error_result(
            "pipeline_export_failed",
            exported.get("message", "导出结果失败"),
            export_result=dict(exported),
        )

    files = exported.get("exported", [])
    s11_files = [path for path in files if re.search(r"s11_run\d+\.json$", str(path), re.IGNORECASE)]
    farfield_files = [path for path in files if "farfield" in str(path).lower()]
    metric = _parse_s11_json(str(s11_files[-1])) if s11_files else None
    maximum_after = _max_exported_run_id(project_path)
    result = success_result(
        pipeline="run-experiment",
        project_path=opened.get("project_path", project_path),
        polls=polls,
        waited_seconds=waited,
        exported_count=len(files),
        exported=files,
        s11_export_path=str(s11_files[-1]) if s11_files else "",
        s11_metric=metric,
        farfield_exported=farfield_files,
        pre_export_max_file_num=maximum_before,
        post_export_max_file_num=maximum_after,
        solver_completed=maximum_after > maximum_before,
    )
    if metric and metric.get("run_id") is not None:
        result["run_id"] = metric["run_id"]
    if maximum_after <= maximum_before:
        if not files:
            return error_result(
                "solver_did_not_complete",
                "求解器没有产生新的结果，也没有可重新导出的缓存结果",
                **dict(result),
            )
        result["warning"] = "solver_result_cached"
        result["message"] = "参数组合已有缓存结果，本次重新导出了现有结果。"
    return result
