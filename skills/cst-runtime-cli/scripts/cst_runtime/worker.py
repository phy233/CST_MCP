"""cst_runtime 的白名单 JSON 行协议 worker。"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any


def _load_local_config() -> dict[str, Any]:
    configured = os.environ.get("CST_MCP_CONFIG")
    candidates = [Path(configured)] if configured else []
    candidates.append(Path.cwd() / ".cst_config.json")
    for path in candidates:
        try:
            if path.is_file():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return {}


def _configure_cst_path() -> None:
    config = _load_local_config()
    configured = (
        os.environ.get("CST_PYTHON_LIBS")
        or config.get("runtime", {}).get("cst_python_libraries")
        or config.get("project", {}).get("cst_path")
    )
    if configured and configured not in sys.path:
        sys.path.insert(0, configured)


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """处理一个白名单请求并回显请求 ID。"""
    request_id = request.get("id")
    action = request.get("action")
    try:
        if action == "ping":
            payload: dict[str, Any] = {"status": "pong"}
        elif action == "describe_tools":
            from .api import describe_tools

            payload = {"status": "success", "tools": describe_tools()}
        elif action == "call_tool":
            from .api import invoke_tool

            payload = invoke_tool(
                str(request.get("name", "")),
                request.get("arguments") or {},
            )
        else:
            payload = {
                "status": "error",
                "error_type": "unsupported_action",
                "message": f"不支持的 worker 动作: {action}",
            }
    except Exception as exc:
        payload = {
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    return {"id": request_id, **payload}


def main() -> int:
    """启动 worker 并通过标准输入输出处理 JSON 行。"""
    _configure_cst_path()
    print(json.dumps({"status": "ready"}, ensure_ascii=False), flush=True)
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            if request.get("action") == "shutdown":
                response = {
                    "id": request.get("id"),
                    "status": "success",
                    "shutdown": True,
                }
                print(json.dumps(response, ensure_ascii=False), flush=True)
                return 0
            response = handle_request(request)
        except json.JSONDecodeError as exc:
            response = {
                "id": None,
                "status": "error",
                "error_type": "json_error",
                "message": str(exc),
            }
        print(json.dumps(response, ensure_ascii=False, default=str), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
