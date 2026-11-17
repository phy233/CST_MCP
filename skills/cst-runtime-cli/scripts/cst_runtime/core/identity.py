from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from .compatibility import (
    activate_project,
    active_project,
    connect_design_environment,
    connect_to_any_design_environment,
    design_environment_pid,
    get_open_project,
    has_active_project,
    list_open_project_paths,
    running_design_environment_pids,
)
from .errors import error_response


def normalize_project_path(path: str) -> str:
    return os.path.normcase(os.path.abspath(os.path.expanduser(path)))


def project_path_from_args(args: dict[str, Any]) -> str:
    project_path = args.get("project_path") or args.get("fullpath") or args.get("working_project")
    if not project_path:
        raise ValueError("project_path is required")
    return str(project_path)


def infer_run_dir_from_project(project_path: str) -> Path | None:
    path = Path(project_path).expanduser().resolve()
    if path.parent.name.lower() == "projects":
        return path.parent.parent
    return None


def _project_companion_dir(project_path: str) -> Path:
    path = Path(project_path).expanduser().resolve()
    if path.suffix.lower() != ".cst":
        path = path.with_suffix(".cst")
    return path.with_suffix("")


def find_lock_files(project_path: str) -> list[Path]:
    companion_dir = _project_companion_dir(project_path)
    if not companion_dir.exists():
        return []
    return sorted(companion_dir.rglob("*.lok"))


def wait_project_unlocked(
    project_path: str,
    timeout_seconds: float = 10.0,
    poll_interval_seconds: float = 0.5,
) -> dict[str, Any]:
    started = time.monotonic()
    last_locks: list[Path] = []
    while True:
        last_locks = find_lock_files(project_path)
        if not last_locks:
            return {
                "status": "success",
                "project_path": os.path.abspath(project_path),
                "locked": False,
                "waited_seconds": round(time.monotonic() - started, 3),
                "runtime_module": "cst_runtime.core.identity",
            }
        if time.monotonic() - started >= timeout_seconds:
            return error_response(
                "lock_not_released",
                "project lock files still exist after timeout",
                project_path=os.path.abspath(project_path),
                locked=True,
                lock_files=[path.as_posix() for path in last_locks],
                timeout_seconds=timeout_seconds,
                runtime_module="cst_runtime.core.identity",
            )
        time.sleep(poll_interval_seconds)


def _connect_to_any():
    try:
        return connect_to_any_design_environment()
    except Exception as exc:
        return None, str(exc)


def _discover_design_environment_pids() -> list[int]:
    try:
        return running_design_environment_pids()
    except Exception:
        return []


def _connected_design_environments() -> tuple[list[tuple[Any, int | None]], str]:
    environments: list[tuple[Any, int | None]] = []
    errors: list[str] = []
    seen: set[int] = set()
    for pid in _discover_design_environment_pids():
        try:
            de = connect_design_environment(pid)
            environments.append((de, pid))
            seen.add(pid)
        except Exception as exc:
            errors.append(f"{pid}: {exc}")

    if not environments:
        connected = _connect_to_any()
        if isinstance(connected, tuple):
            errors.append(connected[1])
        else:
            pid = design_environment_pid(connected)
            if pid is None or pid not in seen:
                environments.append((connected, pid))

    return environments, "; ".join(error for error in errors if error)


def _active_project_filename(de: Any) -> str:
    active = active_project(de)
    if active is None:
        raise RuntimeError("CST 会话没有活动工程")
    return str(active.filename())


def list_open_projects() -> dict[str, Any]:
    environments, errors = _connected_design_environments()
    if not environments:
        return error_response(
            "no_cst_session",
            errors or "No DEs found to connect to.",
            open_projects=[],
            runtime_module="cst_runtime.core.identity",
        )
    projects: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for de, pid in environments:
        try:
            paths = list_open_project_paths(de)
        except Exception as exc:
            failures.append({"design_environment_pid": pid, "error": str(exc)})
            continue
        projects.extend(
            {
                "project_path": os.path.abspath(path),
                "project_name": Path(path).stem,
                "design_environment_pid": pid,
            }
            for path in paths
        )
    if failures and not projects:
        return error_response(
            "list_open_projects_failed",
            "Could not list open projects from any CST Design Environment.",
            open_projects=[],
            failures=failures,
            runtime_module="cst_runtime.core.identity",
        )
    return {
        "status": "success",
        "open_projects": projects,
        "count": len(projects),
        "design_environment_count": len(environments),
        "failures": failures,
        "runtime_module": "cst_runtime.core.identity",
    }


