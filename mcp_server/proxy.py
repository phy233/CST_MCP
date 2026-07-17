"""MCP Transport Layer — JSON-RPC proxy to CST Worker subprocess.

This module is the MCP layer's own Transport component. It manages the lifecycle
of a Python 3.9 worker subprocess (cst_worker.py) and provides JSON-RPC
communication over stdin/stdout.

Responsibilities (and nothing else):
    - Worker lifecycle (start, restart, shutdown)
    - JSON-RPC serialization / deserialization
    - Timeout management
    - Error detection and reporting

This is a deliberate copy of cst_runtime.core.proxy, adapted for MCP layer
independence. MCP must NOT import from cst_runtime.
"""
from __future__ import annotations

import json
import subprocess
import sys
import queue
import threading
from pathlib import Path
from typing import Any

from .config import get_config


class CSTTransportError(Exception):
    """Raised when the transport layer encounters an error.

    This includes: worker crash, IPC failure, timeout, startup failure.
    Lib/Core errors are passed through as-is in the response dict.
    """
    pass


class CSTWorkerProxy:
    """Singleton proxy that manages a Python 3.9 CST worker subprocess.

    Communication protocol:
        Request  (stdin):  {"module": "lib.xxx", "function": "yyy", "kwargs": {...}}
        Response (stdout): {"status": "success", ...} or {"status": "error", ...}
    """
    _instance: CSTWorkerProxy | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self.response_queue: queue.Queue = queue.Queue()
        self.reader_thread: threading.Thread | None = None
        self._start_worker()

    @classmethod
    def get_instance(cls) -> CSTWorkerProxy:
        with cls._lock:
            if cls._instance is None:
                cls._instance = CSTWorkerProxy()
            return cls._instance

    def _find_worker_script(self) -> Path:
        """Locate cst_worker.py using relative path from project root."""
        config = get_config()
        worker = config.worker_script
        if not worker.exists():
            raise CSTTransportError(
                f"Worker script not found: {worker}\n"
                f"Expected at: {worker.resolve()}"
            )
        return worker

    def _start_worker(self) -> None:
        """Launch the CST worker subprocess in conda env 'cst39'."""
        worker_script = self._find_worker_script()

        # conda is a .bat on Windows, requires shell=True
        cmd_str = f'conda run -n cst39 --no-capture-output python "{worker_script}"'

        self.process = subprocess.Popen(
            cmd_str,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # line buffered
            shell=True  # Required on Windows to resolve 'conda' command
        )

        self.reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader_thread.start()

        # Wait for ready signal
        try:
            ready_resp = self.response_queue.get(timeout=15)
            if ready_resp.get("status") != "ready":
                raise CSTTransportError(f"Worker failed to start: {ready_resp}")
        except queue.Empty:
            raise CSTTransportError(
                "Timeout waiting for cst_worker.py to initialize. "
                "Ensure conda env 'cst39' exists."
            )

    def _read_stdout(self) -> None:
        """Background thread: read JSON lines from worker stdout."""
        try:
            if self.process and self.process.stdout:
                for line in self.process.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        resp = json.loads(line)
                        self.response_queue.put(resp)
                    except json.JSONDecodeError:
                        # Non-JSON output from CST engine, forward to stderr
                        print(f"[CST Worker] {line}", file=sys.stderr)
        except Exception:
            pass

    def call(
        self,
        module_name: str,
        func_name: str,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a request to the worker and wait for a response.

        Args:
            module_name: Target module (e.g. "lib.session")
            func_name: Target function name
            timeout: Response timeout in seconds. None = use config default.
            **kwargs: Arguments passed to the target function.

        Returns:
            Response dict from the worker.

        Raises:
            CSTTransportError: On IPC failure, timeout, or worker crash.
        """
        if self.process is None or self.process.poll() is not None:
            # Restart if dead
            self._start_worker()

        if timeout is None:
            timeout = get_config().default_timeout

        req = {
            "module": module_name,
            "function": func_name,
            "kwargs": kwargs,
        }

        try:
            self.process.stdin.write(json.dumps(req) + "\n")
            self.process.stdin.flush()

            resp = self.response_queue.get(timeout=timeout)

            # Check for worker-side errors and raise
            if resp.get("status") == "error":
                error_type = resp.get("error_type", "unknown")
                message = resp.get("message", "Unknown error from worker")
                raise CSTTransportError(
                    f"[{error_type}] {message}"
                )

            return resp

        except queue.Empty:
            raise CSTTransportError(
                f"Worker did not respond within {timeout}s. "
                f"Call: {module_name}.{func_name}"
            )
        except CSTTransportError:
            raise
        except Exception as e:
            raise CSTTransportError(f"IPC error: {e}") from e

    def shutdown(self) -> None:
        """Gracefully shut down the worker subprocess."""
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(json.dumps({"action": "shutdown"}) + "\n")
                self.process.stdin.flush()
                self.process.wait(timeout=3)
            except Exception:
                self.process.kill()


def call_cst(module_name: str, func_name: str, **kwargs: Any) -> dict[str, Any]:
    """Convenience function: send a request to the CST worker.

    Args:
        module_name: Target module (e.g. "lib.session")
        func_name: Target function name
        **kwargs: Arguments passed to the target function.

    Returns:
        Response dict from the worker.

    Raises:
        CSTTransportError: On transport-level errors.
    """
    proxy = CSTWorkerProxy.get_instance()
    return proxy.call(module_name, func_name, **kwargs)
