"""由多个原子能力组成的可靠实验动作。"""
from __future__ import annotations

import math
import time
from typing import Any

from ._pipeline_support import safe_log_db
from .contracts import OperationResult, error_result, success_result
from .modeling import get_background
from .results import inspect_1d_result, list_result_items, list_run_ids
from .session import close_project, open_project
from .simulation import is_simulation_running, start_simulation_async
from ..core.em_setup import list_monitors
from ..core.environment import get_long_run_threshold
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


def _result_node_absent(
    project_path: str,
    result_path: str,
    failure: dict[str, Any],
) -> bool:
    """判断 list_run_ids 失败是否因为结果节点尚不存在。

    首次仿真前 S1,1 等节点当然不存在，这是正常初始状态而不是预检失败：
    CST 结果 API 对不存在的节点报 "tree path not found"，再通过手册
    文档化的树枚举通道（get_tree_items/0D/1D）复核该节点确实不在结果
    树中；两者一致才视为合法空基线，其余错误仍按预检/后检失败处理。
    """
    error_type = failure.get("error_type")
    message = str(failure.get("message", "")).casefold()
    if error_type == "result_node_not_found":
        # core 层已给出“节点不存在”的稳定错误码
        pass
    elif error_type == "list_run_ids_failed" and "tree path not found" in message:
        # 旧版 CST 文案兜底：仍按节点缺失处理，但必须经树枚举复核
        pass
    else:
        # 其余报错（工程未打开、文件不存在等）即使树枚举恰好为空
        # 也不能当作“节点尚未创建”的正常初始状态。
        return False
    enumerated = list_result_items(
        project_path=project_path,
        module_type="3d",
        filter_type="0D/1D",
        allow_interactive=True,
    )
    if enumerated.get("status") != "success":
        # 树枚举通道故障时保守处理：不能证明节点缺失，按真实预检失败上报，
        # 避免把读取通道损坏误判为“首次仿真的正常空基线”。
        return False
    normalized_target = _normalize_result_path(result_path)
    items = {
        _normalize_result_path(str(item))
        for item in enumerated.get("items", [])
    }
    # 树枚举显示节点存在则与 CST 报错矛盾，按真实失败处理
    return normalized_target not in items


def _normalize_result_path(path: str) -> str:
    """统一结果树路径格式：反斜杠分隔、去首尾空白、大小写不敏感。"""
    return str(path).strip().replace("/", "\\").casefold()


# result_metrics 内联复数序列的最大采样点数；超过后均匀降采样并保留原点数。
_MAX_METRIC_SERIES_POINTS = 5000


def _parse_complex_sample(value: Any) -> tuple[float, float] | None:
    """把 inspect_1d_result 序列化后的单点解析为 (real, imag)。"""
    if isinstance(value, dict) and "real" in value and "imag" in value:
        return float(value["real"]), float(value["imag"])
    if isinstance(value, dict) and "abs" in value and "deg" in value:
        magnitude = float(value["abs"])
        angle_rad = math.radians(float(value["deg"]))
        return (
            magnitude * math.cos(angle_rad),
            magnitude * math.sin(angle_rad),
        )
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value), 0.0
    return None


def _serialize_metric_series(
    xdata: list[Any],
    ydata: list[Any],
) -> tuple[list[float], list[dict[str, float]], bool] | None:
    """整理为 (频率数组, 复数点数组, 是否降采样)；无法解析时返回 None。

    频率与复数点一一对应；超过 _MAX_METRIC_SERIES_POINTS 时按等步长降采样，
    min_db/best_freq 等摘要仍基于完整原始数据计算。
    """
    freqs: list[float] = []
    points: list[dict[str, float]] = []
    for freq_value, value in zip(xdata, ydata):
        parsed = _parse_complex_sample(value)
        if parsed is None:
            return None
        try:
            freqs.append(float(freq_value))
        except (TypeError, ValueError):
            return None
        points.append({"real": parsed[0], "imag": parsed[1]})
    if not freqs:
        return None
    step = max(1, math.ceil(len(freqs) / _MAX_METRIC_SERIES_POINTS))
    downsampled = step > 1
    indices = range(0, len(freqs), step)
    return (
        [freqs[i] for i in indices],
        [points[i] for i in indices],
        downsampled,
    )


def _metric_from_result(result: dict[str, Any]) -> dict[str, Any]:
    """从已验证的 0D/1D 数据生成摘要，并保留供目标函数使用的复数序列。"""
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
        parsed = _parse_complex_sample(value)
        if parsed is None:
            return metric
        magnitude = math.hypot(parsed[0], parsed[1])
        db_values.append(safe_log_db(magnitude))
    minimum_index = db_values.index(min(db_values))
    metric["min_db"] = db_values[minimum_index]
    metric["best_freq"] = (
        xdata[minimum_index] if minimum_index < len(xdata) else None
    )
    series = _serialize_metric_series(xdata, ydata)
    if series is not None:
        series_freqs, series_points, downsampled = series
        metric["xdata"] = series_freqs
        metric["ydata"] = series_points
        if downsampled:
            metric["downsampled"] = True
            metric["source_point_count"] = len(db_values)
    return metric


