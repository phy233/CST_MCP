"""MCP 纯适配层配置。"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _load_config_file() -> tuple[Path | None, dict[str, Any]]:
    configured = os.environ.get("CST_MCP_CONFIG")
    candidates = [Path(configured)] if configured else [Path.cwd() / ".cst_config.json"]
    for path in candidates:
        try:
            if path.is_file():
                return path.resolve(), json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return None, {}


def _find_worker_python(config: dict[str, Any]) -> Path:
    configured = (
        os.environ.get("CST_WORKER_PYTHON")
        or config.get("runtime", {}).get("worker_python")
    )
    if configured:
        return Path(configured).expanduser().resolve()
    if sys.version_info[:2] == (3, 9):
        return Path(sys.executable).resolve()
    user_home = Path.home()
    candidates = [
        user_home / "miniconda3" / "envs" / "cst39" / "python.exe",
        user_home / "anaconda3" / "envs" / "cst39" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def _find_runtime_source(project_root: Path, config: dict[str, Any]) -> Path | None:
    configured = config.get("runtime", {}).get("source_path")
    if configured:
        path = Path(configured).expanduser().resolve()
        return path if path.is_dir() else None
    candidate = project_root / "skills" / "cst-runtime-cli" / "scripts"
    return candidate if candidate.is_dir() else None


@dataclass
class MCPConfig:
    """MCP 服务和 worker 传输配置。

    超时预算分三层（均为秒，可在 ``.cst_config.json`` 的 ``runtime.*`` 下覆盖）：

    - ``long_run_threshold_seconds``：长任务分界（权威判定在 runtime 侧，
      按 solver 实际运行时长计算）；MCP 层仅透传/文档引用；
    - ``simulation_timeout``：transport 硬兜底，必须大于长任务分界；
      到点对 long-running 工具执行 detach 并终止 worker；
    - ``session_timeout``：cst-session-open/close 等 session 或
      process-control 类工具的预算（冷启动 Design Environment 耗时较长）；
    - ``request_timeout``：其余轻量请求预算。
    """

    server_name: str = "cst-runtime"
    transport: str = "stdio"
    startup_timeout: int = 30
    request_timeout: int = 120
    simulation_timeout: int = 1200
    session_timeout: int = 300
    long_run_threshold_seconds: int = 600
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    config_path: Path | None = None
    worker_python: Path = field(default_factory=lambda: Path(sys.executable))
    runtime_source: Path | None = None
    cst_python_libraries: str = ""

    @property
    def instructions(self) -> str:
        return (
            "CST Studio Suite 自动化服务。工具定义和业务行为由独立的 "
            "cst_runtime Python 库提供；MCP 层只负责协议转换和 IPC。"
        )


def get_config() -> MCPConfig:
    """读取环境变量和本地配置。"""
    config_path, raw = _load_config_file()
    project_root = Path(__file__).resolve().parent.parent
    runtime = raw.get("runtime", {})
    return MCPConfig(
        server_name=str(runtime.get("server_name", "cst-runtime")),
        startup_timeout=int(runtime.get("startup_timeout", 30)),
        request_timeout=int(runtime.get("request_timeout", 120)),
        simulation_timeout=int(runtime.get("simulation_timeout", 1200)),
        session_timeout=int(runtime.get("session_timeout", 300)),
        long_run_threshold_seconds=int(
            runtime.get("long_run_threshold_seconds", 600)
        ),
        project_root=project_root,
        config_path=config_path,
        worker_python=_find_worker_python(raw),
        runtime_source=_find_runtime_source(project_root, raw),
        cst_python_libraries=str(
            os.environ.get("CST_PYTHON_LIBS")
            or runtime.get("cst_python_libraries")
            or raw.get("project", {}).get("cst_path")
            or ""
        ),
    )
