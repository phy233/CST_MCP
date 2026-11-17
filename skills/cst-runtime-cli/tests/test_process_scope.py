"""Issue #1 离线回归测试：进程检查/清理必须按目标工程与操作意图收敛。

契约：进程检查/清理按目标工程与计划操作收敛（GitHub issue #1）。

本模块完全离线：进程发现、锁文件、进程终止、打开工程枚举、工程身份、
目标求解器探测与会话租约全部打桩；不连接 CST、不启动子进程、绝不终止
任何真实进程。
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPO_ROOT / "skills" / "cst-runtime-cli" / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from cst_runtime.core import process as process_core

DE_NAME = "CST DESIGN ENVIRONMENT_AMD64"
LICENSE_PID = 9001
DC_CONTROLLER_PID = 9002
DC_SOLVER_PID = 9003
TARGET_PID = 555
UNRELATED_PID = 777
ORPHAN_PID = 888

SERVICE_PIDS = (LICENSE_PID, DC_CONTROLLER_PID, DC_SOLVER_PID)


def _services() -> list[dict[str, Any]]:
    return [
        {"pid": LICENSE_PID, "name": "cstd"},
        {"pid": DC_CONTROLLER_PID, "name": "CSTDCMainController_AMD64"},
        {"pid": DC_SOLVER_PID, "name": "CSTDCSolverServer_AMD64"},
    ]


def _de(pid: int, *, name: str = DE_NAME, title: str = "") -> dict[str, Any]:
    return {"pid": pid, "name": name, "main_window_title": title}


def _open_project(path: str, pid: int) -> dict[str, Any]:
    return {
        "project_path": str(path),
        "project_name": Path(path).stem,
        "design_environment_pid": pid,
    }


def _pids(items: Any) -> list[int]:
    values: list[int] = []
    for item in items or []:
        pid = item.get("pid") if isinstance(item, dict) else item
        if pid is not None:
            values.append(int(pid))
    return values


def _conflicts(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in result.get("conflicts") or [] if isinstance(item, dict)]


def _conflict_kinds(result: dict[str, Any]) -> set[str]:
    return {str(item.get("kind")) for item in _conflicts(result)}


def _blocking_conflicts(result: dict[str, Any]) -> list[dict[str, Any]]:
    operation = result.get("operation")
    return [
        item
        for item in _conflicts(result)
        if operation in (item.get("blocks_operations") or [])
    ]


def _conflict(result: dict[str, Any], kind: str) -> dict[str, Any]:
    matches = [item for item in _conflicts(result) if item.get("kind") == kind]
    assert matches, f"missing {kind} conflict: {result}"
    return matches[0]


def _next_steps_text(result: dict[str, Any]) -> str:
    return "\n".join(str(step) for step in result.get("next_steps") or [])


def _notes_text(result: dict[str, Any]) -> str:
    return " ".join(str(note) for note in result.get("background_notes") or [])


class FakeEnvironment:
    """可编程的 CST/进程边界，所有真实 OS/COM 调用都被替换。"""

    def __init__(self, tmp_path: Path) -> None:
        self.project_path = str(
            (tmp_path / "runs" / "run_001" / "projects" / "working.cst").resolve()
        )
        self.other_project_path = str((tmp_path / "other" / "other.cst").resolve())
        self.processes: list[dict[str, Any]] = _services()
        self.processes_after: list[dict[str, Any]] | None = None
        self.discovery_sequence: list[list[dict[str, Any]]] | None = None
        self.discoveries = 0
        self.lock_files: list[Path] = []
        self.open_projects_result: dict[str, Any] = {
            "status": "success",
            "open_projects": [],
            "count": 0,
            "design_environment_count": 0,
            "failures": [],
        }
        self.identity_result: dict[str, Any] = {
            "status": "error",
            "error_type": "project_not_open",
            "open_projects": [],
            "expected_project_path": self.project_path,
        }
        self.solver_result: dict[str, Any] = {
            "status": "success",
            "running": False,
            "design_environment_pid": None,
            "runtime_module": "cst_runtime.core.identity",
        }
        self.lease: dict[str, Any] = {
            "known": False,
            "design_environment_pid": None,
            "ownership": "none",
        }
        self.stop_calls: list[tuple[int, str]] = []
        self.stop_results: dict[int, dict[str, Any]] = {}
        self.probe_calls: list[tuple[str, int | None]] = []

    # --- 场景构造 ---------------------------------------------------------
    def open_target(
        self,
        pid: int = TARGET_PID,
        *,
        external: bool = False,
        with_lock: bool = True,
    ) -> int:
        self.processes = [*_services(), _de(pid)]
        self.open_projects_result = {
            "status": "success",
            "open_projects": [_open_project(self.project_path, pid)],
            "count": 1,
            "design_environment_count": 1,
            "failures": [],
        }
        self.identity_result = {
            "status": "success",
            "expected_project_path": self.project_path,
            "open_projects": [self.project_path],
            "design_environment_pid": pid,
            "runtime_module": "cst_runtime.core.identity",
        }
        if with_lock:
            companion = Path(self.project_path).with_suffix("")
            self.lock_files = [companion / "working.lok"]
        if external:
            self.lease = {
                "known": False,
                "design_environment_pid": None,
                "ownership": "none",
            }
        else:
            self.lease = {
                "known": True,
                "design_environment_pid": pid,
                "ownership": "runtime_owned",
            }
        return pid

    def add_unrelated_open_project(self, pid: int = UNRELATED_PID) -> None:
        self.processes = [*self.processes, _de(pid)]
        self.open_projects_result = {
            "status": "success",
            "open_projects": [
                _open_project(self.project_path, TARGET_PID),
                _open_project(self.other_project_path, pid),
            ],
            "count": 2,
            "design_environment_count": 2,
            "failures": [],
        }

    # --- 打桩 -------------------------------------------------------------
    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        environment = self

        def discover() -> list[dict[str, Any]]:
            environment.discoveries += 1
            if environment.discovery_sequence is not None:
                if environment.discovery_sequence:
                    return copy.deepcopy(environment.discovery_sequence.pop(0))
                fallback = environment.processes_after
                if fallback is None:
                    fallback = environment.processes
                return copy.deepcopy(fallback)
            return copy.deepcopy(environment.processes)

        def list_open_projects() -> dict[str, Any]:
            return copy.deepcopy(environment.open_projects_result)

        def verify_project_identity(project_path: str) -> dict[str, Any]:
            payload = copy.deepcopy(environment.identity_result)
            payload.setdefault("expected_project_path", str(project_path))
            return payload

        def probe_target_solver_state(
            project_path: str,
            design_environment_pid: int | None = None,
        ) -> dict[str, Any]:
            environment.probe_calls.append(
                (os.path.normcase(os.path.abspath(str(project_path))), design_environment_pid)
            )
            return copy.deepcopy(environment.solver_result)

        def runtime_session_lease(project_path: str) -> dict[str, Any]:
            return dict(environment.lease)

        def stop_process(pid: int, name: str) -> dict[str, Any]:
            environment.stop_calls.append((int(pid), str(name)))
            result = environment.stop_results.get(int(pid))
            if result is None:
                result = {"status": "killed", "pid": int(pid), "name": str(name)}
            return copy.deepcopy(result)

        monkeypatch.setattr(process_core, "_discover_cst_processes", discover)
        monkeypatch.setattr(
            process_core,
            "find_lock_files",
            lambda project_path: list(environment.lock_files),
        )
        monkeypatch.setattr(process_core, "stop_process", stop_process)
        monkeypatch.setattr(process_core.project_identity, "list_open_projects", list_open_projects)
        monkeypatch.setattr(
            process_core.project_identity,
            "verify_project_identity",
            verify_project_identity,
        )
        monkeypatch.setattr(
            process_core.project_identity,
            "probe_target_solver_state",
            probe_target_solver_state,
        )
        monkeypatch.setattr(process_core, "_runtime_session_lease", runtime_session_lease)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> FakeEnvironment:
    environment = FakeEnvironment(tmp_path)
    environment.install(monkeypatch)
    return environment


def _normalized(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


# ---------------------------------------------------------------------------
# 覆盖点 2：只有共享服务时，检查必须 clear 且没有清理候选
# ---------------------------------------------------------------------------
def test_services_only_are_classified_retained_and_never_cleanup(env: FakeEnvironment) -> None:
    env.processes = _services()

    result = process_core.inspect_cst_environment(env.project_path, "write")

    assert result["status"] == "success", result
    assert result["operation"] == "write"
    assert result["process_count"] == 3
    assert result["background_service_count"] == 3
    assert result["target_process_count"] == 0
    assert result["readiness"] == "clear", result
    assert result["cleanup_required"] is False, result
    assert result["cleanup_candidates"] == [], result
    assert _conflicts(result) == [], result
    assert "cleanup-cst-processes" not in _next_steps_text(result)

    classified = {str(item["classification"]) for item in result["processes"]}
    assert classified == {"license_service", "dc_controller", "dc_solver_server"}
    for item in result["processes"]:
        assert item["is_background_service"] is True
        assert item["target_relation"] == "shared_service"
        assert item["may_terminate_by_default"] is False
    assert _pids(result["background_processes"]) == list(SERVICE_PIDS)
    assert _pids(result["target_processes"]) == []
    assert _pids(result["unrelated_processes"]) == []
    assert "service" in _notes_text(result).lower()
    assert result["target"]["open"] is False
    assert result["target"]["session_ownership"] == "none"


# ---------------------------------------------------------------------------
# 覆盖点 3：无关 Design Environment 不影响写操作，也不进入候选
# ---------------------------------------------------------------------------
def test_unrelated_design_environment_never_blocks_write(env: FakeEnvironment) -> None:
    env.processes = [*_services(), _de(UNRELATED_PID)]
    env.open_projects_result = {
        "status": "success",
        "open_projects": [_open_project(env.other_project_path, UNRELATED_PID)],
        "count": 1,
        "design_environment_count": 1,
        "failures": [],
    }
    env.identity_result = {
        "status": "error",
        "error_type": "project_not_open",
        "open_projects": [env.other_project_path],
    }

    result = process_core.inspect_cst_environment(env.project_path, "write")

    assert result["status"] == "success", result
    assert result["readiness"] == "clear", result
    assert _conflicts(result) == [], result
    assert result["cleanup_required"] is False
    assert result["cleanup_candidates"] == []
    unrelated = [item for item in result["processes"] if int(item["pid"]) == UNRELATED_PID]
    assert unrelated, result["processes"]
    assert unrelated[0]["target_relation"] == "other_session"
    # 契约：is_background_service == (classification != "design_environment")
    assert unrelated[0]["is_background_service"] is False
    assert unrelated[0]["may_terminate_by_default"] is False
    assert _pids(result["unrelated_processes"]) == [UNRELATED_PID]
    assert _pids(result["background_processes"]) == list(SERVICE_PIDS)
    assert UNRELATED_PID not in _pids(result["cleanup_candidates"])
    assert _pids(result["target_processes"]) == []
    assert "unrelated" in _notes_text(result).lower()
    assert "cleanup-cst-processes" not in _next_steps_text(result)


# ---------------------------------------------------------------------------
# 覆盖点 4：目标工程已被 Runtime 打开时，检查/写放行，copy/reopen 被阻塞
# ---------------------------------------------------------------------------
def test_target_open_runtime_owned_intent_matrix(env: FakeEnvironment) -> None:
    env.open_target(TARGET_PID, with_lock=True)

    inspect_result = process_core.inspect_cst_environment(env.project_path, "inspect")
    assert inspect_result["status"] == "success", inspect_result
    assert inspect_result["readiness"] == "clear", inspect_result
    assert _conflicts(inspect_result) == []
    assert inspect_result["target"]["open"] is True
    assert inspect_result["target"]["locked"] is True
    assert inspect_result["target"]["identity_confirmed"] is True
    assert inspect_result["target"]["session_ownership"] == "runtime_owned"
    assert inspect_result["target"]["design_environment_pids"] == [TARGET_PID]
    assert inspect_result["lock_count"] >= 1

    write_result = process_core.inspect_cst_environment(env.project_path, "write")
    assert write_result["readiness"] != "blocked", write_result
    assert _blocking_conflicts(write_result) == [], write_result
    assert _conflict_kinds(write_result) == set(), write_result

    copy_result = process_core.inspect_cst_environment(env.project_path, "copy")
    assert copy_result["readiness"] == "blocked", copy_result
    target_open = _conflict(copy_result, "target_project_open")
    assert "copy" in target_open["blocks_operations"]
    assert "reopen" in target_open["blocks_operations"]
    assert "write" not in target_open["blocks_operations"]
    assert copy_result["target_release_required"] is True
    assert copy_result["safe_to_copy_or_reopen"] is False

    candidates = copy_result["cleanup_candidates"]
    assert _pids(candidates) == [TARGET_PID]
    candidate = candidates[0]
    assert candidate["name"] == DE_NAME
    assert candidate["classification"] == "design_environment"
    assert candidate["target_relation"] == "target_project_session"
    assert candidate["ownership"] == "runtime_owned"
    assert candidate["authorization"] == "runtime_owned"
    assert candidate["may_terminate"] is True
    assert not (set(SERVICE_PIDS) & set(_pids(candidates)))
    assert "cleanup-cst-processes" not in _next_steps_text(copy_result)


# ---------------------------------------------------------------------------
# 覆盖点 5：目标工程属于外部会话时，只允许检查/读取，写操作要求用户确认
# ---------------------------------------------------------------------------
def test_target_open_external_session_requires_confirmation(env: FakeEnvironment) -> None:
    env.open_target(TARGET_PID, external=True, with_lock=True)

    inspect_result = process_core.inspect_cst_environment(env.project_path, "inspect")
    assert inspect_result["status"] == "success", inspect_result
    assert inspect_result["target"]["session_ownership"] == "external_unknown"
    assert inspect_result["readiness"] == "attention_required", inspect_result
    assert "target_session_confirmation_required" in _conflict_kinds(inspect_result)
    assert _blocking_conflicts(inspect_result) == []

    write_result = process_core.inspect_cst_environment(env.project_path, "write")
    assert write_result["readiness"] == "blocked", write_result
    conflict = _conflict(write_result, "target_session_confirmation_required")
    assert "write" in conflict["blocks_operations"]
    assert "solve" in conflict["blocks_operations"]
    assert "inspect" not in conflict["blocks_operations"]
    assert _blocking_conflicts(write_result)[0]["kind"] == "target_session_confirmation_required"
    assert write_result["cleanup_required"] is False
    candidates = write_result["cleanup_candidates"]
    assert _pids(candidates) == [TARGET_PID]
    assert candidates[0]["authorization"] == "requires_user_authorization"
    assert candidates[0]["may_terminate"] is False
    assert "confirm" in _next_steps_text(write_result).lower()


# ---------------------------------------------------------------------------
# 覆盖点 6：只有锁文件、没有可见会话时，写/复制被阻塞，但绝不建议杀进程
# ---------------------------------------------------------------------------
def test_lock_without_visible_session_blocks_write_without_kill_instruction(
    env: FakeEnvironment,
) -> None:
    env.processes = _services()
    env.lock_files = [Path(env.project_path).with_suffix("") / "working.lok"]
    env.open_projects_result = {
        "status": "success",
        "open_projects": [],
        "count": 0,
        "design_environment_count": 0,
        "failures": [],
    }
    env.identity_result = {
        "status": "error",
        "error_type": "no_cst_session",
        "open_projects": [],
    }

    for operation in ("write", "copy"):
        result = process_core.inspect_cst_environment(env.project_path, operation)
        assert result["readiness"] == "blocked", result
        conflict = _conflict(result, "target_lock_without_visible_session")
        assert operation in conflict["blocks_operations"]
        assert conflict["target_related"] is True
        assert result["cleanup_required"] is True
        assert result["cleanup_candidates"] == []
        steps = _next_steps_text(result)
        assert "cleanup-cst-processes" not in steps
        lowered = steps.lower()
        assert any(
            word in lowered for word in ("identify", "owner", "owning", "wait")
        ), steps


# ---------------------------------------------------------------------------
# 覆盖点 7：多个目标 DE PID 或歧义身份时，连只读检查都必须 blocked
# ---------------------------------------------------------------------------
def test_multiple_target_pids_block_read_only_inspect(env: FakeEnvironment) -> None:
    env.processes = [*_services(), _de(TARGET_PID), _de(TARGET_PID + 1)]
    env.open_projects_result = {
        "status": "success",
        "open_projects": [
            _open_project(env.project_path, TARGET_PID),
            _open_project(env.project_path, TARGET_PID + 1),
        ],
        "count": 2,
        "design_environment_count": 2,
        "failures": [],
    }
    env.identity_result = {
        "status": "success",
        "expected_project_path": env.project_path,
        "open_projects": [env.project_path],
    }

    result = process_core.inspect_cst_environment(env.project_path, "inspect")

    assert result["readiness"] == "blocked", result
    conflict = _conflict(result, "target_session_ambiguous")
    assert "inspect" in conflict["blocks_operations"]
    assert result["target"]["design_environment_pids"] == [TARGET_PID, TARGET_PID + 1]
    assert result["target_release_required"] is True
    assert result["cleanup_required"] is True


def test_ambiguous_identity_blocks_read_only_inspect(env: FakeEnvironment) -> None:
    env.open_target(TARGET_PID)
    env.identity_result = {
        "status": "error",
        "error_type": "ambiguous_open_projects",
        "open_projects": [env.project_path, env.other_project_path],
    }

    result = process_core.inspect_cst_environment(env.project_path, "inspect")

    assert result["readiness"] == "blocked", result
    conflict = _conflict(result, "target_identity_ambiguous")
    assert "read" in conflict["blocks_operations"]
    assert "inspect" in conflict["blocks_operations"]
    assert result["target"]["identity_confirmed"] is False


# ---------------------------------------------------------------------------
# 覆盖点 8：身份列表失败时，写操作被占用未确认阻塞，并给出缺失信息
# ---------------------------------------------------------------------------
def test_identity_failure_blocks_write_but_not_read(env: FakeEnvironment) -> None:
    env.open_target(TARGET_PID)
    env.identity_result = {
        "status": "error",
        "error_type": "list_open_projects_failed",
        "open_projects": [],
        "failures": [{"design_environment_pid": TARGET_PID, "error": "COM unavailable"}],
    }

    read_result = process_core.inspect_cst_environment(env.project_path, "read")
    assert read_result["readiness"] != "blocked", read_result
    assert _blocking_conflicts(read_result) == [], read_result

    write_result = process_core.inspect_cst_environment(env.project_path, "write")
    assert write_result["readiness"] == "blocked", write_result
    conflict = _conflict(write_result, "target_occupancy_unconfirmed")
    assert "write" in conflict["blocks_operations"]
    assert "read" not in conflict["blocks_operations"]
    assert conflict["target_related"] is True
    assert conflict["missing_information"], conflict
    assert write_result["cleanup_required"] is True


# ---------------------------------------------------------------------------
# 覆盖点 9：求解器运行/不可读只阻塞写与求解，只读检查不探测求解器
# ---------------------------------------------------------------------------
def test_solver_running_blocks_write_but_not_read(env: FakeEnvironment) -> None:
    env.open_target(TARGET_PID)
    env.solver_result = {
        "status": "success",
        "running": True,
        "design_environment_pid": TARGET_PID,
        "runtime_module": "cst_runtime.core.identity",
    }

    read_result = process_core.inspect_cst_environment(env.project_path, "read")
    assert read_result["readiness"] != "blocked", read_result
    assert env.probe_calls == [], "只读检查不得探测求解器"

    write_result = process_core.inspect_cst_environment(env.project_path, "write")
    assert len(env.probe_calls) == 1
    probed_path, probed_pid = env.probe_calls[0]
    assert probed_path == _normalized(env.project_path)
    assert probed_pid == TARGET_PID
    assert write_result["readiness"] == "blocked", write_result
    conflict = _conflict(write_result, "target_solver_running")
    assert "write" in conflict["blocks_operations"]
    assert "read" not in conflict["blocks_operations"]
    assert write_result["target"]["solver"]["running"] is True
    assert write_result["target"]["solver"]["checked"] is True


def test_solver_state_unreadable_blocks_write(env: FakeEnvironment) -> None:
    env.open_target(TARGET_PID)
    env.solver_result = {
        "status": "error",
        "error_type": "solver_state_unreadable",
        "message": "COM query failed",
        "running": None,
        "design_environment_pid": TARGET_PID,
        "runtime_module": "cst_runtime.core.identity",
    }

    write_result = process_core.inspect_cst_environment(env.project_path, "write")

    assert write_result["readiness"] == "blocked", write_result
    conflict = _conflict(write_result, "target_solver_state_unknown")
    assert "write" in conflict["blocks_operations"]
    assert conflict["missing_information"], conflict
    assert write_result["target"]["solver"]["status"] == "error"
    assert write_result["target"]["solver"]["running"] is None


# ---------------------------------------------------------------------------
# 覆盖点 10/12：清理候选范围在 dry_run 与真实执行之间完全一致；
# 共享服务与无关 DE 永远不是 target 范围候选。
# ---------------------------------------------------------------------------
def test_cleanup_dry_run_and_actual_share_candidate_scope(env: FakeEnvironment) -> None:
    before = [*_services(), _de(TARGET_PID), _de(UNRELATED_PID)]
    after = [*_services(), _de(UNRELATED_PID)]
    env.processes = copy.deepcopy(after)
    env.processes_after = copy.deepcopy(after)
    env.discovery_sequence = [copy.deepcopy(before), copy.deepcopy(after)]
    env.open_projects_result = {
        "status": "success",
        "open_projects": [
            _open_project(env.project_path, TARGET_PID),
            _open_project(env.other_project_path, UNRELATED_PID),
        ],
        "count": 2,
        "design_environment_count": 2,
        "failures": [],
    }
    env.identity_result = {
        "status": "success",
        "expected_project_path": env.project_path,
        "open_projects": [env.project_path],
        "design_environment_pid": TARGET_PID,
    }
    env.lease = {
        "known": True,
        "design_environment_pid": TARGET_PID,
        "ownership": "runtime_owned",
    }

    actual = process_core.cleanup_cst_processes(
        project_path=env.project_path,
        dry_run=False,
        settle_seconds=0.0,
    )
    assert actual["status"] == "success", actual
    assert actual["cleanup_status"] == "completed", actual
    assert actual["completed"] is True
    assert actual["scope"] == "target"
    assert _pids(actual["candidates"]) == [TARGET_PID]
    assert env.stop_calls == [(TARGET_PID, DE_NAME)]
    assert _pids(actual["services_retained"]) == list(SERVICE_PIDS)
    assert _pids(actual["unrelated_processes_retained"]) == [UNRELATED_PID]
    assert actual["unhandled_processes"] == []
    candidates = actual["candidates"]
    assert all(item["classification"] == "design_environment" for item in candidates)
    assert all(item["target_relation"] == "target_project_session" for item in candidates)
    assert not (set(SERVICE_PIDS) & set(_pids(candidates)))
    assert UNRELATED_PID not in _pids(candidates)

    # 同一场景的 dry_run 必须给出完全相同的候选范围，且不调用 stop_process。
    env.discovery_sequence = None
    env.processes = copy.deepcopy(before)
    env.processes_after = None
    env.stop_calls.clear()
    dry = process_core.cleanup_cst_processes(
        project_path=env.project_path,
        dry_run=True,
        settle_seconds=0.0,
    )
    assert dry["status"] == "success", dry
    assert dry["cleanup_status"] == "dry_run", dry
    assert dry["completed"] is False
    assert _pids(dry["candidates"]) == _pids(actual["candidates"])
    assert env.stop_calls == []
    assert _pids(dry["services_retained"]) == list(SERVICE_PIDS)
    assert _pids(dry["unrelated_processes_retained"]) == [UNRELATED_PID]

    # 检查视图的候选范围必须与清理视图一致。
    inspect_result = process_core.inspect_cst_environment(env.project_path, "inspect")
    assert _pids(inspect_result["cleanup_candidates"]) == _pids(actual["candidates"])
    assert not (set(SERVICE_PIDS) & set(_pids(inspect_result["cleanup_candidates"])))
    assert UNRELATED_PID not in _pids(inspect_result["cleanup_candidates"])


# ---------------------------------------------------------------------------
# 覆盖点 11：Access is denied 必须保留在审计与未处理列表，清理不能算完成
# ---------------------------------------------------------------------------
def test_access_denied_is_unhandled_and_never_filtered(env: FakeEnvironment) -> None:
    env.open_target(TARGET_PID)
    env.processes_after = copy.deepcopy(env.processes)
    env.discovery_sequence = [copy.deepcopy(env.processes), copy.deepcopy(env.processes)]
    env.stop_results[TARGET_PID] = {
        "status": "failed",
        "pid": TARGET_PID,
        "name": DE_NAME,
        "error": "Access is denied.",
    }

    result = process_core.cleanup_cst_processes(
        project_path=env.project_path,
        dry_run=False,
        settle_seconds=0.0,
    )

    assert result["status"] == "error", result
    assert result["error_type"] == "cleanup_cst_processes_incomplete", result
    assert result["cleanup_status"] == "incomplete", result
    assert result["completed"] is False
    assert _pids(result["unhandled_processes"]) == [TARGET_PID]
    assert TARGET_PID in _pids(result["processes_after"]), result["processes_after"]
    denied = result["access_denied"]
    assert denied, result
    assert any(int(item.get("pid")) == TARGET_PID for item in denied), denied
    assert _pids(result["services_retained"]) == list(SERVICE_PIDS)
    note = str(result.get("note", "")).lower()
    assert "access is denied" in note
    assert "unhandled" in note


# ---------------------------------------------------------------------------
# 覆盖点 12：target 范围内真实清理外部会话，只能报授权错误且绝不终止
# ---------------------------------------------------------------------------
def test_target_scope_external_session_requires_authorization(env: FakeEnvironment) -> None:
    env.open_target(TARGET_PID, external=True)

    dry = process_core.cleanup_cst_processes(
        project_path=env.project_path,
        dry_run=True,
        settle_seconds=0.0,
    )
    assert dry["status"] == "success", dry
    assert dry["would_require_authorization"] is True, dry
    assert _pids(dry["candidates"]) == [TARGET_PID]
    assert dry["completed"] is False
    assert env.stop_calls == []

    actual = process_core.cleanup_cst_processes(
        project_path=env.project_path,
        dry_run=False,
        settle_seconds=0.0,
    )
    assert actual["status"] == "error", actual
    assert actual["error_type"] == "cleanup_authorization_required", actual
    assert (
        actual.get("authorization_required")
        == "explicit_user_authorization_for_existing_session"
    ), actual
    assert _pids(actual["candidates"]) == [TARGET_PID]
    assert env.stop_calls == []


# ---------------------------------------------------------------------------
# 覆盖点 13：global 范围必须有显式确认，且共享服务始终保留
# ---------------------------------------------------------------------------
def test_global_scope_requires_confirmation_and_retains_services(
    env: FakeEnvironment,
) -> None:
    env.processes = [*_services(), _de(TARGET_PID), _de(UNRELATED_PID)]

    unauthorized = process_core.cleanup_cst_processes(
        project_path=env.project_path,
        dry_run=False,
        settle_seconds=0.0,
        scope="global",
    )
    assert unauthorized["status"] == "error", unauthorized
    assert unauthorized["error_type"] == "cleanup_authorization_required", unauthorized
    assert env.stop_calls == []

    dry = process_core.cleanup_cst_processes(
        project_path=env.project_path,
        dry_run=True,
        settle_seconds=0.0,
        scope="global",
        confirm_global_cleanup=True,
    )
    assert dry["status"] == "success", dry
    assert set(_pids(dry["candidates"])) == {TARGET_PID, UNRELATED_PID}
    assert not (set(SERVICE_PIDS) & set(_pids(dry["candidates"])))
    assert _pids(dry["services_retained"]) == list(SERVICE_PIDS)
    assert env.stop_calls == []

    after = _services()
    env.processes_after = copy.deepcopy(after)
    env.discovery_sequence = [copy.deepcopy(env.processes), copy.deepcopy(after)]
    actual = process_core.cleanup_cst_processes(
        project_path=env.project_path,
        dry_run=False,
        settle_seconds=0.0,
        scope="global",
        confirm_global_cleanup=True,
    )
    assert actual["status"] == "success", actual
    assert {pid for pid, _ in env.stop_calls} == {TARGET_PID, UNRELATED_PID}
    assert not (set(SERVICE_PIDS) & {pid for pid, _ in env.stop_calls})
    assert _pids(actual["services_retained"]) == list(SERVICE_PIDS)


# ---------------------------------------------------------------------------
# 覆盖点 14：孤儿清理默认只报告，不终止任何进程
# ---------------------------------------------------------------------------
def test_orphan_cleanup_is_report_only_by_default(env: FakeEnvironment) -> None:
    env.processes = [*_services(), _de(ORPHAN_PID)]
    env.open_projects_result = {
        "status": "success",
        "open_projects": [],
        "count": 0,
        "design_environment_count": 0,
        "failures": [],
    }
    env.identity_result = {
        "status": "error",
        "error_type": "no_cst_session",
        "open_projects": [],
    }

    report = process_core.cleanup_orphan_processes(settle_seconds=0.0)

    assert report["status"] == "success", report
    assert report["cleanup_status"] == "report_only", report
    assert _pids(report["candidates"]) == [ORPHAN_PID]
    assert env.stop_calls == []

    confirmed = process_core.cleanup_orphan_processes(
        settle_seconds=0.0,
        confirm_terminate=True,
    )
    assert _pids(confirmed["candidates"]) == [ORPHAN_PID]
    assert [pid for pid, _ in env.stop_calls] == [ORPHAN_PID]
    assert env.stop_calls[0][1] == DE_NAME
    assert not (set(SERVICE_PIDS) & {pid for pid, _ in env.stop_calls})


# ---------------------------------------------------------------------------
# 覆盖点 15：非法 operation 必须显式报错
# ---------------------------------------------------------------------------
def test_invalid_operation_is_rejected(env: FakeEnvironment) -> None:
    result = process_core.inspect_cst_environment(env.project_path, "delete")

    assert result["status"] == "error", result
    assert result["error_type"] == "invalid_operation", result
    assert result["runtime_module"] == "cst_runtime.core.process"
    allowed = set(result.get("allowed_operations") or [])
    assert {"inspect", "read", "write", "solve", "copy", "reopen"} <= allowed
    assert "delete" not in allowed


# ---------------------------------------------------------------------------
# 覆盖点 16：没有 project_path 时检查仍是安全 JSON，不产生冲突或清理要求
# ---------------------------------------------------------------------------
def test_inspect_without_project_path_is_safe(env: FakeEnvironment) -> None:
    env.processes = _services()
    env.open_projects_result = {
        "status": "error",
        "error_type": "no_cst_session",
        "open_projects": [],
        "message": "No DEs found to connect to.",
    }

    result = process_core.inspect_cst_environment()

    assert result["status"] == "success", result
    assert result["project_path"] == ""
    assert result["operation"] == "inspect"
    assert result["readiness"] == "clear", result
    assert _conflicts(result) == [], result
    assert result["cleanup_required"] is False
    assert result["cleanup_candidates"] == []
    assert result["target"]["open"] is False
    assert result["target"]["project_path"] == ""
    assert result["target"]["session_ownership"] == "none"
    assert _pids(result["cleanup_candidates"]) == []
    steps = _next_steps_text(result)
    assert "project_path" in steps
    assert "cleanup-cst-processes" not in steps
    # 兼容字段仍然存在
    for key in (
        "force_kill_allowlist",
        "processes",
        "process_count",
        "lock_files",
        "lock_count",
        "open_projects_status",
        "project_identity_status",
        "cleanup_required",
        "safe_to_copy_or_reopen",
        "next_steps",
        "runtime_module",
    ):
        assert key in result, key


def test_target_scope_cleanup_without_project_path_has_no_candidates(
    env: FakeEnvironment,
) -> None:
    env.processes = [*_services(), _de(TARGET_PID)]

    result = process_core.cleanup_cst_processes(
        project_path="",
        dry_run=True,
        settle_seconds=0.0,
    )

    assert result["status"] == "success", result
    assert result["candidates"] == []
    assert env.stop_calls == []
