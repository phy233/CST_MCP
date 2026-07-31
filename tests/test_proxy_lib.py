"""MCP 到 runtime worker 的协议测试。"""
from __future__ import annotations


def test_worker_ping_and_request_id() -> None:
    from mcp_server.proxy import CSTWorkerProxy

    proxy = CSTWorkerProxy()
    try:
        result = proxy.request("ping")
        assert result["status"] == "pong"
        assert isinstance(result["id"], str)
        assert result["id"]
    finally:
        proxy.shutdown()


def test_worker_rejects_unknown_operation() -> None:
    from mcp_server.proxy import CSTWorkerProxy

    proxy = CSTWorkerProxy()
    try:
        result = proxy.call_tool("not-a-real-tool", {})
        assert result["status"] == "error"
        assert result["error_type"] == "unknown_tool"
    finally:
        proxy.shutdown()


def test_proxy_restarts_after_worker_exit() -> None:
    from mcp_server.proxy import CSTWorkerProxy

    proxy = CSTWorkerProxy()
    try:
        assert proxy.process is not None
        old_pid = proxy.process.pid
        proxy.process.kill()
        proxy.process.wait(timeout=3)
        result = proxy.request("ping")
        assert result["status"] == "pong"
        assert proxy.process is not None
        assert proxy.process.pid != old_pid
    finally:
        proxy.shutdown()


def test_worker_rejects_arbitrary_module_dispatch() -> None:
    from cst_runtime.worker import handle_request

    result = handle_request(
        {
            "id": "request-1",
            "action": "import_module",
            "module": "os",
            "function": "system",
        }
    )
    assert result["id"] == "request-1"
    assert result["status"] == "error"
    assert result["error_type"] == "unsupported_action"


def test_worker_rejects_arbitrary_module_dispatch() -> None:
    from mcp_server.proxy import CSTWorkerProxy

    proxy = CSTWorkerProxy()
    try:
        result = proxy.request(
            "call",
            module="os",
            function="system",
            arguments={"command": "echo forbidden"},
        )
        assert result["status"] == "error"
        assert result["error_type"] == "unsupported_action"
    finally:
        proxy.shutdown()
