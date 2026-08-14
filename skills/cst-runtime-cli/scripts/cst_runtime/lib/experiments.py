"""由多个原子能力组成的可靠实验动作。"""
from __future__ import annotations

import math
import time
from typing import Any

from ._pipeline_support import safe_log_db
from .contracts import OperationResult, error_result, success_result
from .modeling import get_background
from .results import inspect_1d_result, list_run_ids
from .session import close_project, open_project
from .simulation import is_simulation_running, start_simulation_async
from ..core.em_setup import list_monitors
from ..core.solver_diagnostics import (
    capture_solver_log_baseline,
    read_appended_solver_logs,
)


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

    # 求解前预检（best-effort）：存在远场监视器且背景不兼容时直接失败，
    # 避免把 CST 的远场-背景错误留到求解器里才发现。
    preflight_warnings: list[str] = []
    background_snapshot = get_background(project_path)
    if background_snapshot.get("status") == "error":
        preflight_warnings.append(
            f"背景预检不可用：{background_snapshot.get('message', '未知错误')}"
        )
        background_snapshot = None
    farfield_monitors: list[dict[str, Any]] | None = None
    try:
        monitors_result = list_monitors(project_path)
    except Exception as exc:
        monitors_result = {"status": "error", "message": str(exc)}
    if monitors_result.get("status") == "error":
        preflight_warnings.append(
            f"监视器预检不可用：{monitors_result.get('message', '未知错误')}"
        )
    else:
        farfield_monitors = [
            monitor
            for monitor in monitors_result.get("monitors", [])
            if "farfield" in str(monitor.get("type", "")).casefold()
        ]
    if background_snapshot is not None and farfield_monitors:
        if not background_snapshot.get("farfield_compatible", True):
            close_project(project_path, save=False)
            return error_result(
                "background_incompatible_with_farfield",
                "当前背景不满足远场监视器要求：Farfield monitors are not supported "
                "with pec, dispersive, lossy or surface impedance as background "
                "material",
                project_path=opened.get("project_path", project_path),
                background=dict(background_snapshot),
                farfield_monitors=farfield_monitors,
                next_action=(
                    "使用 define-background 将背景重置为 Normal/Vacuum，"
                    "或删除远场监视器后重试"
                ),
            )

    log_baseline = capture_solver_log_baseline(project_path)
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

    # 求解器停止后先检查本次求解新增的日志错误，把 CST 原始报错回传给调用方。
    diagnostics = read_appended_solver_logs(project_path, baseline=log_baseline)
    if diagnostics.get("errors"):
        close_project(project_path, save=False)
        return error_result(
            "solver_reported_error",
            "CST 求解器在结束前报告错误（原始文本见 cst_errors）",
            project_path=opened.get("project_path", project_path),
            polls=polls,
            waited_seconds=waited,
            cst_errors=diagnostics.get("errors", []),
            cst_error_lines=diagnostics.get("error_lines", []),
            log_files=diagnostics.get("log_files", []),
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
            solver_log_tails=diagnostics.get("log_tails", {}),
            preflight_warnings=preflight_warnings,
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
        cst_errors=diagnostics.get("errors", []),
        preflight_warnings=preflight_warnings,
    )
