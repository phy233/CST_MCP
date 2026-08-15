"""MCP 到 Runtime Worker 的协议测试。"""
from __future__ import annotations

import io
import json
import queue
import subprocess
import sys
import threading
from types import SimpleNamespace

import pytest


@pytest.mark.worker_proxy
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


@pytest.mark.worker_proxy
def test_worker_rejects_unknown_operation() -> None:
    from mcp_server.proxy import CSTWorkerProxy

    proxy = CSTWorkerProxy()
    try:
        result = proxy.call_tool("not-a-real-tool", {})
        assert result["status"] == "error"
        assert result["error_type"] == "unknown_tool"
    finally:
        proxy.shutdown()


def test_worker_emits_non_gbk_character_as_ascii_json(monkeypatch) -> None:
    """响应包含 GBK 无法编码的字符时，Worker 应使用 JSON 转义安全输出。"""
    from cst_runtime.worker import _emit_json_line

    raw_output = io.BytesIO()
    gbk_stdout = io.TextIOWrapper(raw_output, encoding="gbk", errors="strict")
    monkeypatch.setattr(sys, "stdout", gbk_stdout)

    _emit_json_line({"message": "\ue045"})
    gbk_stdout.flush()

    encoded_line = raw_output.getvalue().decode("gbk")
    assert "\\ue045" in encoded_line
    assert json.loads(encoded_line) == {"message": "\ue045"}


@pytest.mark.worker_proxy
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


@pytest.mark.worker_proxy
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


def test_worker_internal_error_hides_traceback_from_response(monkeypatch, capsys) -> None:
    import cst_runtime.api
    from cst_runtime.worker import handle_request

    def fail(_name, _arguments):
        raise RuntimeError("worker exploded")

    monkeypatch.setattr(cst_runtime.api, "invoke_tool", fail)

    result = handle_request(
        {"id": "request-2", "action": "call_tool", "name": "demo", "arguments": {}}
    )

    assert result["status"] == "error"
    assert result["error_type"] == "worker_error"
    assert result["error"]["phase"] == "worker"
    assert "traceback" not in result
    assert "Traceback" in capsys.readouterr().err


def test_proxy_does_not_misclassify_serialization_error() -> None:
    from mcp_server.proxy import CSTWorkerProxy

    proxy = object.__new__(CSTWorkerProxy)
    proxy._call_lock = threading.RLock()
    proxy._ensure_worker = lambda: None

    with pytest.raises(TypeError):
        proxy.request("call_tool", arguments={"invalid": object()})


def test_proxy_wraps_worker_process_start_failure(monkeypatch, tmp_path) -> None:
    from mcp_server import proxy as proxy_module

    worker_python = tmp_path / "python.exe"
    worker_python.write_text("placeholder", encoding="utf-8")
    proxy = object.__new__(proxy_module.CSTWorkerProxy)
    proxy.config = SimpleNamespace(worker_python=worker_python)
    proxy._responses = queue.Queue()
    proxy._worker_environment = lambda: {}

    def fail_to_start(*_args, **_kwargs):
        raise OSError("launch denied")

    monkeypatch.setattr(
        proxy_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="3.9\n"),
    )
    monkeypatch.setattr(proxy_module.subprocess, "Popen", fail_to_start)

    with pytest.raises(proxy_module.CSTTransportError) as exc_info:
        proxy._start_worker()

    assert exc_info.value.code == "worker_process_start_failed"
    assert exc_info.value.context["worker_python"] == str(worker_python)


def test_proxy_wraps_worker_version_probe_failure(monkeypatch, tmp_path) -> None:
    from mcp_server import proxy as proxy_module

    worker_python = tmp_path / "python.exe"
    worker_python.write_text("placeholder", encoding="utf-8")
    proxy = object.__new__(proxy_module.CSTWorkerProxy)
    proxy.config = SimpleNamespace(worker_python=worker_python)

    def fail_to_probe(*_args, **_kwargs):
        raise OSError("probe denied")

    monkeypatch.setattr(proxy_module.subprocess, "run", fail_to_probe)

    with pytest.raises(proxy_module.CSTTransportError) as exc_info:
        proxy._start_worker()

    assert exc_info.value.code == "worker_version_probe_failed"
    assert exc_info.value.context["worker_python"] == str(worker_python)


def test_proxy_wraps_worker_version_probe_timeout(monkeypatch, tmp_path) -> None:
    from mcp_server import proxy as proxy_module

    worker_python = tmp_path / "python.exe"
    worker_python.write_text("placeholder", encoding="utf-8")
    proxy = object.__new__(proxy_module.CSTWorkerProxy)
    proxy.config = SimpleNamespace(worker_python=worker_python)

    def time_out(*_args, **_kwargs):
        raise subprocess.TimeoutExpired([str(worker_python), "-c", "..."], 10)

    monkeypatch.setattr(proxy_module.subprocess, "run", time_out)

    with pytest.raises(proxy_module.CSTTransportError) as exc_info:
        proxy._start_worker()

    assert exc_info.value.code == "worker_version_probe_timeout"
    assert exc_info.value.context["worker_python"] == str(worker_python)


def test_proxy_rejects_non_python_39_worker(monkeypatch, tmp_path) -> None:
    from mcp_server import proxy as proxy_module

    worker_python = tmp_path / "python.exe"
    worker_python.write_text("placeholder", encoding="utf-8")
    proxy = object.__new__(proxy_module.CSTWorkerProxy)
    proxy.config = SimpleNamespace(worker_python=worker_python)
    monkeypatch.setattr(
        proxy_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="3.12\n"),
    )

    with pytest.raises(proxy_module.CSTTransportError) as exc_info:
        proxy._start_worker()

    assert exc_info.value.code == "worker_python_version_mismatch"
    assert exc_info.value.context == {
        "worker_python": str(worker_python),
        "worker_version": "3.12",
    }
