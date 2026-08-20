from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import gateway
from . import process as process_cleanup
from . import identity as project_identity
from .compatibility import (
    connect_design_environment,
    create_design_environment,
    design_environment_pid,
    running_design_environment_pids,
)
from .errors import error_response
from .utils import abs_project_path as _abs_project_path

_OPENED_PROJECTS: dict[str, Any] = {}


@dataclass(frozen=True)
class _DesignEnvironmentLease:
    """记录 Design Environment 句柄及其关闭权限。"""

    environment: Any | None
    design_environment_pid: int | None
    runtime_owned: bool


class _ExistingSessionTakeoverRequired(RuntimeError):
    """只有已存在或归属不明确的 CST 会话可用时，要求用户确认。"""

    def __init__(self, candidate_pids: list[int], reason: str) -> None:
        self.candidate_pids = tuple(sorted(set(candidate_pids)))
        self.reason = reason
        super().__init__("接管已存在的 CST 会话前需要用户确认")


_OPENED_DESIGN_ENVIRONMENTS: dict[str, _DesignEnvironmentLease] = {}


def get_attached_project(project_path: str) -> dict[str, Any] | None:
    normalized = _abs_project_path(project_path)
    return _OPENED_PROJECTS.get(normalized)


def _connect_new_design_environment():
    return create_design_environment()


def _running_pid_set() -> set[int]:
    """取得当前可见的有效 Design Environment PID 集合。"""
    return {int(pid) for pid in running_design_environment_pids() if int(pid) > 0}


def _confirmation_required(
    project_path: str,
    candidate_pids: list[int] | tuple[int, ...],
    *,
    reason: str,
) -> dict[str, Any]:
    """构造必须先询问用户的两阶段确认响应。"""
    candidates = sorted(set(int(pid) for pid in candidate_pids))
    return error_response(
        "existing_session_confirmation_required",
        "检测到本次调用前已存在或归属不明确的 CST 会话；未经用户明确同意，"
        "Runtime 不会接管这些会话。",
        phase="confirmation",
        next_action=(
            "请向用户展示 candidate_design_environment_pids；仅在用户明确同意后，"
            "使用 confirm_existing_session_takeover=true 和 existing_session_pid 重试。"
        ),
        project_path=project_path,
        runtime_module="cst_runtime.core.session",
        requires_user_confirmation=True,
        confirmation_reason=reason,
        candidate_design_environment_pids=candidates,
        confirmation_arguments={
            "confirm_existing_session_takeover": True,
            "existing_session_pid": "<用户确认的 PID>",
        },
    )


def _connect_unique_new_design_environment(
    baseline_pids: set[int],
    *,
    deadline: float,
    original_error: Exception,
) -> Any:
    """仅连接基线之后唯一新增的 DE；旧 PID 或多候选必须由用户确认。"""
    last_running_pids = set(baseline_pids)
    last_connection_error: Exception | None = None
    while True:
        current_pids = _running_pid_set()
        last_running_pids = current_pids
        new_pids = sorted(current_pids - baseline_pids)
        if len(new_pids) == 1:
            try:
                return connect_design_environment(new_pids[0])
            except Exception as exc:
                last_connection_error = exc
        if time.monotonic() >= deadline:
            if len(new_pids) > 1:
                raise _ExistingSessionTakeoverRequired(
                    new_pids,
                    "multiple_new_sessions",
                ) from original_error
            preexisting_pids = sorted(last_running_pids & baseline_pids)
            if not new_pids and preexisting_pids:
                raise _ExistingSessionTakeoverRequired(
                    preexisting_pids,
                    "preexisting_sessions_only",
                ) from original_error
            if last_connection_error is not None:
                raise last_connection_error from original_error
            raise original_error
        time.sleep(0.5)


def _create_or_connect_design_environment(
    *,
    timeout_seconds: float = 120.0,
) -> tuple[Any, set[int]]:
    """创建 DE；CST 2022 冷启动时启动器会转交进程后退出。

    构造器与静态 new 都可能报 "Could not connect to a DE with pid"（实测
    构造函数在冷启动时直接抛 TimeoutError）。此时只允许连接启动基线之后
    唯一新增的 PID；已有 PID 或多个新增 PID 都必须先由用户确认。
    """
    baseline_pids = _running_pid_set()
    try:
        return _connect_new_design_environment(), baseline_pids
    except Exception as exc:
        if "pid" not in str(exc).casefold():
            raise
        deadline = time.monotonic() + max(timeout_seconds, 0.0)
        return (
            _connect_unique_new_design_environment(
                baseline_pids,
                deadline=deadline,
                original_error=exc,
            ),
            baseline_pids,
        )


