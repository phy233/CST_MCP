"""CST Runtime 测试的公共 Pytest 配置和夹具。"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest import mock

import pytest


SKILL_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-cst",
        action="store_true",
        default=False,
        help="显式运行需要真实 CST 2022 和许可证的串行集成测试",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "cst_integration: 需要真实 CST 安装和许可证的串行集成测试",
    )
    config.addinivalue_line(
        "markers",
        "cst_solver: 会短暂启动并强制停止真实 CST 求解器的测试",
    )
    config.addinivalue_line(
        "markers",
        "cst_destructive: 会修改隔离工程但必须在测试内清理的真机测试",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """普通 pytest 明确跳过真机层，只有 --run-cst 才允许执行。"""
    if config.getoption("--run-cst"):
        return
    skip = pytest.mark.skip(reason="使用 --run-cst 后才运行真实 CST 集成测试")
    for item in items:
        if "cst_integration" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def mocker(monkeypatch: pytest.MonkeyPatch):
    """项目内置的轻量 pytest-mock 兼容夹具。"""

    class Mocker:
        MagicMock = mock.MagicMock

    active_patchers: list[Any] = []

    class ManagedMocker(Mocker):
        @staticmethod
        def patch(target: str, *args: Any, **kwargs: Any) -> Any:
            patcher = mock.patch(target, *args, **kwargs)
            active_patchers.append(patcher)
            return patcher.start()

    yield ManagedMocker()
    for patcher in reversed(active_patchers):
        patcher.stop()


@pytest.fixture(autouse=True)
def clear_gateway_registry():
    """隔离离线测试的网关内存状态和临时标记。"""
    from cst_runtime.core.gateway import (
        _dirty_marker_path,
        _farfield_marker_path,
        _registry,
    )

    for state in list(_registry.values()):
        for marker_path in (_dirty_marker_path, _farfield_marker_path):
            marker = marker_path(state.path)
            if marker.exists():
                try:
                    marker.unlink()
                except OSError:
                    pass
    _registry.clear()
    yield
    _registry.clear()


@pytest.fixture
def run_cli():
    """在子进程中运行 cst_runtime CLI，并解析 JSON 响应。"""
    python = sys.executable
    inherited_pythonpath = os.environ.get("PYTHONPATH", "")
    pythonpath = (
        str(SKILL_SCRIPTS)
        if not inherited_pythonpath
        else os.pathsep.join([str(SKILL_SCRIPTS), inherited_pythonpath])
    )

    def _run(*args: str) -> dict[str, Any]:
        completed = subprocess.run(
            [python, "-m", "cst_runtime", *args],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
            env={**os.environ, "PYTHONPATH": pythonpath},
            check=False,
        )
        if completed.stdout.strip():
            return json.loads(completed.stdout)
        return {"raw": completed.stdout, "returncode": completed.returncode}

    return _run


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_snapshot(source: Path) -> dict[str, str]:
    """记录源工程及伴随目录摘要，用于证明测试没有污染源文件。"""
    snapshot = {source.name: _file_digest(source)}
    companion = source.with_suffix("")
    if companion.is_dir():
        for path in sorted(item for item in companion.rglob("*") if item.is_file()):
            snapshot[path.relative_to(source.parent).as_posix()] = _file_digest(path)
    return snapshot


def _normalized_path(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _design_environment_processes() -> list[dict[str, Any]]:
    """不连接 CST，直接检查是否已有 Design Environment 进程。"""
    command = (
        "$items = @(Get-Process -ErrorAction SilentlyContinue | "
        "Where-Object { $_.ProcessName -like 'CST DESIGN ENVIRONMENT*' } | "
        "ForEach-Object { [pscustomobject]@{ pid = $_.Id; name = $_.ProcessName; "
        "title = $_.MainWindowTitle } }); $items | ConvertTo-Json -Depth 3"
    )
    completed = subprocess.run(
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
        timeout=15,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "无法检查 CST Design Environment 进程")
    raw = completed.stdout.strip()
    if not raw:
        return []
    value = json.loads(raw)
    if isinstance(value, dict):
        return [value]
    return [item for item in value if isinstance(item, dict)]


def _stop_design_environment(pid: int) -> None:
    """只终止本次 fixture 新创建且已确认归属测试的精确进程。"""
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"Stop-Process -Id {int(pid)} -Force -ErrorAction Stop",
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            completed.stderr.strip() or f"无法终止测试 Design Environment PID {pid}"
        )


@dataclass
class SharedCSTProject:
    """整个真机测试会话共享的唯一 CST 工程和 Worker。"""

    proxy: Any
    project_path: str
    source_path: Path
    temp_root: Path
    source_snapshot: dict[str, str]
    resources: list[tuple[str, str]] = field(default_factory=list)
    tainted: bool = False

    def call(
        self,
        tool: str,
        arguments: dict[str, Any] | None = None,
        *,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        payload = dict(arguments or {})
        response = self.proxy.call_tool(tool, payload, timeout=timeout)
        print(
            json.dumps(
                {"tool": tool, "arguments": payload, "result": response},
                ensure_ascii=False,
            ),
            flush=True,
        )
        return response

    def require_success(
        self,
        tool: str,
        arguments: dict[str, Any] | None = None,
        *,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        result = self.call(tool, arguments, timeout=timeout)
        assert result.get("status") == "success", result
        return result

    def list_entities(self, component: str = "") -> list[dict[str, str]]:
        result = self.require_success(
            "list-entities",
            {"project_path": self.project_path, "component": component},
        )
        return list(result.get("entities", []))

    def entity_exists(self, component: str, name: str) -> bool:
        return any(
            item.get("component", "").casefold() == component.casefold()
            and item.get("name") == name
            for item in self.list_entities(component)
        )

    def register_entity(self, component: str, name: str) -> None:
        resource = (component, name)
        if resource not in self.resources:
            self.resources.append(resource)

    def forget_entity(self, component: str, name: str) -> None:
        resource = (component, name)
        if resource in self.resources:
            self.resources.remove(resource)

    def delete_entity(self, component: str, name: str) -> None:
        self.require_success(
            "delete-entity",
            {"project_path": self.project_path, "component": component, "name": name},
        )
        assert not self.entity_exists(component, name)
        self.forget_entity(component, name)


@dataclass
class CSTCase:
    """为单个测试提供唯一名称和成对资源清理。"""

    shared: SharedCSTProject
    prefix: str

    @property
    def project_path(self) -> str:
        return self.shared.project_path

    def name(self, suffix: str) -> str:
        return f"{self.prefix}_{suffix}"

    def call(
        self,
        tool: str,
        arguments: dict[str, Any] | None = None,
        *,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        return self.shared.call(tool, arguments, timeout=timeout)

    def require_success(
        self,
        tool: str,
        arguments: dict[str, Any] | None = None,
        *,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        return self.shared.require_success(tool, arguments, timeout=timeout)


@pytest.fixture(scope="session")
def shared_cst_project(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> SharedCSTProject:
    """复制并打开唯一隔离工程，结束时关闭、验证并删除全部痕迹。"""
    if not request.config.getoption("--run-cst"):
        pytest.skip("使用 --run-cst 后才创建真实 CST 工程")
    if os.environ.get("PYTEST_XDIST_WORKER"):
        pytest.fail("真实 CST 测试禁止使用 pytest-xdist 并行执行")

    from mcp_server.proxy import CSTWorkerProxy

    default_source = Path(__file__).resolve().parent / "refs" / "ref_0" / "ref_0.cst"
    source = Path(os.environ.get("CST_TEST_PROJECT", str(default_source))).expanduser().resolve()
    assert source.is_file(), f"找不到 CST 测试基准工程：{source}"
    source_snapshot = _source_snapshot(source)

    proxy = CSTWorkerProxy.get_instance()
    preflight = proxy.call_tool("list-open-projects", {}, timeout=30)
    print(
        json.dumps(
            {"tool": "list-open-projects", "arguments": {}, "result": preflight},
            ensure_ascii=False,
        ),
        flush=True,
    )
    if preflight.get("status") == "success" and preflight.get("open_projects"):
        proxy.shutdown()
        pytest.fail(f"检测到已有 CST 工程，拒绝启动真机测试：{preflight}")
    if (
        preflight.get("status") == "error"
        and preflight.get("error_type") != "no_cst_session"
    ):
        proxy.shutdown()
        pytest.fail(f"无法证明 CST 启动前没有打开工程：{preflight}")

    existing_environments = _design_environment_processes()
    if existing_environments:
        proxy.shutdown()
        pytest.fail(
            "检测到已有 CST Design Environment，拒绝启动真机测试："
            f"{existing_environments}"
        )

    temp_root = tmp_path_factory.mktemp("cst-shared-session")
    working = temp_root / "working.cst"
    shutil.copy2(source, working)
    companion = source.with_suffix("")
    if companion.is_dir():
        shutil.copytree(companion, working.with_suffix(""))

    baseline_pids = {int(item["pid"]) for item in existing_environments}
    try:
        opened = proxy.call_tool(
            "cst-session-open",
            {"project_path": str(working)},
            timeout=300,
        )
        if opened.get("status") != "success":
            raise RuntimeError(f"唯一 CST 测试工程打开失败：{opened}")
    except Exception as exc:
        proxy.shutdown()
        cleanup_errors: list[str] = []
        for item in _design_environment_processes():
            pid = int(item["pid"])
            if pid in baseline_pids:
                continue
            try:
                _stop_design_environment(pid)
            except Exception as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
        if not cleanup_errors:
            shutil.rmtree(temp_root, ignore_errors=True)
        detail = f"；兜底清理失败：{'；'.join(cleanup_errors)}" if cleanup_errors else ""
        pytest.fail(f"真实 CST 工程打开失败：{exc}{detail}", pytrace=False)

    shared = SharedCSTProject(
        proxy=proxy,
        project_path=str(working.resolve()),
        source_path=source,
        temp_root=temp_root,
        source_snapshot=source_snapshot,
    )
    visible = shared.require_success("list-open-projects", {})
    visible_paths = {
        _normalized_path(item.get("project_path", ""))
        for item in visible.get("open_projects", [])
    }
    assert visible_paths == {_normalized_path(shared.project_path)}, visible

    teardown_errors: list[str] = []
    try:
        yield shared
    finally:
        try:
            running = shared.call(
                "is-simulation-running",
                {"project_path": shared.project_path},
            )
            if running.get("status") == "success" and running.get("running"):
                stopped = shared.call(
                    "stop-simulation",
                    {"project_path": shared.project_path},
                )
                if stopped.get("status") != "success":
                    teardown_errors.append(f"求解器停止失败：{stopped}")
        except Exception as exc:
            teardown_errors.append(f"求解器兜底检查失败：{exc}")

        for component, name in reversed(shared.resources.copy()):
            try:
                if shared.entity_exists(component, name):
                    shared.delete_entity(component, name)
                else:
                    shared.forget_entity(component, name)
            except Exception as exc:
                teardown_errors.append(f"实体兜底删除失败 {component}:{name}：{exc}")

        try:
            closed = shared.call(
                "cst-session-close",
                {
                    "project_path": shared.project_path,
                    "save": False,
                    "wait_unlock": True,
                    "timeout_seconds": 30,
                    "poll_interval_seconds": 0.5,
                    "kill_processes": False,
                },
            )
            if closed.get("status") != "success":
                teardown_errors.append(f"测试工程关闭失败：{closed}")
        except Exception as exc:
            teardown_errors.append(f"测试工程关闭异常：{exc}")

        try:
            deadline = time.monotonic() + 30
            remaining_environments = _design_environment_processes()
            while remaining_environments and time.monotonic() < deadline:
                time.sleep(0.5)
                remaining_environments = _design_environment_processes()
            if remaining_environments:
                teardown_errors.append(
                    f"测试结束后仍有 CST Design Environment：{remaining_environments}"
                )
        except Exception as exc:
            teardown_errors.append(f"最终进程状态检查失败：{exc}")

        proxy.shutdown()
        if _source_snapshot(source) != source_snapshot:
            teardown_errors.append(f"源工程被测试修改：{source}")
        if not teardown_errors:
            shutil.rmtree(temp_root)
        if teardown_errors:
            pytest.fail("；".join(teardown_errors), pytrace=False)


@pytest.fixture
def cst_case(shared_cst_project: SharedCSTProject) -> CSTCase:
    """提供单用例名称空间，并在失败后立即清理已登记实体。"""
    if shared_cst_project.tainted:
        pytest.exit("共享 CST 工程已被标记为污染，停止剩余真机测试")
    case = CSTCase(
        shared=shared_cst_project,
        prefix=f"pytest_{uuid.uuid4().hex[:10]}",
    )
    before = set(shared_cst_project.resources)
    try:
        yield case
    finally:
        cleanup_errors: list[str] = []
        added = [item for item in shared_cst_project.resources if item not in before]
        for component, name in reversed(added):
            try:
                if shared_cst_project.entity_exists(component, name):
                    shared_cst_project.delete_entity(component, name)
                else:
                    shared_cst_project.forget_entity(component, name)
            except Exception as exc:
                cleanup_errors.append(f"{component}:{name}：{exc}")
        if cleanup_errors:
            shared_cst_project.tainted = True
            pytest.fail("单用例资源清理失败：" + "；".join(cleanup_errors), pytrace=False)


@pytest.fixture
def temp_workspace(tmp_path: Path, run_cli):
    """创建隔离的 Runtime 工作区。"""
    result = run_cli("init-workspace", "--workspace", str(tmp_path))
    assert result["status"] == "success"
    return tmp_path
