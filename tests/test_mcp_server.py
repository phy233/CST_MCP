"""MCP 纯适配层测试。"""
from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_config_has_separate_worker_runtime() -> None:
    from mcp_server.config import get_config

    config = get_config()
    assert config.server_name == "cst-runtime"
    assert config.worker_python.name.lower() == "python.exe"
    assert "IPC" in config.instructions


def test_proxy_reads_runtime_owned_manifest() -> None:
    from mcp_server.proxy import CSTWorkerProxy

    proxy = CSTWorkerProxy()
    try:
        tools = proxy.describe_tools()
        names = {tool["name"] for tool in tools}
        assert len(tools) >= 100
        assert {"build-array", "quick-sweep", "cross-process-sweep"} <= names
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