def discover_expected_project_pids(
    project_path: str,
    design_environment_pids: set[int],
) -> tuple[list[int], dict[str, Any]]:
    """只读查找已打开目标工程的 PID，不激活工程或保留会话句柄。"""
    expected = normalize_project_path(project_path)
    matches: list[int] = []
    failures: list[dict[str, Any]] = []
    for pid in sorted(design_environment_pids):
        try:
            de = connect_design_environment(pid)
            open_projects = list_open_project_paths(de)
        except Exception as exc:
            failures.append({"design_environment_pid": pid, "error": str(exc)})
            continue
        if any(
            normalize_project_path(str(path)) == expected
            for path in open_projects
        ):
            matches.append(pid)
    return matches, {
        "status": "success",
        "candidate_design_environment_pids": matches,
        "failures": failures,
        "runtime_module": "cst_runtime.core.identity",
    }


def _attach_expected_project_in_environment(
    project_path: str,
    de: Any,
    pid: int | None,
) -> tuple[Any | None, dict[str, Any]]:
    """仅在给定 Design Environment 内取得并激活目标工程。"""
    expected = normalize_project_path(project_path)
    try:
        open_projects = list_open_project_paths(de)
    except Exception as exc:
        return None, error_response(
            "list_open_projects_failed",
            str(exc),
            expected_project_path=os.path.abspath(project_path),
            design_environment_pid=pid,
            runtime_module="cst_runtime.core.identity",
        )

    matching_projects = [
        path
        for path in open_projects
        if normalize_project_path(str(path)) == expected
    ]
    if not matching_projects:
        return None, error_response(
            "project_not_open",
            "expected project is not open in CST",
            expected_project_path=os.path.abspath(project_path),
            open_projects=[str(path) for path in open_projects],
            design_environment_pid=pid,
            runtime_module="cst_runtime.core.identity",
        )

    was_activated = False
    try:
        active_path = normalize_project_path(_active_project_filename(de))
    except Exception:
        active_path = ""
    if active_path != expected:
        try:
            activate_project(de, get_open_project(de, str(matching_projects[0])))
            was_activated = True
        except Exception as exc:
            return None, error_response(
                "activate_project_failed",
                f"Failed to activate expected project: {exc}",
                expected_project_path=os.path.abspath(project_path),
                open_projects=[str(path) for path in open_projects],
                design_environment_pid=pid,
                runtime_module="cst_runtime.core.identity",
            )

    try:
        if not has_active_project(de):
            return None, error_response(
                "no_active_project",
                "CST session has no active project",
                expected_project_path=os.path.abspath(project_path),
                open_projects=[str(path) for path in open_projects],
                design_environment_pid=pid,
                runtime_module="cst_runtime.core.identity",
            )
        active = active_project(de)
        if active is None:
            raise RuntimeError("CST 会话没有活动工程")
        active_path = normalize_project_path(str(active.filename()))
        if active_path != expected:
            return None, error_response(
                "active_project_mismatch",
                "Activated project does not match expected project",
                expected_project_path=os.path.abspath(project_path),
                active_project_path=active_path,
                open_projects=[str(path) for path in open_projects],
                design_environment_pid=pid,
                runtime_module="cst_runtime.core.identity",
            )
        return active, {
            "status": "success",
            "expected_project_path": os.path.abspath(project_path),
            "open_projects": [str(path) for path in open_projects],
            "design_environment_pid": pid,
            "was_activated": was_activated,
            "runtime_module": "cst_runtime.core.identity",
        }
    except Exception as exc:
        return None, error_response(
            "attach_active_project_failed",
            str(exc),
            expected_project_path=os.path.abspath(project_path),
            open_projects=[str(path) for path in open_projects],
            design_environment_pid=pid,
            runtime_module="cst_runtime.core.identity",
        )


def attach_expected_project_at_pid(
    project_path: str,
    design_environment_pid: int,
) -> tuple[Any | None, Any | None, dict[str, Any]]:
    """只连接用户指定的 PID，并在该会话内取得目标工程。"""
    try:
        de = connect_design_environment(design_environment_pid)
    except Exception as exc:
        return None, None, error_response(
            "design_environment_connect_failed",
            str(exc),
            expected_project_path=os.path.abspath(project_path),
            design_environment_pid=design_environment_pid,
            runtime_module="cst_runtime.core.identity",
        )
    project, status = _attach_expected_project_in_environment(
        project_path,
        de,
        design_environment_pid,
    )
    return project, de, status


def attach_expected_project(project_path: str) -> tuple[Any | None, dict[str, Any]]:
    environments, errors = _connected_design_environments()
    if not environments:
        return None, error_response(
            "no_cst_session",
            errors or "No DEs found to connect to.",
            expected_project_path=os.path.abspath(project_path),
            runtime_module="cst_runtime.core.identity",
        )

    all_open_projects: list[str] = []
    failures: list[dict[str, Any]] = []
    for de, pid in environments:
        project, status = _attach_expected_project_in_environment(project_path, de, pid)
        all_open_projects.extend(status.get("open_projects", []))
        if project is not None:
            return project, status
        error_type = status.get("error_type")
        if error_type == "list_open_projects_failed":
            failures.append({
                "design_environment_pid": pid,
                "error": status.get("message", "无法列出工程"),
            })
            continue
        if error_type != "project_not_open":
            return None, status

    return None, error_response(
        "project_not_open",
        "expected project is not open in CST",
        expected_project_path=os.path.abspath(project_path),
        open_projects=all_open_projects,
        failures=failures,
        runtime_module="cst_runtime.core.identity",
    )


