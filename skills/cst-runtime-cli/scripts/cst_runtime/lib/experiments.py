"""由多个原子能力组成的可靠实验动作。"""
from __future__ import annotations

import math
import time
from typing import Any

from ._pipeline_support import safe_log_db
from .contracts import OperationResult, error_result, success_result
from .results import inspect_1d_result, list_run_ids
from .session import close_project, open_project
from .simulation import is_simulation_running, start_simulation_async


def _run_ids_for_path(project_path: str, result_path: str) -> OperationResult:
    return list_run_ids(
        project_path=project_path,
        treepath=result_path,
        module_type="3d",
        allow_interactive=True,
        subproject_treepath="",
        skip_nonparametric=False,
        max_mesh_passes_only=True,
    )


def _metric_from_result(result: dict[str, Any]) -> dict[str, Any]:
    """从已验证的 0D/1D 数据生成不绑定物理模型的摘要。"""
    metric: dict[str, Any] = {
        "result_path": result.get("result_path"),
        "run_id": result.get("run_id"),
        "point_count": int(result.get("point_count", 0)),
    }
    xdata = result.get("xdata")
    ydata = result.get("ydata")
    if not isinstance(xdata, list) or not isinstance(ydata, list) or not ydata:
        return metric
    db_values: list[float] = []
    for value in ydata:
        if isinstance(value, dict) and "real" in value and "imag" in value:
            magnitude = math.hypot(float(value["real"]), float(value["imag"]))
        elif isinstance(value, (int, float)):
            magnitude = abs(float(value))
        else:
            return metric
        db_values.append(safe_log_db(magnitude))
    minimum_index = db_values.index(min(db_values))
    metric["min_db"] = db_values[minimum_index]
    metric["best_freq"] = (
        xdata[minimum_index] if minimum_index < len(xdata) else None
    )
    return metric


def run_experiment(
    project_path: str,
    completion_result_paths: list[str],
    timeout_seconds: int = 3600,
    poll_interval_seconds: float = 10.0,
) -> OperationResult:
    """启动仿真并以新 Run ID 和指定非空结果节点确认完成。"""
    normalized_paths = [str(path).strip() for path in completion_result_paths]
    if not normalized_paths or any(not path for path in normalized_paths):
        return error_result(
            "completion_result_paths_missing",
            "completion_result_paths 必须是非空结果路径数组",
        )
    if len(set(path.casefold() for path in normalized_paths)) != len(normalized_paths):
        return error_result(
            "duplicate_completion_result_path",
            "completion_result_paths 不得包含重复路径",
        )

    before: dict[str, set[int]] = {}
    for result_path in normalized_paths:
        listed = _run_ids_for_path(project_path, result_path)
        if listed.get("status") == "error":
            return error_result(
                "completion_result_preflight_failed",
                "求解前无法读取指定结果节点的 Run ID",
                result_path=result_path,
                detail=dict(listed),
            )
        before[result_path] = {int(item) for item in listed.get("run_ids", [])}

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

    new_run_sets: list[set[int]] = []
    for result_path in normalized_paths:
        listed = _run_ids_for_path(project_path, result_path)
        if listed.get("status") == "error":
            return error_result(
                "completion_result_postflight_failed",
                "求解后无法读取指定结果节点的 Run ID",
                result_path=result_path,
                detail=dict(listed),
            )
        after = {int(item) for item in listed.get("run_ids", [])}
        new_run_sets.append(after - before[result_path])
    common_new_runs = set.intersection(*new_run_sets) if new_run_sets else set()
    if not common_new_runs:
        return error_result(
            "solver_did_not_create_new_run",
            "指定完成节点没有共同的新 Run ID，不能确认本次求解完成",
            completion_result_paths=normalized_paths,
        )
    run_id = max(common_new_runs)
    metrics: list[dict[str, Any]] = []
    for result_path in normalized_paths:
        inspected = inspect_1d_result(
            project_path,
            result_path,
            run_id,
            allow_interactive=True,
        )
        if inspected.get("status") == "error" or int(inspected.get("point_count", 0)) <= 0:
            return error_result(
                "completion_result_empty",
                "指定完成节点不存在、读取失败或数据为空",
                result_path=result_path,
                run_id=run_id,
                detail=dict(inspected),
            )
        metrics.append(_metric_from_result(dict(inspected)))
    s11_metric = next(
        (
            metric for metric in metrics
            if str(metric.get("result_path", "")).rsplit("\\", 1)[-1].casefold() == "s1,1"
        ),
        None,
    )
    return success_result(
        pipeline="run-experiment",
        project_path=opened.get("project_path", project_path),
        polls=polls,
        waited_seconds=waited,
        run_id=run_id,
        completion_result_paths=normalized_paths,
        result_metrics=metrics,
        s11_metric=s11_metric,
        solver_completed=True,
    )
