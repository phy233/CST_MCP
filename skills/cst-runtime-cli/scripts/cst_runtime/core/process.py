"""CST 进程发现、分类与目标工程范围的清理。

"CST_FORCE_KILL_PROCESS_ALLOWLIST" / "_load_allowlist()" 只用于“发现并分类”
CST 相关进程（许可证服务、DC 基础服务、Design Environment），它不是默认终止清单。
是否允许终止某个进程必须由目标工程身份、Runtime 会话归属和显式用户授权共同决定；
共享许可证/DC 服务与无关 Design Environment 永远不是清理候选，也永远不因
“白名单里有进程存在”而阻塞目标操作。
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import warnings
from pathlib import Path
from typing import Any

from . import identity as project_identity, workspace
from .errors import error_response
from .identity import find_lock_files
from .utils import abs_project_path

_ALLOWED_OPERATIONS: tuple[str, ...] = ("inspect", "read", "write", "solve", "copy", "reopen")
_ALLOWED_OPERATION_SET = frozenset(_ALLOWED_OPERATIONS)
_DEFAULT_OPERATION = "inspect"
_WRITE_SOLVE_OPERATIONS = frozenset({"write", "solve"})
_COPY_REOPEN_OPERATIONS = frozenset({"copy", "reopen"})
_OCCUPANCY_ERROR_TYPES = frozenset(
    {
        "list_open_projects_failed",
        "attach_active_project_failed",
        "no_active_project",
        "active_project_mismatch",
        "activate_project_failed",
        "design_environment_connect_failed",
        "existing_session_discovery_failed",
    }
)
_IDENTITY_AMBIGUITY_ERROR = "ambiguous_open_projects"
_CLEANUP_REQUIRED_CONFLICT_KINDS = frozenset(
    {"target_lock_without_visible_session", "target_session_ambiguous", "target_occupancy_unconfirmed"}
)
_TARGET_RELEASE_CONFLICT_KINDS = frozenset(
    {"target_project_open", "target_lock_without_visible_session", "target_session_ambiguous"}
)
_RUNTIME_MODULE = "cst_runtime.core.process"


def _load_allowlist() -> list[str]:
    """加载CST进程白名单配置，带错误处理和回退"""
    workspace_root, _, _ = workspace.resolve_workspace_root("")
    config_path = workspace_root / "cst_process_allowlist.json"
    default_allowlist = [
        "cstd",
        "CST DESIGN ENVIRONMENT_AMD64",
        "CSTDCMainController_AMD64",
        "CSTDCSolverServer_AMD64",
    ]
    
    if not config_path.exists():
        return default_allowlist
    
    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
            allowlist = config.get("cst_force_kill_process_allowlist", [])
            if not allowlist:
                warnings.warn(
                    f"Empty allowlist in {config_path}, using default",
                    UserWarning
                )
                return default_allowlist
            return allowlist
    except Exception as exc:
        warnings.warn(
            f"Failed to load allowlist from {config_path}: {exc}, using default",
            UserWarning
        )
        return default_allowlist

CST_FORCE_KILL_PROCESS_ALLOWLIST = _load_allowlist()


def _run_powershell(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )


def _loads_json_array(text: str) -> list[dict[str, Any]]:
    stripped = text.strip()
    if not stripped:
        return []
    value = json.loads(stripped)
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _discover_cst_processes() -> list[dict[str, Any]]:
    names = ",".join(json.dumps(name) for name in CST_FORCE_KILL_PROCESS_ALLOWLIST)
    command = f"""
$allow = @({names})
$items = @()
foreach ($name in $allow) {{
  $items += Get-Process -Name $name -ErrorAction SilentlyContinue |
    ForEach-Object {{
      [pscustomobject]@{{
        pid = $_.Id
        name = $_.ProcessName
        main_window_title = $_.MainWindowTitle
      }}
    }}
}}
$items | Sort-Object pid -Unique | ConvertTo-Json -Depth 4
"""
    result = _run_powershell(command)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Get-Process failed")
    return _loads_json_array(result.stdout)


def stop_process(pid: int, name: str) -> dict[str, Any]:
    command = f"""
