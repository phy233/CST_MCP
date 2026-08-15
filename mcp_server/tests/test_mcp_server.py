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
        assert {"build-array", "quick-sweep", "cross-process-sweep"} <= names
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
        def call_tool(self, name, arguments, *, timeout):
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
