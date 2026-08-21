"""cst_runtime 的白名单 JSON 行协议 worker。"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any


def _emit_json_line(payload: dict[str, Any]) -> None:
    """以仅含 ASCII 的 JSONL 输出响应，避免受 Windows 控制台编码影响。"""
    print(json.dumps(payload, ensure_ascii=True, default=str), flush=True)


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
    from .context import set_current_execution_context
    from .contracts import error_response, normalize_response

    request_id = request.get("id")
    action = request.get("action")
    arguments = request.get("arguments") or {}

    interaction_id = request.get("interaction_id") or arguments.get("_mcp_interaction_id")
    task_id = request.get("task_id") or arguments.get("task_id")
    run_id = request.get("run_id") or arguments.get("run_id")
    project_path = arguments.get("project_path") or arguments.get("fullpath") or arguments.get("working_project")

    set_current_execution_context(
        interaction_id=str(interaction_id) if interaction_id else None,
        task_id=str(task_id) if task_id else None,
        run_id=str(run_id) if run_id else None,
        project_path=str(project_path) if project_path else None,
    )

    try:
        if action == "ping":
            payload: dict[str, Any] = {"status": "pong"}
        elif action == "describe_tools":
            from .api import describe_tools

            payload = {"status": "success", "tools": describe_tools()}
        elif action == "call_tool":
            from .api import invoke_tool

            payload = normalize_response(
                invoke_tool(
                    str(request.get("name", "")),
                    arguments,
                )
            )
        else:
            payload = error_response(
                "unsupported_action",
                f"不支持的 worker 动作: {action}",
                phase="validation",
                action=action,
            )
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        payload = error_response(
            "worker_error",
            str(exc) or "worker 内部调用失败",
            phase="worker",
            action=action,
            tool_name=request.get("name"),
        )
    return {"id": request_id, **payload}


def main() -> int:
    """启动 worker 并通过标准输入输出处理 JSON 行。"""
    _configure_cst_path()
    _emit_json_line({"status": "ready"})
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
                _emit_json_line(response)
                return 0
            response = handle_request(request)
        except json.JSONDecodeError as exc:
            from .contracts import error_response

            response = {
                "id": None,
                **error_response(
                    "validation_error",
                    str(exc),
                    phase="validation",
                    protocol_error="json_error",
                ),
            }
        except Exception as exc:
            from .contracts import error_response

            traceback.print_exc(file=sys.stderr)
            response = {
                "id": None,
                **error_response(
                    "worker_error",
                    str(exc) or "worker 请求处理失败",
                    phase="worker",
                ),
            }
        _emit_json_line(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
