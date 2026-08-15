"""会话与工程只读操作的真实 CST 2022 集成测试。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from cst_helpers import normalized, project_arguments


pytestmark = [
    pytest.mark.cst_integration,
    pytest.mark.cst_destructive,
]


def test_session_inspect_reports_sole_project(cst_case: Any) -> None:
    """cst-session-inspect 必须看到唯一隔离工程与唯一 DE（打开中的工程持锁 → blocked）。"""
    result = cst_case.require_success(
        "cst-session-inspect",
        project_arguments(cst_case),
    )
    open_status = result["open_projects_status"]
    assert open_status["status"] == "success", result
    projects = list(open_status.get("open_projects", []))
    assert len(projects) == 1, result
    assert normalized(projects[0]["project_path"]) == normalized(cst_case.project_path)
    assert open_status["design_environment_count"] == 1, result
    assert result["project_identity_status"]["status"] == "success", result
    # 工程处于打开状态，CST 持有锁文件，readiness 必须如实上报 blocked。
    assert result["readiness"] == "blocked", result
    assert result["lock_count"] >= 1, result
    cst_case.shared.require_visible_window()


def test_verify_project_identity_confirms_expected(cst_case: Any) -> None:
    """身份校验必须精确匹配期望路径与当前 DE PID。"""
    result = cst_case.require_success(
        "verify-project-identity",
        project_arguments(cst_case),
    )
    assert normalized(result["expected_project_path"]) == normalized(cst_case.project_path)
    assert result["design_environment_pid"] == cst_case.shared.design_environment_pid


def test_wait_project_unlocked_reports_open_project_locks(cst_case: Any) -> None:
    """打开中的工程持有锁文件：工具必须在超时后如实返回 lock_not_released。"""
    result = cst_case.call(
        "wait-project-unlocked",
        project_arguments(cst_case, timeout_seconds=2, poll_interval_seconds=0.5),
    )
    assert result.get("status") == "error", result
    assert result.get("error_type") == "lock_not_released", result
    assert result.get("locked") is True, result
    assert result.get("lock_files"), result


def test_save_project_roundtrip_advances_file(cst_case: Any) -> None:
    """save-project 必须真实落盘（mtime 不倒退、文件非空）。"""
    path = Path(cst_case.project_path)
    before = path.stat()
    result = cst_case.require_success("save-project", project_arguments(cst_case))
    assert normalized(result["project_path"]) == normalized(path)
    after = path.stat()
    assert path.is_file() and after.st_size > 0
    assert after.st_mtime_ns >= before.st_mtime_ns
    cst_case.shared.require_visible_window()


def test_session_reattach_keeps_sole_project(cst_case: Any) -> None:
    """重新附着后仍只看到唯一隔离工程。"""
    cst_case.require_success("cst-session-reattach", project_arguments(cst_case))
    opened = cst_case.require_success("list-open-projects", {})
    projects = list(opened.get("open_projects", []))
    assert len(projects) == 1, opened
    assert normalized(projects[0]["project_path"]) == normalized(cst_case.project_path)


def test_infer_run_dir_resolves_or_none(cst_case: Any) -> None:
    """共享工程不在 projects/ 布局下，run_dir 只能是 None 或绝对路径。"""
    result = cst_case.require_success("infer-run-dir", project_arguments(cst_case))
    run_dir = result.get("run_dir")
    assert run_dir is None or isinstance(run_dir, str), result


def test_is_simulation_running_idle_false(cst_case: Any) -> None:
    """任何求解器启动前，运行状态必须是 False。"""
    result = cst_case.require_success(
        "is-simulation-running",
        project_arguments(cst_case),
    )
    assert result["running"] is False, result