def _open_project_with_pid_handoff_fallback(
    normalized_project: str,
    design_environment: Any,
    *,
    baseline_pids: set[int],
    handoff_timeout_seconds: float = 30.0,
) -> tuple[Any, Any]:
    """de.open_project 的 CST 2022 PID 交接回退，返回 (project, design_environment)。

    CST 2022 的启动器会把 DE 主窗口转交给另一个进程后退出；Python 对象
    仍按旧 PID 查找，报 "Could not connect to a DE with pid: X"。此时等待
    实际运行的 DE 出现，但只连接相对启动基线唯一新增的 PID。
    """
    try:
        return design_environment.open_project(normalized_project), design_environment
    except Exception as exc:
        if "pid" not in str(exc).casefold():
            raise
        deadline = time.monotonic() + max(handoff_timeout_seconds, 0.0)
        replacement = _connect_unique_new_design_environment(
            baseline_pids,
            deadline=deadline,
            original_error=exc,
        )
        return replacement.open_project(normalized_project), replacement


def inspect(project_path: str = "") -> dict[str, Any]:
    return process_cleanup.inspect_cst_environment(project_path=project_path)


def create_blank_project(project_path: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    if Path(normalized_project).is_file():
        return error_response(
            "project_already_exists",
            "project_path already exists; choose a different path or delete it first",
            project_path=normalized_project,
            runtime_module="cst_runtime.core.session",
        )
    project_dir = Path(normalized_project).parent
    project_dir.mkdir(parents=True, exist_ok=True)
    de = None
    try:
        de = create_design_environment()
        # 目前仅创建 MWS(微波工作室)。若需拓展其他类型，可用：
        # de.new_cs() / new_ds() / new_ems() / new_fd3d() / new_mps() / new_pcbs() / new_ps()
        project = de.new_mws()
        project.save(normalized_project)
        _OPENED_PROJECTS[normalized_project] = project
        _OPENED_DESIGN_ENVIRONMENTS[normalized_project] = _DesignEnvironmentLease(
            environment=de,
            design_environment_pid=design_environment_pid(de),
            runtime_owned=True,
        )
        gateway.on_session_open(normalized_project, "modeler")
        return {
            "status": "success",
            "project_path": normalized_project,
            "session_action": "create",
            "runtime_module": "cst_runtime.core.session",
        }
    except Exception as exc:
        # 创建失败时也要关闭刚启动的空白 Design Environment。
        if de is not None:
            try:
                de.close()
            except Exception:
                pass
        return error_response(
            "create_blank_project_failed",
            str(exc),
            project_path=normalized_project,
            runtime_module="cst_runtime.core.session",
        )


def open_project(
    project_path: str,
    *,
    confirm_existing_session_takeover: bool = False,
    existing_session_pid: int | None = None,
) -> dict[str, Any]:
    """打开一个已经存在的 CST 工程。
    
    该方法会检查文件是否存在，然后调用 CST 的 COM 接口将其打开。
    若工程已在其他会话打开，首次调用只返回候选 PID；取得用户确认后才会附着。

    Args:
        project_path: CST 工程文件的绝对或相对路径（如 "model.cst"）。
        confirm_existing_session_takeover: 用户是否已明确同意接管已有 CST 会话。
        existing_session_pid: 用户明确确认的已有 Design Environment PID。

    Returns:
        返回一个包含执行状态的字典。成功时 status 为 "success"。
    """
    normalized_project = _abs_project_path(project_path)
    if type(confirm_existing_session_takeover) is not bool:
        return error_response(
            "invalid_arguments",
            "confirm_existing_session_takeover 必须是布尔值",
            phase="validation",
            project_path=normalized_project,
            runtime_module="cst_runtime.core.session",
        )
    if existing_session_pid is not None and (
        type(existing_session_pid) is not int or existing_session_pid <= 0
    ):
        return error_response(
            "invalid_arguments",
            "existing_session_pid 必须是大于 0 的整数 PID",
            phase="validation",
            project_path=normalized_project,
            runtime_module="cst_runtime.core.session",
        )
    has_confirmed_pid = existing_session_pid is not None
    if confirm_existing_session_takeover != has_confirmed_pid:
        return error_response(
            "invalid_arguments",
            "confirm_existing_session_takeover 与 existing_session_pid 必须同时提供；"
            "不得在未取得用户明确同意时单独设置其中一个参数。",
            phase="validation",
            project_path=normalized_project,
            runtime_module="cst_runtime.core.session",
        )
    confirmed_pid = existing_session_pid
    if not Path(normalized_project).is_file():
        return error_response(
            "project_file_missing",
            "project_path does not exist",
            project_path=normalized_project,
            runtime_module="cst_runtime.core.session",
        )

    cached_project = _OPENED_PROJECTS.get(normalized_project)
    if cached_project is not None:
        return {
            "status": "success",
            "project_path": normalized_project,
            "already_open": True,
            "session_action": "open",
            "attachment_source": "runtime_cache",
            "post_inspect": inspect(project_path),
            "runtime_module": "cst_runtime.core.session",
        }

    if confirmed_pid is None:
        try:
            preexisting_pids = _running_pid_set()
            candidate_pids, _discovery_status = (
                project_identity.discover_expected_project_pids(
                    normalized_project,
                    preexisting_pids,
                )
            )
        except Exception as exc:
            return error_response(
                "existing_session_discovery_failed",
                str(exc),
                phase="discovery",
                project_path=normalized_project,
                runtime_module="cst_runtime.core.session",
            )
        if candidate_pids:
            return _confirmation_required(
                normalized_project,
                candidate_pids,
                reason="target_project_already_open",
            )

    de = None
    runtime_owned = False
    try:
        # CST 2022 必须遵循官方顺序：先创建 DesignEnvironment，再由该对象打开工程。
        # 若把 --project-file 传给 DesignEnvironment.new()，启动器可能转交到其他进程，
        # 导致 Python 接口仍按原 PID 查找并报错“No DE found with pid”。
        # 冷启动时构造/静态 new 也可能报 "Could not connect to a DE with pid"，
        # 由 _create_or_connect_design_environment 等待真实 DE 后按官方路径接管；
        # 旧句柄在 open_project 时报同样的 PID 错误时由
        # _open_project_with_pid_handoff_fallback 换新句柄重试。
        if confirmed_pid is not None:
            project, de, attachment_status = (
                project_identity.attach_expected_project_at_pid(
                    normalized_project,
                    confirmed_pid,
                )
            )
            if de is None:
                return {
                    **attachment_status,
                    "session_action": "open",
                    "project_path": normalized_project,
                    "confirmed_existing_session_pid": confirmed_pid,
                    "runtime_module": "cst_runtime.core.session",
                }
            already_open = project is not None
            if project is None:
                if attachment_status.get("error_type") != "project_not_open":
                    return {
                        **attachment_status,
                        "session_action": "open",
                        "project_path": normalized_project,
                        "confirmed_existing_session_pid": confirmed_pid,
                        "runtime_module": "cst_runtime.core.session",
                    }
                # 用户只确认了这个 PID；这里不允许再回退到其他会话。
                project = de.open_project(normalized_project)
            runtime_owned = False
        else:
            de, startup_baseline_pids = _create_or_connect_design_environment()
            runtime_owned = True
            already_open = False
            # 打开工程可能再次触发 PID 交接；把当前新建 DE 也纳入基线，
            # 避免把它与随后真正新增的交接 PID 混在一起。
            handoff_baseline_pids = startup_baseline_pids | _running_pid_set()

            # PROFILING
            import time
            from . import utils as core_utils
            is_profile = hasattr(core_utils, "_PROFILE_DATA")
            if is_profile and core_utils._PROFILE_DATA["t_com_begin"] == 0:
                core_utils._PROFILE_DATA["t_com_begin"] = time.perf_counter()

            project, de = _open_project_with_pid_handoff_fallback(
                normalized_project,
                de,
                baseline_pids=handoff_baseline_pids,
            )

            # PROFILING
            if is_profile and core_utils._PROFILE_DATA["t_com_end"] == 0:
                core_utils._PROFILE_DATA["t_com_end"] = time.perf_counter()
            
        _OPENED_PROJECTS[normalized_project] = project
        _OPENED_DESIGN_ENVIRONMENTS[normalized_project] = _DesignEnvironmentLease(
            environment=de,
            design_environment_pid=(
                confirmed_pid if confirmed_pid is not None else design_environment_pid(de)
            ),
            runtime_owned=runtime_owned,
        )
        gateway.on_session_open(normalized_project, "modeler")
        return {
            "status": "success",
            "project_path": normalized_project,
            "already_open": already_open,
            "session_action": "open",
            "design_environment_ownership": (
                "runtime_owned" if runtime_owned else "user_confirmed"
            ),
            "confirmed_existing_session_pid": confirmed_pid,
            "post_inspect": inspect(project_path),
            "runtime_module": "cst_runtime.core.session",
        }
    except _ExistingSessionTakeoverRequired as exc:
        if de is not None and runtime_owned:
            try:
                de.close()
            except Exception:
                pass
        return _confirmation_required(
            normalized_project,
            exc.candidate_pids,
            reason=exc.reason,
        )
    except Exception as exc:
        # 仅释放本次调用创建的空白 CST 窗口；用户确认接管的 DE 绝不关闭。
        if de is not None and runtime_owned:
            try:
                de.close()
            except Exception:
                pass
        return error_response(
            "open_project_failed",
            str(exc),
            project_path=normalized_project,
            runtime_module="cst_runtime.core.session",
        )


def reattach_project(
    project_path: str,
    *,
    confirm_existing_session_takeover: bool = False,
    existing_session_pid: int | None = None,
) -> dict[str, Any]:
    """在用户确认后，只按指定 PID 重新附着已有工程。"""
    normalized_project = _abs_project_path(project_path)
    if type(confirm_existing_session_takeover) is not bool:
        return error_response(
            "invalid_arguments",
            "confirm_existing_session_takeover 必须是布尔值",
            phase="validation",
            project_path=normalized_project,
            runtime_module="cst_runtime.core.session",
        )
    if existing_session_pid is not None and (
        type(existing_session_pid) is not int or existing_session_pid <= 0
    ):
        return error_response(
            "invalid_arguments",
            "existing_session_pid 必须是大于 0 的整数 PID",
            phase="validation",
            project_path=normalized_project,
            runtime_module="cst_runtime.core.session",
        )
    if confirm_existing_session_takeover != (existing_session_pid is not None):
        return error_response(
            "invalid_arguments",
            "confirm_existing_session_takeover 与 existing_session_pid 必须同时提供",
            phase="validation",
            project_path=normalized_project,
            runtime_module="cst_runtime.core.session",
        )

    if normalized_project in _OPENED_PROJECTS:
        return {
            "status": "success",
            "session_action": "reattach",
            "attachment_source": "runtime_cache",
            "post_inspect": inspect(project_path),
            "runtime_module": "cst_runtime.core.session",
        }

    if existing_session_pid is None:
        try:
            candidate_pids, _discovery_status = (
                project_identity.discover_expected_project_pids(
                    normalized_project,
                    _running_pid_set(),
                )
            )
        except Exception as exc:
            return error_response(
                "existing_session_discovery_failed",
                str(exc),
                phase="discovery",
                project_path=normalized_project,
                runtime_module="cst_runtime.core.session",
            )
        if candidate_pids:
            return _confirmation_required(
                normalized_project,
                candidate_pids,
                reason="reattach_existing_project",
            )
        return error_response(
            "project_not_open",
            "目标工程未在可见的 CST 会话中打开",
            project_path=normalized_project,
            runtime_module="cst_runtime.core.session",
        )

    project, de, status = project_identity.attach_expected_project_at_pid(
        normalized_project,
        existing_session_pid,
    )
    if project is None or de is None:
        return {
            **status,
            "session_action": "reattach",
            "project_path": normalized_project,
            "confirmed_existing_session_pid": existing_session_pid,
            "runtime_module": "cst_runtime.core.session",
        }

    _OPENED_PROJECTS[normalized_project] = project
    _OPENED_DESIGN_ENVIRONMENTS[normalized_project] = _DesignEnvironmentLease(
        environment=de,
        design_environment_pid=existing_session_pid,
        runtime_owned=False,
    )
    gateway.on_session_open(normalized_project, "modeler")
    return {
        **status,
        "session_action": "reattach",
        "design_environment_ownership": "user_confirmed",
        "confirmed_existing_session_pid": existing_session_pid,
        "post_inspect": inspect(project_path),
        "runtime_module": "cst_runtime.core.session",
    }


def close_project(
    project_path: str,
    save: bool = False,
    wait_unlock: bool = True,
    timeout_seconds: float = 30.0,
    poll_interval_seconds: float = 0.5,
    kill_processes: bool = False,
) -> dict[str, Any]:
    """安全关闭当前正在运行的 CST 工程。
    
    这是工业级脚本中最核心的安全函数。它不仅会关闭工程，还会通过进程表检查确保
    CST 释放了 .lock 锁定文件。如果出现僵尸进程，它会强制终结它们，防止后续仿真卡死。

    Args:
        project_path: 工程路径。
        save: 关闭前是否保存工程。
        wait_unlock: 是否阻塞等待直到 CST 的文件锁 (.lock) 彻底释放。
        timeout_seconds: 等待文件锁释放的最长超时时间。
        kill_processes: 关闭后是否强制杀死遗留的 "DESIGN ENVIRONMENT" 进程。

    Returns:
        包含清理结果的字典，包括是否成功保存、进程是否已被终结等信息。
    """
    normalized_project = _abs_project_path(project_path)

    # T3: refuse save after farfield export
    effective_save = save
    t3_warning = ""
    if save:
        effective_save, t3_warning = gateway.guard_before_close_save(normalized_project, save)

    cached_project = _OPENED_PROJECTS.get(normalized_project)
    environment_lease = _OPENED_DESIGN_ENVIRONMENTS.get(normalized_project)
    registered_de = environment_lease.environment if environment_lease is not None else None
    registered_de_pid = (
        environment_lease.design_environment_pid
        if environment_lease is not None
        else None
    )
    runtime_owned_environment = bool(
        environment_lease is not None and environment_lease.runtime_owned
    )
    if cached_project is not None:
        project = cached_project
        a_status = {
            "status": "success",
            "attachment_source": "runtime_cache",
            "design_environment_pid": registered_de_pid,
        }
    else:
        project, a_status = project_identity.attach_expected_project(normalized_project)
    de_pid: int | None = registered_de_pid or a_status.get("design_environment_pid")
    had_dirty_state = gateway.has_dirty_state(normalized_project)
    close_result: dict[str, Any] = a_status if project is None else {"status": "success"}
    if project is not None:
        try:
            # PROFILING
            import time
            from . import utils as core_utils
            is_profile = hasattr(core_utils, "_PROFILE_DATA")
            if is_profile and core_utils._PROFILE_DATA["t_com_begin"] == 0:
                core_utils._PROFILE_DATA["t_com_begin"] = time.perf_counter()
                
            if effective_save:
                project.save()
            project.close()
            environment_closed = False
            if registered_de is not None and runtime_owned_environment:
                # 只有 Runtime 明确创建的环境才有权关闭；用户确认接管的环境只关闭工程。
                registered_de.close()
                environment_closed = True
            
            # PROFILING
            if is_profile and core_utils._PROFILE_DATA["t_com_end"] == 0:
                core_utils._PROFILE_DATA["t_com_end"] = time.perf_counter()
                
            close_result = {
                "status": "success",
                "project_path": normalized_project,
                "saved": effective_save,
                "environment_closed": environment_closed,
                "environment_owned_by_runtime": runtime_owned_environment,
            }
            if t3_warning:
                close_result["t3_warning"] = t3_warning
                close_result["requested_save"] = True
                close_result["trap"] = "T3_farfield_export_save_forced_false"
            # 保存与关闭成功后才清理运行时状态（含 T2 脏标记）；
            # 若提前清理，save=False/保存失败会静默丢失未落盘的参数改动。
            _OPENED_PROJECTS.pop(normalized_project, None)
            _OPENED_DESIGN_ENVIRONMENTS.pop(normalized_project, None)
            gateway.on_session_close(normalized_project)
            if not effective_save and had_dirty_state:
                close_result["warning"] = (
                    "close 时 save=False 且存在未保存的参数改动；"
                    "改动未落盘，重新打开将使用磁盘上的旧参数"
                )
        except Exception as exc:
            # 关闭失败：保留注册表与脏标记，便于上层重试与诊断
            close_result = error_response(
                "close_project_failed",
                str(exc),
                project_path=normalized_project,
                runtime_module="cst_runtime.core.session",
            )
    else:
        # 无法取得工程对象时仍要清理本 Worker 的运行时注册状态
        _OPENED_PROJECTS.pop(normalized_project, None)
        _OPENED_DESIGN_ENVIRONMENTS.pop(normalized_project, None)
        gateway.on_session_close(normalized_project)

    unlock_result: dict[str, Any] | None = None
    if close_result.get("status") != "error" and wait_unlock:
        unlock_result = project_identity.wait_project_unlocked(
            project_path=project_path,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )

    kill_result: dict[str, Any] | None = None
    if close_result.get("status") != "error" and kill_processes and not runtime_owned_environment:
        kill_result = error_response(
            "design_environment_not_owned",
            "拒绝终止非 Runtime 所有的 CST Design Environment；"
            "用户对接管工程的确认不等于同意关闭整个 CST 会话。",
            phase="validation",
            project_path=normalized_project,
            design_environment_pid=de_pid,
        )
    elif close_result.get("status") != "error" and kill_processes and de_pid:
        kill_result = process_cleanup.stop_process(de_pid, "CST DESIGN ENVIRONMENT_AMD64")
    else:
        kill_result = None

    # 不扫描或终止其他 CST 会话；只允许处理已与当前项目关联的 PID。
    orphan_result: dict[str, Any] | None = None

    status = "success"
    if (
        close_result.get("status") == "error"
        or (unlock_result or {}).get("status") == "error"
        or (
            kill_processes
            and (kill_result or {}).get("status") == "error"
        )
    ):
        status = "error"
    payload: dict[str, Any] = {
        "status": status,
        "session_action": "close",
        "project_path": project_path,
        "save": save,
        "close_result": close_result,
        "unlock_result": unlock_result,
        "kill_result": kill_result,
        "orphan_result": orphan_result,
        "post_inspect": inspect(project_path),
        "runtime_module": "cst_runtime.core.session",
    }
    if status == "error":
        payload["error_type"] = "session_close_failed"
        payload["message"] = "关闭工程、释放文件锁或退出关联 CST 进程失败"
    return payload


def quit_cst(
    project_path: str = "",
    dry_run: bool = False,
    settle_seconds: float = 0.5,
    force_global_cleanup: bool = False,
) -> dict[str, Any]:
    """彻底退出整个 CST 应用程序实例并清理所有相关的后台子进程。
    
    默认只允许终止本 Runtime 明确创建并登记的 Design Environment；
    全局扫描仅用于 dry_run 或显式 force_global_cleanup。

    Args:
        project_path: 可选的工程路径，用于精准定位它的子进程。
        dry_run: 若为 True，则只扫描不实际杀死进程（用于调试）。
        settle_seconds: 杀死进程后的冷却时间。

    Returns:
        清理报告字典。
    """
    before = inspect(project_path)
    if dry_run or force_global_cleanup:
        cleanup = process_cleanup.cleanup_cst_processes(
            project_path=project_path,
            dry_run=dry_run,
            settle_seconds=settle_seconds,
        )
    elif not project_path:
        cleanup = error_response(
            "session_scope_required",
            "非 dry-run 退出必须提供 project_path；全局清理需显式启用 force_global_cleanup",
            runtime_module="cst_runtime.core.session",
        )
    else:
        normalized_project = _abs_project_path(project_path)
        environment_lease = _OPENED_DESIGN_ENVIRONMENTS.get(normalized_project)
        if environment_lease is None or not environment_lease.runtime_owned:
            cleanup = error_response(
                "design_environment_not_owned",
                "拒绝终止非 Runtime 所有或所有权未知的 CST Design Environment",
                project_path=project_path,
                design_environment_pid=(
                    environment_lease.design_environment_pid
                    if environment_lease is not None
                    else None
                ),
                runtime_module="cst_runtime.core.session",
            )
        elif environment_lease.design_environment_pid:
            cleanup = process_cleanup.stop_process(
                environment_lease.design_environment_pid,
                "CST DESIGN ENVIRONMENT_AMD64",
            )
        else:
            cleanup = error_response(
                "owned_process_not_found",
                "未找到与指定项目关联的 CST 进程，拒绝执行全局清理",
                project_path=project_path,
                runtime_module="cst_runtime.core.session",
            )
    after = inspect(project_path)
    status = "success" if cleanup.get("status") != "error" else "error"
    payload: dict[str, Any] = {
        "status": status,
        "session_action": "quit",
        "project_path": project_path,
        "dry_run": dry_run,
        "pre_inspect": before,
        "cleanup_result": cleanup,
        "post_inspect": after,
        "runtime_module": "cst_runtime.core.session",
    }
    if status == "error":
        payload["error_type"] = "session_quit_failed"
        payload["message"] = "cleanup_cst_processes did not finish cleanly"
    return payload
