"""MCP 纯适配层测试。"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_config_has_separate_worker_runtime() -> None:
    from mcp_server.config import get_config

    config = get_config()
    assert config.server_name == "cst-runtime"
    assert config.worker_python.name.lower() == "python.exe"
    assert "IPC" in config.instructions


@pytest.mark.worker_proxy
def test_proxy_reads_runtime_owned_manifest() -> None:
    from mcp_server.proxy import CSTWorkerProxy

    proxy = CSTWorkerProxy()
    try:
        tools = proxy.describe_tools()
        names = {tool["name"] for tool in tools}
        assert len(tools) >= 100
        assert {"build-array", "quick-sweep"} <= names
        assert "add-to-history" not in names
        assert "activate-post-process" not in names
        assert all(tool["input_schema"]["type"] == "object" for tool in tools)
    finally:
        proxy.shutdown()


def test_server_uses_low_level_mcp() -> None:
    from mcp.server import Server
    from mcp_server.server import create_mcp_server

    server = create_mcp_server()
    assert isinstance(server, Server)


def test_mcp_layer_does_not_import_runtime() -> None:
    violations: list[str] = []
    for path in (PROJECT_ROOT / "mcp_server").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "cst_runtime" or alias.name.startswith("cst_runtime."):
                        violations.append(f"{path.name}:{node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and (
                    node.module == "cst_runtime"
                    or node.module.startswith("cst_runtime.")
                ):
                    violations.append(f"{path.name}:{node.lineno}")
    assert not violations


def test_mcp_only_uses_runtime_registry_through_worker() -> None:
    """MCP 服务不得绕过 Worker 直接依赖 Runtime 的内部层。"""
    forbidden = ("cst_runtime.core", "cst_runtime.lib", "cst_runtime.tools")
    violations: list[str] = []
    for path in (PROJECT_ROOT / "mcp_server").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            for module in modules:
                if module.startswith(forbidden):
                    violations.append(f"{path.name}:{node.lineno}:{module}")

    assert not violations


def test_transport_error_is_returned_as_mcp_error_envelope() -> None:
    from mcp_server.proxy import CSTTransportError
    from mcp_server.server import _call_tool_with_transport_envelope

    class FailingProxy:
        def call_tool(self, name, arguments, *, timeout, timeout_class="abnormal"):
            raise CSTTransportError(
                "worker timed out",
                code="worker_request_timeout",
                context={"action": "call_tool"},
            )

    result = _call_tool_with_transport_envelope(
        FailingProxy(),
        "define-brick",
        {"name": "demo"},
        timeout=1,
    )

    assert result["ok"] is False
    assert result["error_type"] == "transport_error"
    assert result["error"]["phase"] == "transport"
    assert result["error"]["code"] == "worker_request_timeout"
    assert result["context"]["tool_name"] == "define-brick"


def test_long_running_tools_use_simulation_timeout() -> None:
    from mcp_server.server import _timeout_for_risk

    assert _timeout_for_risk(
        "long-running",
        request_timeout=120,
        simulation_timeout=3600,
    ) == 3600
    assert _timeout_for_risk(
        "write",
        request_timeout=120,
        simulation_timeout=3600,
    ) == 120


def test_session_risk_uses_dedicated_budget() -> None:
    from mcp_server.server import _timeout_for_risk

    common = dict(request_timeout=120, simulation_timeout=1200)
    assert _timeout_for_risk("session", session_timeout=300, **common) == 300
    assert (
        _timeout_for_risk("process-control", session_timeout=300, **common)
        == 300
    )
    # 未提供 session_timeout 时向后兼容旧调用形态，回退普通请求预算
    assert _timeout_for_risk("session", **common) == 120


class TestGovernanceRejection:

    GOVERNED = {"run-experiment", "wait-simulation"}

    def test_within_budget_passes(self) -> None:
        from mcp_server.server import _governance_rejection

        for requested in (None, 0, 300, 1139, 1140):
            args = {} if requested is None else {"timeout_seconds": requested}
            assert (
                _governance_rejection(
                    self.GOVERNED, "run-experiment", args, effective_timeout=1200
                )
                is None
            )

    def test_over_budget_rejected(self) -> None:
        from mcp_server.server import _governance_rejection

        result = _governance_rejection(
            self.GOVERNED,
            "wait-simulation",
            {"timeout_seconds": 1141},
            effective_timeout=1200,
        )
        assert result is not None
        assert result["status"] == "error"
        assert result["error_type"] == "invalid_arguments"
        assert result["context"]["requested_seconds"] == 1141
        assert result["context"]["allowed_wait_budget_seconds"] == 1140
        assert "runtime.simulation_timeout" in result["message"]

    def test_non_governed_tool_ignored(self) -> None:
        from mcp_server.server import _governance_rejection

        assert (
            _governance_rejection(
                set(),
                "run-experiment",
                {"timeout_seconds": 99999},
                effective_timeout=1200,
            )
            is None
        )


def test_governed_tools_derived_from_descriptions() -> None:
    from mcp_server.server import _governed_long_running_tools

    descriptions = [
        {
            "name": "run-experiment",
            "risk": "long-running",
            "input_schema": {
                "type": "object",
                "properties": {"timeout_seconds": {"type": "integer"}},
            },
        },
        {
            "name": "quick-sweep",
            "risk": "long-running",
            "input_schema": {
                "type": "object",
                "properties": {"target_freq_ghz": {"type": "number"}},
            },
        },
        {
            "name": "define-brick",
            "risk": "write",
            "input_schema": {
                "type": "object",
                "properties": {"timeout_seconds": {"type": "integer"}},
            },
        },
    ]
    assert _governed_long_running_tools(descriptions) == {"run-experiment"}


def test_config_defaults_match_frozen_plan() -> None:
    from mcp_server.config import MCPConfig

    config = MCPConfig()
    assert config.request_timeout == 120
    assert config.session_timeout == 300
    assert config.long_run_threshold_seconds == 600
    assert config.simulation_timeout == 1200


@pytest.fixture()
def _reset_proxy_singleton():
    from mcp_server.proxy import CSTWorkerProxy

    previous = CSTWorkerProxy._instance
    CSTWorkerProxy._instance = None
    try:
        yield
    finally:
        CSTWorkerProxy._instance = previous


def test_create_mcp_server_does_not_spawn_worker(_reset_proxy_singleton):
    """懒加载：create_mcp_server 本身不得拉起 worker 进程。"""
    from mcp_server.proxy import CSTWorkerProxy
    from mcp_server.server import create_mcp_server

    create_mcp_server()
    assert CSTWorkerProxy._instance is None


def test_list_tools_surfaces_structured_worker_failure(
    _reset_proxy_singleton, monkeypatch
):
    """worker 不可用时 tools/list 必须抛带修复指引的 McpError（A 方案）。"""
    import asyncio

    from mcp.shared.exceptions import McpError
    from mcp.types import ListToolsRequest

    from mcp_server.config import MCPConfig
    from mcp_server.proxy import CSTTransportError
    from mcp_server.server import create_mcp_server

    class UnavailableProxy:
        def describe_tools(self):
            raise CSTTransportError(
                "找不到 Python 3.9 worker 解释器",
                code="worker_python_not_found",
                context={"worker_probe_candidates": ["D:/cst39/python.exe"]},
            )

    config = MCPConfig(worker_probe_candidates=["D:/cst39/python.exe"])
    monkeypatch.setattr(
        "mcp_server.server.get_config", lambda: config
    )
    monkeypatch.setattr(
        "mcp_server.server.get_proxy", lambda: UnavailableProxy()
    )

    server = create_mcp_server()
    handler = server.request_handlers[ListToolsRequest]
    request = ListToolsRequest(method="tools/list")

    with pytest.raises(McpError) as excinfo:
        asyncio.run(handler(request))

    message = str(excinfo.value)
    assert "CST_WORKER_PYTHON" in message
    assert "D:/cst39/python.exe" in message
    assert "INSTALL.md" in message


def test_config_records_probe_candidates():
    """显式配置缺失解释器时返回 None 并保留候选清单供诊断。"""
    from mcp_server.config import _find_worker_python

    worker, tried = _find_worker_python(
        {"runtime": {"worker_python": "D:/missing/python39.exe"}}
    )
    assert worker is None
    assert len(tried) == 1
    assert "missing" in tried[0]
    assert "CST_WORKER_PYTHON/runtime.worker_python" in tried[0]


def test_find_worker_python_falls_back_to_conda_candidates():
    from mcp_server.config import _find_worker_python

    worker, tried = _find_worker_python({})
    # 本机未配置时的行为二选一：命中 cst39 fallback 或返回 None，
    # 但两种情况下候选清单都不得为空（诊断信息必须可用）
    assert isinstance(tried, list)
    if worker is None:
        assert len(tried) >= 1
    else:
        assert worker.is_file()