def verify_project_identity(project_path: str) -> dict[str, Any]:
    _, status = attach_expected_project(project_path)
    return status


def probe_target_solver_state(
    project_path: str,
    design_environment_pid: int | None = None,
) -> dict[str, Any]:
    """只读探测目标工程的求解器状态，绝不激活、保存、关闭或新建工程。"""
    runtime_module = "cst_runtime.core.identity"
    if not project_path:
        return error_response(
            "solver_state_unreadable",
            "project_path is required to probe target solver state",
            project_path="",
            design_environment_pid=design_environment_pid,
            running=None,
            runtime_module=runtime_module,
        )
    absolute = os.path.abspath(os.path.expanduser(str(project_path)))
    expected = normalize_project_path(str(project_path))

    pid_filter: int | None = None
    if design_environment_pid is not None:
        try:
            pid_filter = int(design_environment_pid)
        except (TypeError, ValueError):
            return error_response(
                "solver_state_unreadable",
                f"design_environment_pid is not a valid integer: {design_environment_pid!r}",
                project_path=absolute,
                design_environment_pid=None,
                running=None,
                runtime_module=runtime_module,
            )

    if pid_filter is not None:
        try:
            environment = connect_design_environment(pid_filter)
        except Exception as exc:
            return error_response(
                "solver_state_unreadable",
                f"failed to connect to Design Environment {pid_filter}: {exc}",
                project_path=absolute,
                design_environment_pid=pid_filter,
                running=None,
                runtime_module=runtime_module,
            )
        environments: list[tuple[Any, int | None]] = [(environment, pid_filter)]
    else:
        environments, connection_errors = _connected_design_environments()
        if not environments:
            if _discover_design_environment_pids():
                return error_response(
                    "solver_state_unreadable",
                    "could not connect to a visible CST Design Environment"
                    + (f": {connection_errors}" if connection_errors else ""),
                    project_path=absolute,
                    design_environment_pid=None,
                    running=None,
                    runtime_module=runtime_module,
                )
            return {
                "status": "not_open",
                "project_path": absolute,
                "design_environment_pid": None,
                "running": False,
                "runtime_module": runtime_module,
            }

    errors: list[str] = []
    matched: tuple[Any, int | None] | None = None
    for environment, environment_pid in environments:
        label = str(environment_pid) if environment_pid is not None else "unknown-pid"
        try:
            open_paths = list_open_project_paths(environment)
        except Exception as exc:
            errors.append(f"{label}: {exc}")
            continue
        matching_paths = [
            str(path)
            for path in open_paths
            if normalize_project_path(str(path)) == expected
        ]
        if not matching_paths:
            continue
        project = None
        for matching_path in matching_paths:
            try:
                project = get_open_project(environment, matching_path)
                break
            except Exception:
                project = None
        if project is None:
            # 回退：仅当活动工程确实是目标工程时使用；绝不激活任何工程。
            try:
                candidate = active_project(environment)
                candidate_name = (
                    getattr(candidate, "filename", None) if candidate is not None else None
                )
                candidate_value = (
                    candidate_name() if callable(candidate_name) else candidate_name
                )
                if (
                    candidate_value
                    and normalize_project_path(str(candidate_value)) == expected
                ):
                    project = candidate
            except Exception as exc:
                errors.append(f"{label}: {exc}")
                project = None
        if project is None:
            errors.append(f"{label}: target project handle is not readable")
            continue
        matched = (project, environment_pid)
        break

    if matched is None:
        if errors:
            return error_response(
                "solver_state_unreadable",
                "could not read the target project solver state: " + "; ".join(errors),
                project_path=absolute,
                design_environment_pid=pid_filter,
                running=None,
                runtime_module=runtime_module,
            )
        return {
            "status": "not_open",
            "project_path": absolute,
            "design_environment_pid": None,
            "running": False,
            "runtime_module": runtime_module,
        }

    project, matched_pid = matched
    try:
        modeler = project.modeler
        reader = getattr(modeler, "is_solver_running", None)
        if reader is None:
            raise RuntimeError("project.modeler.is_solver_running is not available")
        running = bool(reader() if callable(reader) else reader)
    except Exception as exc:
        return error_response(
            "solver_state_unreadable",
            f"failed to read target solver state: {exc}",
            project_path=absolute,
            design_environment_pid=matched_pid,
            running=None,
            runtime_module=runtime_module,
        )

    return {
        "status": "success",
        "project_path": absolute,
        "design_environment_pid": matched_pid,
        "running": running,
        "runtime_module": runtime_module,
    }
