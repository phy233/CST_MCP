"""MCP 与 Python 3.9 cst_runtime worker 之间的 JSON 行传输。"""
from __future__ import annotations

import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from .config import MCPConfig, get_config


# ── 阶段信标读端（与 cst_runtime.core.phase_beacon 的双端契约） ──
# 两端必须保持同一路径公式：abs+resolve+casefold 归一化的 project_path
# 的 sha1 前 12 位；任一端修改必须同步另一端。此模块禁止 import
# cst_runtime（架构守卫见 test_mcp_layer_does_not_import_runtime）。
_BEACON_FRESHNESS_SECONDS = 30.0
_GRACE_PHASES = frozenset({"postflight", "closing"})
# L2 兜底触发的优雅收尾窗口（秒）
_DEFAULT_GRACE_SECONDS = 180.0


def _beacon_path_for(project_path: str | None) -> Path | None:
    if not project_path:
        return None
    try:
        normalized = Path(project_path).expanduser().resolve()
    except OSError:
        return None
    key = hashlib.sha1(str(normalized).casefold().encode("utf-8")).hexdigest()[:12]
    tmp_dir = Path.cwd() / ".cst_runtime" / "tmp"
    return tmp_dir / f"phase-{key}.json"


def _phase_allows_grace(project_path: str | None) -> bool:
    """信标存在、新鲜且处于收尾阶段时允许一次优雅宽限。"""
    target = _beacon_path_for(project_path)
    if target is None:
        return False
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        age = time.time() - float(data.get("updated_at"))
    except (OSError, ValueError, TypeError):
        return False
    if age < 0 or age > _BEACON_FRESHNESS_SECONDS:
        return False
    return str(data.get("phase")) in _GRACE_PHASES


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

        error_data = record_dict.get("error")
        if error_data and isinstance(error_data, dict) and not record_dict.get("error_payload_ref"):
            raw_error = json.dumps(error_data, ensure_ascii=False).encode("utf-8")
            if len(raw_error) > 16384:
                import hashlib
                error_sha = hashlib.sha256(raw_error).hexdigest()
                payload_dir = root / "payloads"
                payload_dir.mkdir(parents=True, exist_ok=True)
                error_file = payload_dir / f"{error_sha}.json"
                if not error_file.exists():
                    error_file.write_bytes(raw_error)
                record_dict["error_payload_ref"] = {
                    "storage_path": str(error_file),
                    "size_bytes": len(raw_error),
                    "sha256": error_sha,
                    "is_external": True,
                }
                record_dict["error"] = {
                    "_payload_ref": record_dict["error_payload_ref"],
                    "_preview": f"<External payload stored at {error_file.name}, size {len(raw_error)} bytes>",
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
        """返回进程内唯一代理实例（首次调用触发 worker 启动）。"""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def shutdown_if_created(cls) -> None:
        """已创建代理实例则优雅关闭；从未创建时不做任何事。

        服务退出清理使用本方法，避免懒加载语义下意外拉起 worker。
        """
        with cls._instance_lock:
            if cls._instance is None:
                return
            cls._instance.shutdown()

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
        if worker_python is None:
            candidates = "\n".join(
                f"  - {item}" for item in self.config.worker_probe_candidates
            ) or "  - (未记录任何候选路径)"
            raise CSTTransportError(
                "找不到 Python 3.9 worker 解释器；请设置 CST_WORKER_PYTHON"
                "或在 .cst_config.json 的 runtime.worker_python 配置实际路径。\n"
                f"已探测的候选：\n{candidates}",
                code="worker_python_not_found",
                context={
                    "worker_probe_candidates": list(
                        self.config.worker_probe_candidates
                    ),
                },
            )
        if not worker_python.is_file():
            raise CSTTransportError(
                "找不到 Python 3.9 worker 解释器："
                f"{worker_python}；请设置 CST_WORKER_PYTHON",
                code="worker_python_not_found",
                context={
                    "worker_python": str(worker_python),
                    "worker_probe_candidates": list(
                        self.config.worker_probe_candidates
                    ),
                },
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
        grace_seconds: float | None = None,
        grace_class: str = "abnormal",
        grace_project_path: str | None = None,
        **payload: Any,
    ) -> dict[str, Any]:
        """串行发送一个请求并校验响应 ID。

        ``grace_seconds`` 非 None 时启用 L2 优雅收尾窗口：请求超时后，
        若阶段信标显示 worker 正在 postflight/closing，则在该窗口内
        继续等待迟到响应，命中则视为正常完成；逾期才终止 worker。
        其余情形保持原语义（超时即终止，防止迟到响应污染后续请求）。
        """
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
                if grace_seconds and grace_seconds > 0:
                    collected = self._collect_grace_response(
                        request_id,
                        grace_seconds=grace_seconds,
                        grace_project_path=grace_project_path,
                    )
                    if collected is not None:
                        return collected
                # 超时请求的迟到响应会污染后续请求，因此必须重启 worker。
                self._terminate_worker()
                raise CSTTransportError(
                    f"worker 调用超时: {action}",
                    code="worker_request_timeout",
                    context={
                        "action": action,
                        "timeout_class": grace_class,
                        "project_path": grace_project_path,
                        "grace_used": bool(grace_seconds),
                        "grace_seconds": grace_seconds,
                    },
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

    def _collect_grace_response(
        self,
        request_id: str,
        *,
        grace_seconds: float,
        grace_project_path: str | None,
    ) -> dict[str, Any] | None:
        """宽限窗口内收集迟到的响应；命中返回原响应，否则 None。

        仅当阶段信标显示 worker 正在收尾（postflight/closing）时才等待；
        串行协议保证窗口内队列中的第一条真实响应必然属于当前请求。
        """
        if not _phase_allows_grace(grace_project_path):
            return None
        deadline = time.monotonic() + float(grace_seconds)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                response = self._responses.get(timeout=min(remaining, 0.5))
            except queue.Empty:
                continue
            if response.get("_transport_error"):
                # worker 在宽限期内退出：宽限失效，按超时路径终止清理
                return None
            if response.get("id") != request_id:
                # 串行协议下不应发生；防御性处理：丢弃未知迟到响应
                continue
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
        timeout_class: str = "abnormal",
    ) -> dict[str, Any]:
        """调用一个 runtime 白名单工具，并记录完整 MCP 交互生命周期。

        ``timeout_class``（"expected_simulation" | "abnormal"）决定
        L2 兜底行为：长任务超时先尝试信标宽限；两类终止都会写入
        journal 终态。runtime 返回 ``long_run_relinquish``（L1 让出）
        时记录 ``relinquished`` 终态并终止 worker 释放算力。
        """
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
        grace_seconds = (
            _DEFAULT_GRACE_SECONDS
            if timeout_class == "expected_simulation"
            else None
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
            "timeout_class": timeout_class,
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
                grace_seconds=grace_seconds,
                grace_class=timeout_class,
                grace_project_path=str(project_path) if project_path else None,
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
                before_id = response.get("before_snapshot_id") or response.get("context", {}).get("before_snapshot_id")
                if before_id:
                    record["before_snapshot_id"] = str(before_id)
                b_sha = response.get("before_snapshot_sha256") or response.get("context", {}).get("before_snapshot_sha256")
                if b_sha:
                    record["before_snapshot_sha256"] = str(b_sha)
                after_id = response.get("after_snapshot_id") or response.get("context", {}).get("after_snapshot_id")
                if after_id:
                    record["after_snapshot_id"] = str(after_id)
                a_sha = response.get("after_snapshot_sha256") or response.get("context", {}).get("after_snapshot_sha256")
                if a_sha:
                    record["after_snapshot_sha256"] = str(a_sha)

                if response.get("error_type") == "long_run_relinquish":
                    # L1 让出：业务信号已完整送达 agent，worker 无继续
                    # 存在的价值——立即回收进程释放算力（前台让出场景）。
                    record["state"] = "relinquished"
                    record["result"] = response
                    _log_mcp_interaction(record.get("workspace"), record)
                    self._terminate_worker()
                elif response.get("status") == "error" or response.get("ok") is False:
                    record["state"] = "failed"
                    record["error"] = response
                    _log_mcp_interaction(record.get("workspace"), record)
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
                if exc.code == "worker_request_timeout":
                    # L2 兜底终止（宽限后或无宽限）：journal 必须留下
                    # 明确的 terminated 终态与超时分类，供恢复时判读；
                    # call_tool 作为生命周期收口，再次确保 worker 被回收
                    # （幂等：request 内部已终止时此调用无副作用）。
                    self._terminate_worker()
                    record["state"] = "terminated"
                    record["timeout_class"] = (
                        exc.context.get("timeout_class", timeout_class)
                        if isinstance(exc.context, dict)
                        else timeout_class
                    )
                else:
                    record["state"] = (
                        "timeout" if exc.code == "worker_request_timeout" else "transport_error"
                    )
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
