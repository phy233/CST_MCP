"""MCP 与 Python 3.9 cst_runtime worker 之间的 JSON 行传输。"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Any

from .config import MCPConfig, get_config


class CSTTransportError(RuntimeError):
    """worker 启动、通信或超时时抛出的错误。"""


class CSTWorkerProxy:
    """串行管理一个 cst_runtime worker。"""

    _instance: "CSTWorkerProxy | None" = None
    _instance_lock = threading.Lock()

    def __init__(self, config: MCPConfig | None = None) -> None:
        self.config = config or get_config()
        self.process: subprocess.Popen[str] | None = None
        self._responses: queue.Queue[dict[str, Any]] = queue.Queue()
        self._call_lock = threading.RLock()
        self._reader_thread: threading.Thread | None = None
        self._stderr_thread: threading.Thread | None = None
        self._start_worker()

    @classmethod
    def get_instance(cls) -> "CSTWorkerProxy":
        """返回进程内唯一代理实例。"""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _worker_environment(self) -> dict[str, str]:
        environment = dict(os.environ)
        if self.config.runtime_source is not None:
            current = environment.get("PYTHONPATH", "")
            parts = [str(self.config.runtime_source)]
            if current:
                parts.append(current)
            environment["PYTHONPATH"] = os.pathsep.join(parts)
        if self.config.cst_python_libraries:
            environment["CST_PYTHON_LIBS"] = self.config.cst_python_libraries
        if self.config.config_path is not None:
            environment["CST_MCP_CONFIG"] = str(self.config.config_path)
        return environment

    def _start_worker(self) -> None:
        worker_python = self.config.worker_python
        if not worker_python.is_file():
            raise CSTTransportError(
                "找不到 Python 3.9 worker 解释器："
                f"{worker_python}；请设置 CST_WORKER_PYTHON"
            )
        self._responses = queue.Queue()
        self.process = subprocess.Popen(
            [str(worker_python), "-m", "cst_runtime.worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=False,
            env=self._worker_environment(),
        )
        self._reader_thread = threading.Thread(
            target=self._read_stdout,
            args=(self.process, self._responses),
            name="cst-worker-stdout",
            daemon=True,
        )
        self._stderr_thread = threading.Thread(
            target=self._read_stderr,
            args=(self.process,),
            name="cst-worker-stderr",
            daemon=True,
        )
        self._reader_thread.start()
        self._stderr_thread.start()
        try:
            ready = self._responses.get(timeout=self.config.startup_timeout)
        except queue.Empty as exc:
            self._terminate_worker()
            raise CSTTransportError("等待 cst_runtime worker 就绪超时") from exc
        if ready.get("status") != "ready":
            self._terminate_worker()
            raise CSTTransportError(f"worker 启动失败: {ready}")

    def _read_stdout(
        self,
        process: subprocess.Popen[str],
        responses: queue.Queue[dict[str, Any]],
    ) -> None:
        if process.stdout is None:
            return
        try:
            for raw_line in process.stdout:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    responses.put(json.loads(line))
                except json.JSONDecodeError:
                    print(f"[CST worker 非 JSON 输出] {line}", file=sys.stderr)
        finally:
            responses.put(
                {
                    "_transport_error": "worker_exited",
                    "returncode": process.poll(),
                }
            )

    def _read_stderr(self, process: subprocess.Popen[str]) -> None:
        if process.stderr is None:
            return
        for raw_line in process.stderr:
            line = raw_line.rstrip()
            if line:
                print(f"[CST worker] {line}", file=sys.stderr)

    def _ensure_worker(self) -> None:
        if self.process is None or self.process.poll() is not None:
            self._start_worker()

    def request(
        self,
        action: str,
        *,
        timeout: int | None = None,
        **payload: Any,
    ) -> dict[str, Any]:
        """串行发送一个请求并校验响应 ID。"""
        with self._call_lock:
            self._ensure_worker()
            request_id = uuid.uuid4().hex
            request = {"id": request_id, "action": action, **payload}
            process = self.process
            if process is None or process.stdin is None:
                raise CSTTransportError("worker 标准输入不可用")
            try:
                process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
                process.stdin.flush()
                response = self._responses.get(
                    timeout=timeout or self.config.request_timeout
                )
            except queue.Empty as exc:
                # 超时请求的迟到响应会污染后续请求，因此必须重启 worker。
                self._terminate_worker()
                raise CSTTransportError(
                    f"worker 调用超时: {action}"
                ) from exc
            except Exception as exc:
                raise CSTTransportError(f"worker IPC 失败: {exc}") from exc
            if response.get("_transport_error"):
                self._terminate_worker()
                raise CSTTransportError(
                    "cst_runtime worker 在请求完成前退出"
                )
            if response.get("id") != request_id:
                raise CSTTransportError(
                    f"worker 响应 ID 不匹配: {response.get('id')} != {request_id}"
                )
            return response

    def describe_tools(self) -> list[dict[str, Any]]:
        """读取 runtime 拥有的工具清单。"""
        response = self.request("describe_tools")
        if response.get("status") == "error":
            raise CSTTransportError(response.get("message", "工具清单读取失败"))
        return list(response.get("tools", []))

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """调用一个 runtime 白名单工具。"""
        return self.request(
            "call_tool",
            name=name,
            arguments=arguments,
            timeout=timeout,
        )

    def shutdown(self) -> None:
        """优雅关闭 worker。"""
        with self._call_lock:
            if self.process is None or self.process.poll() is not None:
                return
            try:
                self.request("shutdown", timeout=3)
                self.process.wait(timeout=3)
            except Exception:
                self._terminate_worker()
            finally:
                self.process = None

    def _terminate_worker(self) -> None:
        process = self.process
        if process is not None and process.poll() is None:
            process.kill()
            try:
                process.wait(timeout=3)
            except Exception:
                pass
        self.process = None


def get_proxy() -> CSTWorkerProxy:
    """返回共享 worker 代理。"""
    return CSTWorkerProxy.get_instance()
