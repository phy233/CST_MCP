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
import time
import os
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
        if os.environ.get("CST_RUNTIME_PROFILE") == "1":
            msg = "[Profile] Proxy Created"
            print(msg, file=sys.stderr)
            try:
                log_path = Path(__file__).resolve().parent.parent / "cst_profile.log"
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass
        self.process: subprocess.Popen | None = None
        self.response_queue: queue.Queue = queue.Queue()
        self.reader_thread: threading.Thread | None = None
        self._start_worker()

    @classmethod
    def get_instance(cls) -> CSTWorkerProxy:
        with cls._lock:
            if cls._instance is None:
                cls._instance = CSTWorkerProxy()
            else:
                if os.environ.get("CST_RUNTIME_PROFILE") == "1":
                    msg = "[Profile] Proxy Reused"
                    print(msg, file=sys.stderr)
                    try:
                        log_path = Path(__file__).resolve().parent.parent / "cst_profile.log"
                        with open(log_path, "a", encoding="utf-8") as f:
                            f.write(msg + "\n")
                    except Exception:
                        pass
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
        if os.environ.get("CST_RUNTIME_PROFILE") == "1" and self.process is not None:
            msg = "[Profile] Worker Restarted"
            print(msg, file=sys.stderr)
            try:
                log_path = Path(__file__).resolve().parent.parent / "cst_profile.log"
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass
            
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

        is_profile = os.environ.get("CST_RUNTIME_PROFILE") == "1"
        t_proxy_send = 0
        if is_profile:
            t_proxy_send = time.perf_counter()

        if timeout is None:
            timeout = get_config().default_timeout

        req = {
            "module": module_name,
            "function": func_name,
            "kwargs": kwargs,
        }
        if is_profile:
            req["__profile__"] = True
            
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

            if is_profile:
                t_proxy_receive = time.perf_counter()
                resp["__profile_proxy__"] = {
                    "t_proxy_send": t_proxy_send,
                    "t_proxy_receive": t_proxy_receive
                }
                
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
    """Convenience function: send a request to the CST worker."""
    is_profile = os.environ.get("CST_RUNTIME_PROFILE") == "1"
    t_tool_enter = 0
    if is_profile:
        import time
        t_tool_enter = time.perf_counter()
        
    proxy = CSTWorkerProxy.get_instance()
    resp = proxy.call(module_name, func_name, **kwargs)
    
    if is_profile:
        t_tool_exit = time.perf_counter()
        
        prof = resp.get("__profile__", {})
        prof_p = resp.get("__profile_proxy__", {})
        
        t_proxy_send = prof_p.get("t_proxy_send", 0)
        t_worker_receive = prof.get("t_worker_receive", 0)
        t_lib_enter = prof.get("t_lib_enter", 0)
        t_com_begin = prof.get("t_com_begin", 0)
        t_com_end = prof.get("t_com_end", 0)
        t_worker_return = prof.get("t_worker_return", 0)
        t_proxy_receive = prof_p.get("t_proxy_receive", 0)
        
        total = t_tool_exit - t_tool_enter
        mcp_to_proxy = t_proxy_send - t_tool_enter
        proxy_to_worker = t_worker_receive - t_proxy_send
        worker_dispatch = t_lib_enter - t_worker_receive
        
        # com logic
        if t_com_begin > 0 and t_com_end > 0:
            lib_core_pre = t_com_begin - t_lib_enter
            com_exec = t_com_end - t_com_begin
            lib_core_post = t_worker_return - t_com_end
            lib_core = lib_core_pre + lib_core_post
        else:
            com_exec = 0
            lib_core = t_worker_return - t_lib_enter
            
        worker_return = t_proxy_receive - t_worker_return
        proxy_return = t_tool_exit - t_proxy_receive
        
        out_lines = [
            "=" * 50,
            f"Tool: {module_name}.{func_name}",
            f"Total: {total:.2f} s",
            f"MCP -> Proxy:\n{mcp_to_proxy:.2f} s",
            f"Proxy -> Worker:\n{proxy_to_worker:.2f} s",
            f"Worker Dispatch:\n{worker_dispatch:.2f} s",
            f"Lib/Core:\n{lib_core:.2f} s",
            f"COM Execute:\n{com_exec:.2f} s",
            f"Worker Return:\n{worker_return:.2f} s",
            f"Proxy Return:\n{proxy_return:.2f} s",
            "=" * 50
        ]
        
        # Print to stderr
        for line in out_lines:
            print(line, file=sys.stderr)
            
        # Also write to a file in project root for easy viewing
        try:
            log_path = Path(__file__).resolve().parent.parent / "cst_profile.log"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("\n".join(out_lines) + "\n")
        except Exception:
            pass
        
    return resp