def run_experiment(
    project_path: str,
    completion_result_paths: list[str],
    timeout_seconds: float | None = None,
    poll_interval_seconds: float = 10.0,
) -> OperationResult:
    """启动仿真并以新 Run ID 和指定非空结果节点确认完成。

    长任务让出（L1）：``timeout_seconds`` 省缺时按配置的
    ``long_run_threshold_seconds``（默认 600s，以 solver 实际运行时长
    计）在达到分界处返回 ``long_run_relinquish``——不做 postflight、
    不关闭工程、CST/DE 原样保留；显式传入数值则退回传统语义：
    该值即阻塞上限，到点返回 ``pipeline_sim_timeout``，不触发让出
    （CLI 用户传大值即可单次等待到底；MCP 治理层会拒绝超过其传输
    预算的值并引导 relay 模式）。
    """
    from ..core import phase_beacon as beacon
    from ..core.relinquish import build_relinquish_result

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

    auto_relinquish = timeout_seconds is None
    hard_cap = (
        max(float(timeout_seconds), 0.1) if timeout_seconds is not None else None
    )

    before: dict[str, set[int]] = {}
    missing_result_nodes: list[str] = []
    for result_path in normalized_paths:
        listed = _run_ids_for_path(project_path, result_path)
        if listed.get("status") == "error":
            if not _result_node_absent(project_path, result_path, dict(listed)):
                return error_result(
                    "completion_result_preflight_failed",
                    "求解前无法读取指定结果节点的 Run ID",
                    result_path=result_path,
                    detail=dict(listed),
                )
            # 首次仿真的正常初始状态：节点尚不存在，基线为空集
            before[result_path] = set()
            missing_result_nodes.append(result_path)
            continue
        before[result_path] = {int(item) for item in listed.get("run_ids", [])}

    beacon.write_phase(project_path, beacon.OPENING)
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
    beacon.write_phase(project_path, beacon.PREFLIGHT)
    started = start_simulation_async(project_path)
    if started.get("status") == "error":
        close_project(project_path, save=False)
        return error_result("pipeline_sim_start_failed", started.get("message", "启动仿真失败"))
    beacon.write_phase(project_path, beacon.POLLING)

    long_run_threshold = get_long_run_threshold()

    # 轮询间隔下限钳制，避免 poll_interval_seconds=0 时 CPU 空转自旋
    effective_poll = max(float(poll_interval_seconds), 0.1)
    polls = 0
    waited = 0.0
    while True:
        time.sleep(effective_poll)
        polls += 1
        waited += effective_poll
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
        if (
            auto_relinquish
            and bool(running.get("running"))
            and waited >= long_run_threshold
        ):
            # L1 让出：solver 口径到达长任务分界。不做 postflight、
            # 不关闭工程、CST/DE 原样保留；worker 随后由 MCP proxy 回收，
            # agent 收到 terminal payload 后停止等待并结束回合。
            return build_relinquish_result(
                project_path=str(opened.get("project_path", project_path)),
                waited_seconds=waited,
                polls=polls,
                long_run_threshold_seconds=long_run_threshold,
                source_tool="run-experiment",
                extra={
                    "completion_result_paths": normalized_paths,
                    "missing_result_nodes": missing_result_nodes,
                },
            )
        if hard_cap is not None and waited >= hard_cap:
            close_project(project_path, save=False)
            return error_result(
                "pipeline_sim_timeout",
                "等待仿真完成超时",
                polls=polls,
                timeout_seconds=hard_cap,
            )

    # 求解器停止后先检查本次求解新增的日志错误，把 CST 原始报错回传给调用方。
    beacon.write_phase(project_path, beacon.POSTFLIGHT)
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

    beacon.write_phase(project_path, beacon.CLOSING)
    closed = close_project(project_path, save=False)
    if closed.get("status") == "error":
        return error_result("pipeline_close_failed", closed.get("message", "关闭工程失败"))

    new_run_sets: list[set[int]] = []
    result_nodes_still_missing: list[str] = []
    for result_path in normalized_paths:
        listed = _run_ids_for_path(project_path, result_path)
        if listed.get("status") == "error":
            if not _result_node_absent(project_path, result_path, dict(listed)):
                return error_result(
                    "completion_result_postflight_failed",
                    "求解后无法读取指定结果节点的 Run ID",
                    result_path=result_path,
                    detail=dict(listed),
                )
            # 求解后节点仍不存在 → 视为本次没有生成该节点的新 Run ID
            new_run_sets.append(set())
            result_nodes_still_missing.append(result_path)
            continue
        after = {int(item) for item in listed.get("run_ids", [])}
        new_run_sets.append(after - before[result_path])
    common_new_runs = set.intersection(*new_run_sets) if new_run_sets else set()
    if not common_new_runs:
        return error_result(
            "solver_did_not_create_new_run",
            "指定完成节点没有共同的新 Run ID，不能确认本次求解完成",
            completion_result_paths=normalized_paths,
            missing_result_nodes=missing_result_nodes,
            result_nodes_still_missing=result_nodes_still_missing,
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
        missing_result_nodes=missing_result_nodes,
        cst_errors=diagnostics.get("errors", []),
        preflight_warnings=preflight_warnings,
    )
