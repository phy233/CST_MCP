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

    def __init__(
        self,
        message: str,
        *,
        code: str = "transport_error",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.context = dict(context or {})

    def to_response(self, **context: Any) -> dict[str, Any]:
        """Return the same public envelope shape used by runtime errors."""
        merged_context = {**self.context, **context}
        return {
            "ok": False,
            "status": "error",
            "error_type": "transport_error",
            "message": str(self),
            "error": {
                "type": "transport_error",
                "code": self.code,
                "message": str(self),
                "phase": "transport",
            },
            "context": merged_context,
        }


def _log_mcp_interaction(
    workspace: str | None,
    record_dict: dict[str, Any],
) -> None:
    try:
        ws = Path(workspace).expanduser().resolve() if workspace else None
        if not ws:
            env_ws = os.environ.get("CST_WORKSPACE")
            ws = Path(env_ws).expanduser().resolve() if env_ws else Path.cwd().resolve()

        sid = os.environ.get("CST_SERVER_SESSION_ID") or "default_session"
        root = ws / ".cst_runtime" / "interactions" / sid
        root.mkdir(parents=True, exist_ok=True)

        tool_args = record_dict.get("tool_args")
        if tool_args and isinstance(tool_args, dict) and not record_dict.get("request_payload_ref"):
            raw_b = json.dumps(tool_args, ensure_ascii=False).encode("utf-8")
            if len(raw_b) > 16384:
                import hashlib
                sha = hashlib.sha256(raw_b).hexdigest()
                p_dir = root / "payloads"
                p_dir.mkdir(parents=True, exist_ok=True)
                p_file = p_dir / f"{sha}.json"
                if not p_file.exists():
                    p_file.write_bytes(raw_b)
                record_dict["request_payload_ref"] = {
                    "storage_path": str(p_file),
                    "size_bytes": len(raw_b),
                    "sha256": sha,
                    "is_external": True,
                }
                record_dict["tool_args"] = {
                    "_payload_ref": record_dict["request_payload_ref"],
                    "_preview": f"<External payload stored at {p_file.name}, size {len(raw_b)} bytes>",
                }

        res_data = record_dict.get("result")
        if res_data and isinstance(res_data, dict) and not record_dict.get("response_payload_ref"):
            raw_res = json.dumps(res_data, ensure_ascii=False).encode("utf-8")
            if len(raw_res) > 16384:
                import hashlib
                sha_res = hashlib.sha256(raw_res).hexdigest()
                p_dir = root / "payloads"
                p_dir.mkdir(parents=True, exist_ok=True)
                p_file = p_dir / f"{sha_res}.json"
                if not p_file.exists():
                    p_file.write_bytes(raw_res)
                record_dict["response_payload_ref"] = {
                    "storage_path": str(p_file),
                    "size_bytes": len(raw_res),
                    "sha256": sha_res,
                    "is_external": True,
                }
                record_dict["result"] = {
                    "_payload_ref": record_dict["response_payload_ref"],
                    "_preview": f"<External payload stored at {p_file.name}, size {len(raw_res)} bytes>",
                }

        journal_path = root / "mcp_interactions.jsonl"
        line = json.dumps(record_dict, ensure_ascii=False, default=str)
        with journal_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
    except Exception:
        pass


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
                f"{worker_python}；请设置 CST_WORKER_PYTHON",
                code="worker_python_not_found",
                context={"worker_python": str(worker_python)},
            )
        try:
            version = subprocess.run(
                [str(worker_python), "-c", "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise CSTTransportError(
                f"探测 Python worker 版本超时：{worker_python}",
                code="worker_version_probe_timeout",
                context={"worker_python": str(worker_python)},
            ) from exc
        except OSError as exc:
            raise CSTTransportError(
                f"无法探测 Python worker 版本：{worker_python}：{exc}",
                code="worker_version_probe_failed",
                context={"worker_python": str(worker_python)},
            ) from exc
        worker_version = version.stdout.strip()
        if version.returncode != 0 or worker_version != "3.9":
            raise CSTTransportError(
                "CST worker 必须使用 Python 3.9；"
                f"当前 worker 为 {worker_version or '未知版本'}：{worker_python}。"
                "请在 .cst_config.json 的 runtime.worker_python 中配置 CST 兼容解释器。",
                code="worker_python_version_mismatch",
                context={
                    "worker_python": str(worker_python),
                    "worker_version": worker_version or None,
                },
            )
        self._responses = queue.Queue()
        try:
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
        except OSError as exc:
            raise CSTTransportError(
                f"无法启动 cst_runtime worker: {exc}",
                code="worker_process_start_failed",
                context={"worker_python": str(worker_python)},
            ) from exc
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
            raise CSTTransportError(
                "等待 cst_runtime worker 就绪超时",
                code="worker_startup_timeout",
            ) from exc
        if ready.get("status") != "ready":
            self._terminate_worker()
            raise CSTTransportError(
                f"worker 启动失败: {ready}",
                code="worker_startup_failed",
            )

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
        request_id = uuid.uuid4().hex
        request = {"id": request_id, "action": action, **payload}
        serialized_request = json.dumps(request, ensure_ascii=False)
        with self._call_lock:
            self._ensure_worker()
            process = self.process
            if process is None or process.stdin is None:
                raise CSTTransportError(
                    "worker 标准输入不可用",
                    code="worker_stdin_unavailable",
                    context={"action": action},
                )
            try:
                process.stdin.write(serialized_request + "\n")
                process.stdin.flush()
            except (OSError, ValueError) as exc:
                raise CSTTransportError(
                    f"worker IPC 失败: {exc}",
                    code="worker_ipc_failed",
                    context={"action": action},
                ) from exc
            try:
                response = self._responses.get(
                    timeout=timeout or self.config.request_timeout
                )
            except queue.Empty as exc:
                # 超时请求的迟到响应会污染后续请求，因此必须重启 worker。
                self._terminate_worker()
                raise CSTTransportError(
                    f"worker 调用超时: {action}",
                    code="worker_request_timeout",
                    context={"action": action},
                ) from exc
            if response.get("_transport_error"):
                self._terminate_worker()
                raise CSTTransportError(
                    "cst_runtime worker 在请求完成前退出",
                    code="worker_exited",
                    context={"action": action},
                )
            if response.get("id") != request_id:
                raise CSTTransportError(
                    f"worker 响应 ID 不匹配: {response.get('id')} != {request_id}",
                    code="worker_response_id_mismatch",
                    context={"action": action},
                )
            return response

    def list_tools(self) -> list[dict[str, Any]]:
        """获取由 worker 暴露的工具列表。"""
        resp = self.request("list_tools")
        return list(resp.get("tools", []))

    def describe_tools(self) -> list[dict[str, Any]]:
        """读取 runtime 拥有的工具清单。"""
        response = self.request("describe_tools")
        if response.get("status") == "error":
            raise CSTTransportError(
                response.get("message", "工具清单读取失败"),
                code="tool_manifest_failed",
            )
        return list(response.get("tools", []))

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """调用一个 runtime 白名单工具，并记录完整 MCP 交互生命周期。"""
        import time
        from datetime import datetime, timezone

        interaction_id = uuid.uuid4().hex
        started_at = datetime.now(timezone.utc).astimezone().isoformat()
        start_time = time.monotonic()

        task_id = arguments.get("task_id") or arguments.get("task")
        run_id = arguments.get("run_id") or arguments.get("run")
        workspace = arguments.get("workspace")
        project_path = (
            arguments.get("project_path")
            or arguments.get("fullpath")
            or arguments.get("working_project")
        )

        record: dict[str, Any] = {
            "interaction_id": interaction_id,
            "tool_name": name,
            "tool_args": dict(arguments),
            "task_id": str(task_id) if task_id else None,
            "run_id": str(run_id) if run_id else None,
            "workspace": str(workspace) if workspace else None,
            "project_path": str(project_path) if project_path else None,
            "server_name": self.config.server_name,
            "server_version": "0.1.0",
            "state": "requested",
            "started_at": started_at,
            "result": None,
            "error": None,
            "duration_ms": None,
            "ended_at": None,
            "operation_id": None,
            "before_snapshot_id": None,
            "before_snapshot_sha256": None,
            "after_snapshot_id": None,
            "after_snapshot_sha256": None,
        }
        _log_mcp_interaction(record.get("workspace"), record)
        record["state"] = "running"
        _log_mcp_interaction(record.get("workspace"), record)

        try:
            response = self.request(
                "call_tool",
                interaction_id=interaction_id,
                task_id=str(task_id) if task_id else None,
                run_id=str(run_id) if run_id else None,
                name=name,
                arguments=arguments,
                timeout=timeout,
            )
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            ended_at = datetime.now(timezone.utc).astimezone().isoformat()

            try:
                record["duration_ms"] = duration_ms
                record["ended_at"] = ended_at
                op_id = (
                    response.get("operation_id")
                    or response.get("context", {}).get("operation_id")
                )
                if op_id:
                    record["operation_id"] = str(op_id)
                b_sha = response.get("before_snapshot_sha256") or response.get("context", {}).get("before_snapshot_sha256")
                if b_sha:
                    record["before_snapshot_sha256"] = str(b_sha)
                a_sha = response.get("after_snapshot_sha256") or response.get("context", {}).get("after_snapshot_sha256")
                if a_sha:
                    record["after_snapshot_sha256"] = str(a_sha)

                if response.get("status") == "error" or response.get("ok") is False:
                    record["state"] = "failed"
                    record["error"] = response
                else:
                    record["state"] = "succeeded"
                    record["result"] = response
                _log_mcp_interaction(record.get("workspace"), record)
            except Exception:
                pass

            return response
        except CSTTransportError as exc:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            ended_at = datetime.now(timezone.utc).astimezone().isoformat()
            try:
                record["duration_ms"] = duration_ms
                record["ended_at"] = ended_at
                record["state"] = "timeout" if exc.code == "worker_request_timeout" else "transport_error"
                record["error"] = exc.to_response(tool_name=name)
                _log_mcp_interaction(record.get("workspace"), record)
            except Exception:
                pass
            raise
        except Exception as exc:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            ended_at = datetime.now(timezone.utc).astimezone().isoformat()
            try:
                record["duration_ms"] = duration_ms
                record["ended_at"] = ended_at
                record["state"] = "failed"
                record["error"] = {"error_type": "proxy_exception", "message": str(exc)}
                _log_mcp_interaction(record.get("workspace"), record)
            except Exception:
                pass
            raise

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