try {{
  Stop-Process -Id {int(pid)} -Force -ErrorAction Stop
  [pscustomobject]@{{ status = "killed"; pid = {int(pid)}; name = {json.dumps(name)} }} | ConvertTo-Json -Depth 4
}} catch {{
  [pscustomobject]@{{
    status = "failed"
    pid = {int(pid)}
    name = {json.dumps(name)}
    error = $_.Exception.Message
  }} | ConvertTo-Json -Depth 4
}}
"""
    result = _run_powershell(command)
    if result.returncode != 0:
        return {
            "status": "failed",
            "pid": pid,
            "name": name,
            "error": result.stderr.strip() or result.stdout.strip() or "Stop-Process failed",
        }
    payload = json.loads(result.stdout.strip())
    if isinstance(payload, dict):
        return payload
    return {"status": "failed", "pid": pid, "name": name, "error": "unexpected Stop-Process output"}


def _is_access_denied(message: str) -> bool:
    lowered = message.lower()
    return "access is denied" in lowered or "拒绝访问" in lowered or "存取被拒" in lowered


def _classify_process(proc: dict[str, Any]) -> str:
    """按进程名分类；只做只读名称匹配，不查询路径、父进程或安装目录。"""
    name = str(proc.get("name") or "").casefold()
    if name == "cstd":
        return "license_service"
    if "design environment" in name:
        return "design_environment"
    if "dcmaincontroller" in name:
        return "dc_controller"
    if "dcsolverserver" in name:
        return "dc_solver_server"
    return "configured_process"


def _pid_of(mapping: Any) -> int | None:
    if not isinstance(mapping, dict):
        return None
    raw = mapping.get("pid")
    if raw is None:
        raw = mapping.get("design_environment_pid")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _lock_file_payload(paths: list[Path]) -> list[str]:
    return [path.as_posix() for path in paths]


def _runtime_session_lease(project_path: str) -> dict[str, Any]:
    """只读查询本 Runtime 对目标工程的会话租约；任何异常都不外抛。"""
    unknown = {"known": False, "design_environment_pid": None, "ownership": "none"}
    if not project_path:
        return dict(unknown)
    try:
        from . import session as session_core

        leases = getattr(session_core, "_OPENED_DESIGN_ENVIRONMENTS", None)
        if not isinstance(leases, dict) or not leases:
            return dict(unknown)
        try:
            normalized = abs_project_path(project_path)
        except Exception:
            normalized = str(project_path)
        lease = leases.get(normalized)
        if lease is None:
            normalized_key = os.path.normcase(str(normalized))
            for key, candidate in leases.items():
                if os.path.normcase(str(key)) == normalized_key:
                    lease = candidate
                    break
        if lease is None:
            return dict(unknown)
        if isinstance(lease, dict):
            raw_pid = lease.get("design_environment_pid")
            runtime_owned = bool(lease.get("runtime_owned", False))
        else:
            raw_pid = getattr(lease, "design_environment_pid", None)
            runtime_owned = bool(getattr(lease, "runtime_owned", False))
        try:
            pid = int(raw_pid) if raw_pid is not None else None
        except (TypeError, ValueError):
            pid = None
        return {
            "known": True,
            "design_environment_pid": pid,
            "ownership": "runtime_owned" if runtime_owned else "user_confirmed",
        }
    except Exception:
        return dict(unknown)


def _target_abs_path(project_path: str) -> str:
    if not project_path:
        return ""
    try:
        return abs_project_path(project_path)
    except Exception:
        try:
            return os.path.abspath(os.path.expanduser(str(project_path)))
        except Exception:
            return str(project_path)


def _normalized_path_variants(project_path: str) -> set[str]:
    """目标路径的规范化集合；容忍路径缺少 .cst 后缀但只做精确比较。"""
    variants: set[str] = set()
    if not project_path:
        return variants
    raw = str(project_path)
    candidates = [raw]
    try:
        suffix = Path(raw).suffix.lower()
    except Exception:
        suffix = ""
    try:
        if suffix == ".cst":
            candidates.append(str(Path(raw).with_suffix("")))
        else:
            candidates.append(raw + ".cst")
    except Exception:
        pass
    for candidate in candidates:
        try:
            variants.add(project_identity.normalize_project_path(candidate))
        except Exception:
            continue
    return variants


def _matches_target_project(candidate_path: str, target_norms: set[str]) -> bool:
    if not candidate_path or not target_norms:
        return False
    try:
        return project_identity.normalize_project_path(str(candidate_path)) in target_norms
    except Exception:
        return False


def _match_target_open_projects(
    open_projects: Any,
    project_path: str,
) -> tuple[list[dict[str, Any]], set[int]]:
    matches: list[dict[str, Any]] = []
    pids: set[int] = set()
    if not project_path or not isinstance(open_projects, dict):
        return matches, pids
    if open_projects.get("status") != "success":
        return matches, pids
    target_norms = _normalized_path_variants(project_path)
    for entry in open_projects.get("open_projects") or []:
        if not isinstance(entry, dict):
            continue
        if not _matches_target_project(str(entry.get("project_path") or ""), target_norms):
            continue
        matches.append(entry)
        pid = _pid_of({"pid": entry.get("design_environment_pid")})
        if pid is not None:
            pids.add(pid)
    return matches, pids


def _annotate_process(
    proc: dict[str, Any],
    *,
    target_pids: set[int],
    open_list_ok: bool,
) -> dict[str, Any]:
    classification = _classify_process(proc)
    is_background = classification != "design_environment"
    pid = _pid_of(proc)
    if is_background:
        relation = "shared_service"
    elif pid is not None and pid in target_pids:
        relation = "target_project_session"
    elif open_list_ok:
        relation = "other_session"
    else:
        relation = "unknown"
    return {
        **proc,
        "classification": classification,
        "is_background_service": is_background,
        "target_relation": relation,
        "may_terminate_by_default": False,
    }


def _process_reference(proc: dict[str, Any], classification: str) -> dict[str, Any]:
    return {
        "pid": _pid_of(proc),
        "name": str(proc.get("name") or ""),
        "classification": classification,
    }


def _target_pid_ownership(pid: int, lease: dict[str, Any]) -> str:
    """单个目标 PID 的会话归属；只有租约明确覆盖该 PID 才算 Runtime 所有。"""
    if not lease or not lease.get("known"):
        return "external_unknown"
    lease_pid = lease.get("design_environment_pid")
    if lease_pid is None:
        return "external_unknown"
    try:
        if int(lease_pid) != int(pid):
            return "external_unknown"
    except (TypeError, ValueError):
        return "external_unknown"
    return str(lease.get("ownership") or "external_unknown")


def _authorization_for_ownership(ownership: str) -> str:
    if ownership == "runtime_owned":
        return "runtime_owned"
    if ownership == "user_confirmed":
        return "user_confirmed"
    return "requires_user_authorization"


def _inspect_cleanup_candidate(proc: dict[str, Any], lease: dict[str, Any]) -> dict[str, Any] | None:
    pid = _pid_of(proc)
    if pid is None:
        return None
    ownership = _target_pid_ownership(pid, lease)
    return {
        "pid": pid,
        "name": str(proc.get("name") or ""),
        "classification": "design_environment",
        "target_relation": "target_project_session",
        "ownership": ownership,
        "authorization": _authorization_for_ownership(ownership),
        "may_terminate": ownership == "runtime_owned",
    }


def _cleanup_candidate(
    pid: int,
    name: str,
    target_relation: str,
    ownership: str,
    *,
    authorization: str | None = None,
    may_terminate: bool | None = None,
) -> dict[str, Any]:
    return {
        "pid": int(pid),
        "name": str(name or ""),
        "classification": "design_environment",
        "target_relation": target_relation,
        "ownership": ownership,
        "authorization": authorization or _authorization_for_ownership(ownership),
        "may_terminate": (ownership == "runtime_owned") if may_terminate is None else bool(may_terminate),
    }


def _safe_list_open_projects() -> dict[str, Any]:
    try:
        result = project_identity.list_open_projects()
    except Exception as exc:
        return error_response(
            "list_open_projects_failed",
            f"list_open_projects failed: {exc}",
            open_projects=[],
            runtime_module="cst_runtime.core.identity",
        )
    if isinstance(result, dict):
        return result
    return error_response(
        "list_open_projects_failed",
        "list_open_projects returned an unexpected payload",
        open_projects=[],
        runtime_module="cst_runtime.core.identity",
    )


def _safe_verify_project_identity(project_path: str) -> dict[str, Any]:
    try:
        result = project_identity.verify_project_identity(project_path)
    except Exception as exc:
        return error_response(
            "list_open_projects_failed",
            f"verify_project_identity failed: {exc}",
            project_path=str(project_path),
            runtime_module="cst_runtime.core.identity",
        )
    if isinstance(result, dict):
        return result
    return error_response(
        "list_open_projects_failed",
        "verify_project_identity returned an unexpected payload",
        project_path=str(project_path),
        runtime_module="cst_runtime.core.identity",
    )


def _status_message(status: Any) -> str:
    if isinstance(status, dict):
        return str(status.get("message") or "")
    return ""


def _open_project_paths(status: Any) -> list[str]:
    if not isinstance(status, dict):
        return []
    return [str(item) for item in (status.get("open_projects") or []) if item is not None]


def _conflict(
    kind: str,
    observed: Any,
    blocks_operations: Any,
    message: str,
    resolution: str,
    missing_information: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "target_related": True,
        "observed": observed,
        "blocks_operations": list(blocks_operations),
        "message": message,
        "resolution": resolution,
        "missing_information": missing_information,
    }


def _solver_summary(probe: Any, fallback_pid: int | None) -> dict[str, Any]:
    if not isinstance(probe, dict):
        return {
            "status": "error",
            "running": None,
            "checked": True,
            "design_environment_pid": fallback_pid,
        }
    status = str(probe.get("status") or "error")
    if status not in {"success", "not_open", "error"}:
        status = "error"
    running = probe.get("running") if status in {"success", "not_open"} else None
    raw_pid = probe.get("design_environment_pid")
    try:
        pid = int(raw_pid) if raw_pid is not None else fallback_pid
    except (TypeError, ValueError):
        pid = fallback_pid
    return {
        "status": status,
        "running": running,
        "checked": True,
        "design_environment_pid": pid,
    }


def _background_notes(service_count: int, unrelated_count: int) -> list[str]:
    notes: list[str] = []
    if service_count:
        if service_count == 1:
            notes.append(
                "1 shared CST service is running (license/DC); it is expected and is not a termination candidate."
            )
        else:
            notes.append(
                f"{service_count} shared CST services are running (license/DC); "
                "they are expected and are not termination candidates."
            )
    if unrelated_count:
        if unrelated_count == 1:
            notes.append("1 unrelated Design Environment is open and is left untouched.")
        else:
            notes.append(
                f"{unrelated_count} unrelated Design Environments are open and are left untouched."
            )
    return notes


def _inspect_next_steps(
    *,
    intent: str,
    conflicts: list[dict[str, Any]],
    target: dict[str, Any],
    background_notes: list[str],
    project_path: str,
    lock_files: list[Path],
    safe_to_copy_or_reopen: bool,
) -> list[str]:
    steps: list[str] = []
    kinds = [conflict["kind"] for conflict in conflicts]

    if not project_path:
        steps.append(
            "Pass project_path (and the planned operation) to scope this check to the target "
            "CST project; background services and other sessions are never terminated by this check."
        )
        steps.extend(background_notes)
        if not background_notes:
            steps.append(
                "No target project is scoped yet; no action is required for allowlisted background processes."
            )
        return _dedupe(steps)

    if "target_identity_ambiguous" in kinds:
        steps.append(
            "The target project cannot be mapped to one CST session; ask the user which target "
            "Design Environment owns it before any operation."
        )
    if "target_session_ambiguous" in kinds:
        pids = target.get("design_environment_pids") or []
        steps.append(
            f"Design Environment PIDs {pids} all appear to host the target project; confirm the "
            "single target session with the user before writing or solving."
        )
    if "target_occupancy_unconfirmed" in kinds:
        steps.append(
            "Target project occupancy could not be confirmed from CST; resolve that target-scoped "
            "session/identity error before write/solve instead of terminating processes to guess."
        )
    if "target_lock_without_visible_session" in kinds:
        steps.append(
            f"A lock file exists for the target project ({len(lock_files)} file(s)) but no visible "
            "session owns it; identify the owning session or wait for the lock to be released "
            "(wait-project-unlocked) before copying or reopening. Never kill processes by default."
        )
    if "target_project_open" in kinds:
        steps.append(
            "The target project is open; close that TARGET session normally with cst-session-close "
            "using the required save policy, then wait-project-unlocked before copying or reopening."
        )
    if "target_session_confirmation_required" in kinds:
        pids = target.get("design_environment_pids") or []
        steps.append(
            f"The target project is open in an external Design Environment (PID(s) {pids}); ask the "
            "user to confirm that PID before attaching, and never terminate it without explicit authorization."
        )
    if "target_solver_running" in kinds:
        steps.append(
            "The target solver is running; wait for it to finish (wait-simulation) before writing or solving."
        )
    if "target_solver_state_unknown" in kinds:
        steps.append(
            "The solver state of the target project could not be read; check is-simulation-running or "
            "the target session before writing or solving."
        )

    if not conflicts:
        if intent in _COPY_REOPEN_OPERATIONS and safe_to_copy_or_reopen:
            steps.append("Target project is closed and unlocked; safe to copy or reopen it.")
        elif intent in _WRITE_SOLVE_OPERATIONS:
            steps.append(
                f"No target-scoped conflict for {intent}; background services and unrelated sessions are not blockers."
            )
        else:
            steps.append(
                "No target-scoped conflict; background services and unrelated sessions require no action."
            )
    steps.extend(background_notes)
    return _dedupe(steps)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def inspect_cst_environment(project_path: str = "", operation: str = "") -> dict[str, Any]:
    try:
        raw_operation = operation if isinstance(operation, str) else str(operation or "")
        normalized_operation = raw_operation.strip().lower()
        intent = _DEFAULT_OPERATION if not normalized_operation else normalized_operation
        if intent not in _ALLOWED_OPERATION_SET:
            return error_response(
                "invalid_operation",
                f"Unsupported operation {raw_operation!r}; expected one of "
                f"{', '.join(_ALLOWED_OPERATIONS)}.",
                operation=raw_operation,
                allowed_operations=list(_ALLOWED_OPERATIONS),
                project_path=str(project_path or ""),
                runtime_module=_RUNTIME_MODULE,
            )

        processes = _discover_cst_processes()
        lock_files: list[Path] = find_lock_files(project_path) if project_path else []
        open_projects = _safe_list_open_projects()
        identity_status: dict[str, Any] | None = None
        if project_path:
            identity_status = _safe_verify_project_identity(project_path)

        open_list_ok = isinstance(open_projects, dict) and open_projects.get("status") == "success"
        matching_open_projects, target_pid_set = _match_target_open_projects(open_projects, project_path)
        target_pids = sorted(target_pid_set)
        target_open = bool(target_pids)

        annotated = [
            _annotate_process(proc, target_pids=target_pid_set, open_list_ok=open_list_ok)
            for proc in processes
        ]
        background_processes = [proc for proc in annotated if proc["is_background_service"]]
        target_processes = [
            proc for proc in annotated if proc["target_relation"] == "target_project_session"
        ]
        unrelated_processes = [
            proc for proc in annotated if proc["target_relation"] == "other_session"
        ]

        lease = _runtime_session_lease(project_path) if project_path else {
            "known": False,
            "design_environment_pid": None,
            "ownership": "none",
        }
        if target_open:
            session_ownership = lease["ownership"] if lease.get("known") else "external_unknown"
        else:
            session_ownership = "none"
        identity_confirmed = (
            isinstance(identity_status, dict) and identity_status.get("status") == "success"
        )

        solver: dict[str, Any] = {
            "status": "not_checked",
            "running": None,
            "checked": False,
            "design_environment_pid": target_pids[0] if len(target_pids) == 1 else None,
        }
        probe_message = ""
        if target_open and intent in _WRITE_SOLVE_OPERATIONS:
            probe_pid = target_pids[0]
            try:
                probe = project_identity.probe_target_solver_state(project_path, probe_pid)
            except Exception as exc:
                probe = error_response(
                    "solver_state_unreadable",
                    f"probe_target_solver_state failed: {exc}",
                    project_path=str(project_path),
                    design_environment_pid=probe_pid,
                    running=None,
                    runtime_module="cst_runtime.core.identity",
                )
            solver = _solver_summary(probe, probe_pid)
            if isinstance(probe, dict):
                probe_message = _status_message(probe)

        target = {
            "project_path": _target_abs_path(project_path) if project_path else "",
            "open": target_open,
            "open_projects": matching_open_projects,
            "design_environment_pids": target_pids,
            "locked": bool(lock_files),
            "session_ownership": session_ownership,
            "identity_confirmed": identity_confirmed,
            "solver": solver,
        }

        identity_error_type = None
        if isinstance(identity_status, dict):
            identity_error_type = identity_status.get("error_type")
        open_error_type = open_projects.get("error_type") if isinstance(open_projects, dict) else None
        if identity_error_type == _IDENTITY_AMBIGUITY_ERROR:
            occupancy_error_type = None
        elif (
            project_path
            and identity_error_type not in _OCCUPANCY_ERROR_TYPES
            and open_error_type in _OCCUPANCY_ERROR_TYPES
        ):
            occupancy_error_type = open_error_type
        elif identity_error_type in _OCCUPANCY_ERROR_TYPES:
            occupancy_error_type = identity_error_type
        else:
            occupancy_error_type = None

        conflicts: list[dict[str, Any]] = []
        if identity_error_type == _IDENTITY_AMBIGUITY_ERROR:
            conflicts.append(
                _conflict(
                    "target_identity_ambiguous",
                    {
                        "error_type": identity_error_type,
                        "open_projects": _open_project_paths(identity_status),
                    },
                    _ALLOWED_OPERATIONS,
                    "The target project cannot be uniquely identified across the visible CST sessions.",
                    "Ask the user to identify the intended target Design Environment/session; do not close "
                    "or terminate unrelated sessions by default.",
                    "The mapping from the target project path to one Design Environment is ambiguous.",
                )
            )
        if len(target_pids) > 1:
            conflicts.append(
                _conflict(
                    "target_session_ambiguous",
                    {"design_environment_pids": target_pids},
                    _ALLOWED_OPERATIONS,
                    f"The target project appears to be open in {len(target_pids)} Design Environments.",
                    "Ask the user to confirm which single Design Environment owns the target project "
                    "before any operation.",
                    "A single owning Design Environment PID for the target project.",
                )
            )
        if project_path and occupancy_error_type:
            detail_source = identity_status if occupancy_error_type == identity_error_type else open_projects
            detail = _status_message(detail_source)
            conflicts.append(
                _conflict(
                    "target_occupancy_unconfirmed",
                    {"error_type": occupancy_error_type, "detail": detail},
                    ("write", "solve", "copy", "reopen"),
                    "The target project occupancy could not be confirmed from CST.",
                    "Resolve the target-scoped session/identity error; never terminate processes to guess "
                    "which session owns the target project.",
                    f"Could not confirm target project occupancy ({occupancy_error_type}): "
                    f"{detail or 'no detail available'}",
                )
            )
        if lock_files and not target_open:
            conflicts.append(
                _conflict(
                    "target_lock_without_visible_session",
                    {
                        "lock_files": _lock_file_payload(lock_files),
                        "lock_count": len(lock_files),
                        "visible_target_session": False,
                    },
                    ("write", "solve", "copy", "reopen"),
                    "A target project lock file exists but no visible CST session owns the target project.",
                    "Identify the owning session or wait for the lock to be released (wait-project-unlocked); "
                    "never kill processes by default.",
                    "The PID/session that currently holds the target project lock.",
                )
            )
        if target_open and intent in _COPY_REOPEN_OPERATIONS:
            conflicts.append(
                _conflict(
                    "target_project_open",
                    {"design_environment_pids": target_pids, "operation": intent},
                    ("copy", "reopen"),
                    "The target project is currently open.",
                    "Close the TARGET session normally with cst-session-close using the required save "
                    "policy, then wait-project-unlocked before copying or reopening.",
                    None,
                )
            )
        if target_open and session_ownership == "external_unknown":
            conflicts.append(
                _conflict(
                    "target_session_confirmation_required",
                    {"design_environment_pids": target_pids},
                    ("write", "solve"),
                    "The target project is open in a Design Environment whose ownership is not confirmed "
                    "by this Runtime.",
                    "Ask the user to confirm the target PID before attaching; never terminate an external "
                    "session without explicit user authorization.",
                    "User confirmation of the target Design Environment PID and its ownership.",
                )
            )
        if solver.get("running") is True and intent in _WRITE_SOLVE_OPERATIONS:
            conflicts.append(
                _conflict(
                    "target_solver_running",
                    {"design_environment_pid": solver.get("design_environment_pid")},
                    ("write", "solve"),
                    "The target project solver is running.",
                    "Wait for the target solver to finish (wait-simulation) before writing or solving.",
                    None,
                )
            )
        if solver.get("status") == "error" and intent in _WRITE_SOLVE_OPERATIONS:
            conflicts.append(
                _conflict(
                    "target_solver_state_unknown",
                    {
                        "design_environment_pid": solver.get("design_environment_pid"),
                        "detail": probe_message,
                    },
                    ("write", "solve"),
                    "The solver state of the target project could not be read.",
                    "Retry the solver-state check (is-simulation-running) or inspect the target session "
                    "before writing or solving.",
                    f"Solver running state for the target project: "
                    f"{probe_message or 'unreadable'}",
                )
            )

        blocking_conflicts = [
            conflict
            for conflict in conflicts
            if intent in conflict["blocks_operations"]
        ]
        if blocking_conflicts:
            readiness = "blocked"
        elif conflicts:
            readiness = "attention_required"
        else:
            readiness = "clear"

        identity_blocked = identity_error_type in {
            "ambiguous_open_projects",
            "no_active_project",
            "attach_active_project_failed",
            "list_open_projects_failed",
        }
        wrong_project_open = identity_error_type == "project_not_open" and bool(
            (identity_status or {}).get("open_projects")
        )
        lock_count = len(lock_files)
        safe_to_copy_or_reopen = (
            bool(project_path)
            and not target_open
            and lock_count == 0
            and not identity_blocked
            and not wrong_project_open
        )

        cleanup_candidates: list[dict[str, Any]] = []
        for proc in target_processes:
            candidate = _inspect_cleanup_candidate(proc, lease)
            if candidate is not None:
                cleanup_candidates.append(candidate)

        background_service_count = len(background_processes)
        unrelated_count = len(unrelated_processes)
        background_notes = _background_notes(background_service_count, unrelated_count)
        target_release_required = any(
            conflict["kind"] in _TARGET_RELEASE_CONFLICT_KINDS for conflict in conflicts
        )
        cleanup_required = bool(project_path) and any(
            conflict["kind"] in _CLEANUP_REQUIRED_CONFLICT_KINDS for conflict in conflicts
        )

        return {
            "status": "success",
            "operation": intent,
            "readiness": readiness,
            "project_path": str(project_path or ""),
            "force_kill_allowlist": CST_FORCE_KILL_PROCESS_ALLOWLIST,
            "processes": annotated,
            "process_count": len(annotated),
            "background_processes": background_processes,
            "background_service_count": background_service_count,
            "target_processes": target_processes,
            "target_process_count": len(target_processes),
            "unrelated_processes": unrelated_processes,
            "lock_files": _lock_file_payload(lock_files),
            "lock_count": lock_count,
            "open_projects_status": open_projects,
            "project_identity_status": identity_status,
            "target": target,
            "conflicts": conflicts,
            "blocking_conflicts": blocking_conflicts,
            "target_release_required": target_release_required,
            "cleanup_required": cleanup_required,
            "cleanup_candidates": cleanup_candidates,
            "safe_to_copy_or_reopen": safe_to_copy_or_reopen,
            "background_notes": background_notes,
            "next_steps": _inspect_next_steps(
                intent=intent,
                conflicts=conflicts,
                target=target,
                background_notes=background_notes,
                project_path=project_path,
                lock_files=lock_files,
                safe_to_copy_or_reopen=safe_to_copy_or_reopen,
            ),
            "runtime_module": _RUNTIME_MODULE,
        }
    except Exception as exc:
        return error_response(
            "inspect_cst_environment_failed",
            f"inspect_cst_environment failed: {str(exc)}",
            force_kill_allowlist=CST_FORCE_KILL_PROCESS_ALLOWLIST,
            project_path=str(project_path or ""),
            runtime_module=_RUNTIME_MODULE,
        )


def _cleanup_incomplete_message(
    *,
    scope: str,
    unhandled: list[dict[str, Any]],
    access_denied: list[dict[str, Any]],
    other_failures: list[dict[str, Any]],
    lock_residual: bool,
    lock_files_after: list[Path],
) -> str:
    reasons: list[str] = []
    if unhandled:
        reasons.append(f"{len(unhandled)} candidate process(es) still present after cleanup")
    if other_failures:
        reasons.append(f"{len(other_failures)} termination attempt(s) failed")
    if access_denied:
        reasons.append(f"{len(access_denied)} termination attempt(s) were access-denied and remain unhandled")
    if lock_residual:
        reasons.append(f"target project still has {len(lock_files_after)} lock file(s)")
    detail = "; ".join(reasons) if reasons else "cleanup did not finish cleanly"
    return f"{scope}-scoped CST process cleanup incomplete: {detail}."


def cleanup_cst_processes(
    project_path: str = "",
    dry_run: bool = False,
    settle_seconds: float = 0.5,
    *,
    scope: str = "target",
    confirm_global_cleanup: bool = False,
) -> dict[str, Any]:
    try:
        requested_scope = str(scope or "target").strip().lower()
        if requested_scope not in {"target", "global"}:
            return error_response(
                "invalid_scope",
                f"Unsupported cleanup scope {scope!r}; expected 'target' or 'global'.",
                scope=scope,
                allowed_scopes=["target", "global"],
                project_path=str(project_path or ""),
                force_kill_allowlist=CST_FORCE_KILL_PROCESS_ALLOWLIST,
                runtime_module=_RUNTIME_MODULE,
            )
        is_dry_run = bool(dry_run)
        process_project_path = str(project_path or "")

        observations = _discover_cst_processes()
        classified = [(proc, _classify_process(proc)) for proc in observations]
        services_retained = [
            _process_reference(proc, classification)
            for proc, classification in classified
            if classification != "design_environment"
        ]
        de_entries = [
            (proc, classification)
            for proc, classification in classified
            if classification == "design_environment"
        ]
        lock_files_before = find_lock_files(process_project_path) if process_project_path else []

        if requested_scope == "global" and not bool(confirm_global_cleanup):
            return error_response(
                "cleanup_authorization_required",
                "Global CST Design Environment cleanup requires confirm_global_cleanup=True; shared "
                "license/DC services are still never terminated.",
                cleanup_status="authorization_required",
                completed=False,
                scope="global",
                dry_run=is_dry_run,
                project_path=process_project_path,
                force_kill_allowlist=CST_FORCE_KILL_PROCESS_ALLOWLIST,
                candidates=[],
                authorization_required="explicit_confirmation_of_global_cleanup",
                services_retained=services_retained,
                unrelated_processes_retained=[],
                processes_before=observations,
                attempts=[],
                access_denied=[],
                unhandled_processes=[],
                lock_files_before=_lock_file_payload(lock_files_before),
                lock_files_after=_lock_file_payload(lock_files_before),
                next_steps=[
                    "Global cleanup was not authorized; re-run only after the user explicitly confirms "
                    "global Design Environment cleanup. Shared license/DC services are still retained."
                ],
                runtime_module=_RUNTIME_MODULE,
            )

        open_projects_status: dict[str, Any] | None = None
        if requested_scope == "target":
            if not process_project_path:
                de_references = [
                    _process_reference(proc, classification) for proc, classification in de_entries
                ]
                return {
                    "status": "success",
                    "cleanup_status": "dry_run" if is_dry_run else "no_candidates",
                    "completed": not is_dry_run,
                    "scope": "target",
                    "dry_run": is_dry_run,
                    "project_path": "",
                    "message": (
                        "No project_path was provided; target-scoped cleanup dry run found no candidates "
                        "and no CST process was terminated."
                        if is_dry_run
                        else "No project_path was provided; target-scoped cleanup has no candidates and no "
                        "CST process was terminated."
                    ),
                    "force_kill_allowlist": CST_FORCE_KILL_PROCESS_ALLOWLIST,
                    "candidates": [],
                    "services_retained": services_retained,
                    "unrelated_processes_retained": de_references,
                    "processes_before": observations,
                    "processes_after": observations,
                    "attempts": [],
                    "access_denied": [],
                    "unhandled_processes": [],
                    "other_failures": [],
                    "lock_files_before": [],
                    "lock_files_after": [],
                    "would_require_authorization": False,
                    "next_steps": [
                        "Pass project_path to scope process cleanup to the target CST project; shared "
                        "services and unrelated Design Environments are never clean-up candidates."
                    ],
                    "runtime_module": _RUNTIME_MODULE,
                }
            open_projects_status = _safe_list_open_projects()
            _matching_projects, target_pid_set = _match_target_open_projects(
                open_projects_status,
                process_project_path,
            )
            target_pids = sorted(target_pid_set)
            lease = _runtime_session_lease(process_project_path)
            de_by_pid: dict[int, dict[str, Any]] = {}
            for proc, _classification in de_entries:
                pid = _pid_of(proc)
                if pid is not None:
                    de_by_pid[pid] = proc
            candidates: list[dict[str, Any]] = []
            for pid in target_pids:
                proc = de_by_pid.get(pid)
                name = str((proc or {}).get("name") or "") or "CST DESIGN ENVIRONMENT_AMD64"
                ownership = _target_pid_ownership(pid, lease)
                candidates.append(
                    _cleanup_candidate(pid, name, "target_project_session", ownership)
                )
            unrelated_retained = [
                _process_reference(proc, classification)
                for proc, classification in de_entries
                if _pid_of(proc) not in target_pid_set
            ]
        else:
            lease = None
            candidates = []
            for proc, _classification in de_entries:
                pid = _pid_of(proc)
                if pid is None:
                    continue
                candidates.append(
                    _cleanup_candidate(
                        pid,
                        str(proc.get("name") or ""),
                        "other_session",
                        "external_unknown",
                        authorization="global_cleanup_authorized",
                        may_terminate=True,
                    )
                )
            unrelated_retained = []

        blocked_candidates = [
            candidate for candidate in candidates if not candidate["may_terminate"]
        ]
        if blocked_candidates and not is_dry_run:
            return error_response(
                "cleanup_authorization_required",
                "The target project is hosted by a Design Environment that this Runtime does not own; "
                "explicit user authorization is required before terminating it.",
                cleanup_status="authorization_required",
                completed=False,
                scope=requested_scope,
                dry_run=False,
                project_path=process_project_path,
                force_kill_allowlist=CST_FORCE_KILL_PROCESS_ALLOWLIST,
                candidates=candidates,
                authorization_required="explicit_user_authorization_for_existing_session",
                services_retained=services_retained,
                unrelated_processes_retained=unrelated_retained,
                processes_before=observations,
                attempts=[],
                access_denied=[],
                unhandled_processes=[],
                other_failures=[],
                lock_files_before=_lock_file_payload(lock_files_before),
                lock_files_after=_lock_file_payload(lock_files_before),
                open_projects_status=open_projects_status,
                next_steps=[
                    "Ask the user to confirm the target Design Environment PID/ownership; no process "
                    "was terminated. Keep shared services and unrelated sessions running."
                ],
                runtime_module=_RUNTIME_MODULE,
            )

        attempts: list[dict[str, Any]] = []
        if is_dry_run:
            after_observations = observations
            lock_files_after = lock_files_before
        else:
            for candidate in candidates:
                if not candidate["may_terminate"]:
                    continue
                attempts.append(
                    stop_process(int(candidate["pid"]), str(candidate["name"]))
                )
            if candidates and float(settle_seconds) > 0:
                time.sleep(max(0.0, float(settle_seconds)))
            after_observations = _discover_cst_processes()
            lock_files_after = (
                find_lock_files(process_project_path) if process_project_path else []
            )

        # Access is denied 的进程绝不从审计中过滤：它们保持未处理状态。
        access_denied = [
            item
            for item in attempts
            if item.get("status") == "failed" and _is_access_denied(str(item.get("error", "")))
        ]
        other_failures = [
            item
            for item in attempts
            if item.get("status") == "failed" and item not in access_denied
        ]
        after_pids = {
            pid for pid in (_pid_of(proc) for proc in after_observations) if pid is not None
        }
        # dry run 不执行终止，因此绝不能把 before 快照当作残留计算。
        unhandled_processes = (
            []
            if is_dry_run
            else [
                candidate for candidate in candidates if candidate["pid"] in after_pids
            ]
        )
        lock_residual = (
            requested_scope == "target" and not is_dry_run and bool(lock_files_after)
        )
        incomplete = bool(unhandled_processes) or bool(other_failures) or lock_residual

        lock_before_payload = _lock_file_payload(lock_files_before)
        lock_after_payload = _lock_file_payload(lock_files_after)
        if incomplete:
            return error_response(
                "cleanup_cst_processes_incomplete",
                _cleanup_incomplete_message(
                    scope=requested_scope,
                    unhandled=unhandled_processes,
                    access_denied=access_denied,
                    other_failures=other_failures,
                    lock_residual=lock_residual,
                    lock_files_after=lock_files_after,
                ),
                cleanup_status="incomplete",
                completed=False,
                note=(
                    "Access is denied is unhandled, not proof that the target project is in conflict."
                ),
                scope=requested_scope,
                dry_run=is_dry_run,
                project_path=process_project_path,
                force_kill_allowlist=CST_FORCE_KILL_PROCESS_ALLOWLIST,
                candidates=candidates,
                services_retained=services_retained,
                unrelated_processes_retained=unrelated_retained,
                processes_before=observations,
                processes_after=after_observations,
                attempts=attempts,
                access_denied=access_denied,
                unhandled_processes=unhandled_processes,
                other_failures=other_failures,
                lock_files_before=lock_before_payload,
                lock_files_after=lock_after_payload,
                open_projects_status=open_projects_status,
                next_steps=[
                    "Review the unhandled/access_denied PIDs and any residual target lock; identify the "
                    "owning session or wait for lock release. Access is denied is an audit item, not a "
                    "reason to widen the termination scope."
                ],
                runtime_module=_RUNTIME_MODULE,
            )

        cleanup_status = "dry_run" if is_dry_run else "completed"
        completed = not is_dry_run
        if is_dry_run:
            message = (
                "CST process cleanup dry run completed; no process was terminated."
                if candidates
                else "CST process cleanup dry run completed; no target-scoped candidate exists."
            )
        elif candidates:
            message = "CST process cleanup completed for the target-scoped candidates."
        else:
            message = "CST process cleanup completed; no target-scoped candidate required termination."
        if requested_scope == "global":
            message = (
                "Global CST process cleanup completed; shared license/DC services were retained."
                if not is_dry_run
                else "Global CST process cleanup dry run completed; shared license/DC services are retained."
            )

        return {
            "status": "success",
            "cleanup_status": cleanup_status,
            "completed": completed,
            "message": message,
            "scope": requested_scope,
            "dry_run": is_dry_run,
            "project_path": process_project_path,
            "force_kill_allowlist": CST_FORCE_KILL_PROCESS_ALLOWLIST,
            "candidates": candidates,
            "services_retained": services_retained,
            "unrelated_processes_retained": unrelated_retained,
            "processes_before": observations,
            "processes_after": after_observations,
            "attempts": attempts,
            "access_denied": access_denied,
            "unhandled_processes": [],
            "other_failures": [],
            "lock_files_before": lock_before_payload,
            "lock_files_after": lock_after_payload,
            "would_require_authorization": bool(blocked_candidates),
            "open_projects_status": open_projects_status,
            "next_steps": [
                "Review the target-scoped candidates. Real termination still requires Runtime-owned "
                "session evidence or explicit user authorization; shared services and unrelated "
                "sessions are retained."
                if is_dry_run
                else "No further target-scoped process action is required; shared services and "
                "unrelated Design Environments were retained."
            ],
            "runtime_module": _RUNTIME_MODULE,
        }
    except Exception as exc:
        return error_response(
            "cleanup_cst_processes_failed",
            f"cleanup_cst_processes failed: {str(exc)}",
            force_kill_allowlist=CST_FORCE_KILL_PROCESS_ALLOWLIST,
            project_path=str(project_path or ""),
            runtime_module=_RUNTIME_MODULE,
        )


def cleanup_orphan_processes(
    settle_seconds: float = 0.5,
    *,
    confirm_terminate: bool = False,
) -> dict[str, Any]:
    try:
        all_procs = _discover_cst_processes()
        classified = [(proc, _classify_process(proc)) for proc in all_procs]
        services_retained = [
            _process_reference(proc, classification)
            for proc, classification in classified
            if classification != "design_environment"
        ]
        de_entries = [
            (proc, classification)
            for proc, classification in classified
            if classification == "design_environment"
        ]
        open_result = _safe_list_open_projects()
        if not isinstance(open_result, dict) or open_result.get("status") != "success":
            return error_response(
                "cleanup_orphan_unconfirmed",
                "Cannot confirm which Design Environment PIDs are orphans because the open-project "
                "list could not be read; no process was terminated.",
                cleanup_status="unconfirmed",
                completed=False,
                candidates=[],
                services_retained=services_retained,
                open_projects_status=open_result,
                force_kill_allowlist=CST_FORCE_KILL_PROCESS_ALLOWLIST,
                runtime_module=_RUNTIME_MODULE,
            )
        active_pids: set[int] = set()
        for project in open_result.get("open_projects") or []:
            if not isinstance(project, dict):
                continue
            pid = _pid_of({"pid": project.get("design_environment_pid")})
            if pid is not None:
                active_pids.add(pid)

        candidates: list[dict[str, Any]] = []
        for proc, _classification in de_entries:
            pid = _pid_of(proc)
            if pid is None or pid in active_pids:
                continue
            candidates.append(
                {"pid": pid, "name": str(proc.get("name") or ""), "classification": "design_environment"}
            )

        if not candidates:
            return {
                "status": "success",
                "cleanup_status": "completed" if confirm_terminate else "report_only",
                "completed": bool(confirm_terminate),
                "orphan_found": 0,
                "orphan_killed": 0,
                "killed": [],
                "candidates": [],
                "services_retained": services_retained,
                "open_projects_status": open_result,
                "message": "No orphan Design Environment process was found.",
                "next_steps": [
                    "No orphan Design Environment is present; shared services and unrelated sessions "
                    "require no action."
                ],
                "force_kill_allowlist": CST_FORCE_KILL_PROCESS_ALLOWLIST,
                "runtime_module": _RUNTIME_MODULE,
            }

        if not confirm_terminate:
            return {
                "status": "success",
                "cleanup_status": "report_only",
                "completed": False,
                "orphan_found": len(candidates),
                "orphan_killed": 0,
                "killed": [],
                "candidates": candidates,
                "services_retained": services_retained,
                "open_projects_status": open_result,
                "message": (
                    f"Report only: {len(candidates)} orphan Design Environment candidate(s) found and "
                    "left running."
                ),
                "next_steps": [
                    "Re-run with confirm_terminate=True only after the user explicitly approves "
                    "terminating these exact orphan Design Environment PIDs."
                ],
                "force_kill_allowlist": CST_FORCE_KILL_PROCESS_ALLOWLIST,
                "runtime_module": _RUNTIME_MODULE,
            }

        attempts: list[dict[str, Any]] = []
        for candidate in candidates:
            attempts.append(stop_process(int(candidate["pid"]), str(candidate["name"])))
        if settle_seconds > 0:
            time.sleep(max(0.0, float(settle_seconds)))
        after = _discover_cst_processes()
        after_pids = {pid for pid in (_pid_of(proc) for proc in after) if pid is not None}
        unhandled_processes = [
            candidate for candidate in candidates if candidate["pid"] in after_pids
        ]
        access_denied = [
            item
            for item in attempts
            if item.get("status") == "failed" and _is_access_denied(str(item.get("error", "")))
        ]
        other_failures = [
            item
            for item in attempts
            if item.get("status") == "failed" and item not in access_denied
        ]
        killed_payload = [
            {"pid": item.get("pid"), "status": item.get("status")} for item in attempts
        ]
        if unhandled_processes or other_failures:
            return error_response(
                "cleanup_orphan_processes_incomplete",
                "Orphan Design Environment cleanup did not finish cleanly.",
                cleanup_status="incomplete",
                completed=False,
                note=(
                    "Access is denied is unhandled, not proof that the orphan is gone."
                ),
                orphan_found=len(candidates),
                orphan_killed=len(attempts),
                killed=killed_payload,
                candidates=candidates,
                attempts=attempts,
                access_denied=access_denied,
                unhandled_processes=unhandled_processes,
                other_failures=other_failures,
                processes_after=after,
                services_retained=services_retained,
                open_projects_status=open_result,
                force_kill_allowlist=CST_FORCE_KILL_PROCESS_ALLOWLIST,
                next_steps=[
                    "Review the access_denied/unhandled orphan PIDs; do not assume they were terminated."
                ],
                runtime_module=_RUNTIME_MODULE,
            )
        return {
            "status": "success",
            "cleanup_status": "completed",
            "completed": True,
            "orphan_found": len(candidates),
            "orphan_killed": len(attempts),
            "killed": killed_payload,
            "candidates": candidates,
            "access_denied": access_denied,
            "unhandled_processes": [],
            "services_retained": services_retained,
            "open_projects_status": open_result,
            "message": "Orphan Design Environment cleanup completed for confirmed PIDs.",
            "next_steps": [
                "No further orphan cleanup is required; shared services and unrelated sessions are retained."
            ],
            "force_kill_allowlist": CST_FORCE_KILL_PROCESS_ALLOWLIST,
            "runtime_module": _RUNTIME_MODULE,
        }
    except Exception as exc:
        return error_response(
            "cleanup_orphan_failed",
            f"orphan process cleanup failed: {str(exc)}",
            runtime_module=_RUNTIME_MODULE,
        )
