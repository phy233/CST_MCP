"""由 cst_runtime 工具清单驱动的纯 MCP 适配服务。"""
from __future__ import annotations

import asyncio
from typing import Any

from .config import get_config
from .proxy import CSTTransportError, get_proxy


def _call_tool_with_transport_envelope(
    proxy: Any,
    name: str,
    arguments: dict[str, Any],
    *,
    timeout: int,
) -> dict[str, Any]:
    """Keep transport failures inside the public structured-result contract."""
    try:
        return proxy.call_tool(name, arguments, timeout=timeout)
    except CSTTransportError as exc:
        return exc.to_response(tool_name=name)


def _timeout_for_risk(
    risk: str,
    *,
    request_timeout: int,
    simulation_timeout: int,
    session_timeout: int | None = None,
) -> int:
    """按工具风险类别分配传输层预算。

    - long-running：仿真硬兜底（大于 runtime 的长任务分界）；
    - session / process-control：会话类操作（如冷启动 Design Environment）
      使用更长预算；未提供 session_timeout 时按普通请求预算处理；
    - 其余轻量请求使用普通请求预算。
    """
    if risk == "long-running":
        return simulation_timeout
    if risk in {"session", "process-control"}:
        return session_timeout if session_timeout is not None else request_timeout
    return request_timeout


# 治理对象：声明 timeout_seconds 参数的 long-running 工具。
# 该参数语义为"本次调用愿意阻塞多久"，一旦达到或超过 transport 硬兜底，
# worker 会在 internal 收尾之前被 detach 杀掉——显式拒绝优于隐性竞速。
_GOVERNED_TIMEOUT_ARG = "timeout_seconds"

# postflight 余量：internal 在 cap 到点后仍需写日志/关会话/读 Run ID。
_POSTFLIGHT_MARGIN_SECONDS = 60


def _governed_long_running_tools(tool_descriptions: list[dict[str, Any]]) -> set[str]:
    """从 Registry 描述中推导需要超时治理的工具集合（动态，不硬编码）。"""
    governed: set[str] = set()
    for tool in tool_descriptions:
        if str(tool.get("risk")) != "long-running":
            continue
        schema = tool.get("input_schema") or {}
        properties = schema.get("properties") or {}
        if _GOVERNED_TIMEOUT_ARG in properties:
            governed.add(str(tool["name"]))
    return governed


def _governance_rejection(
    governed_tools: set[str],
    name: str,
    arguments: dict[str, Any],
    effective_timeout: int,
) -> dict[str, Any] | None:
    """timeout_seconds 超出允许等待预算时返回结构化拒绝；否则 None。"""
    if name not in governed_tools:
        return None
    raw = arguments.get(_GOVERNED_TIMEOUT_ARG)
    if raw is None or isinstance(raw, bool):
        return None
    try:
        requested = float(raw)
    except (TypeError, ValueError):
        return None
    allowed_budget = effective_timeout - _POSTFLIGHT_MARGIN_SECONDS
    if requested <= allowed_budget:
        return None
    return {
        "ok": False,
        "status": "error",
        "error_type": "invalid_arguments",
        "message": (
            f"{_GOVERNED_TIMEOUT_ARG}={requested:g}s 超过本连接的等待预算 "
            f"{allowed_budget}s（transport 上限 {effective_timeout}s − "
            f"postflight 余量 {_POSTFLIGHT_MARGIN_SECONDS}s）。"
            "超过分界将由 detached 协议接管：请在 .cst_config.json 增大 "
            "runtime.simulation_timeout，或依赖 relay 模式——省缺该参数并在 "
            "detached 后用新的 wait-simulation 继续接力等待。"
        ),
        "error": {
            "type": "invalid_arguments",
            "message": (
                f"timeout_seconds > {allowed_budget}s 对该连接不可等待"
            ),
            "phase": "validation",
        },
        "context": {
            "tool_name": name,
            "requested_seconds": requested,
            "allowed_wait_budget_seconds": allowed_budget,
            "transport_limit_seconds": effective_timeout,
        },
    }


def create_mcp_server():
    """创建低层 MCP Server，不复制 runtime 函数签名。"""
    from mcp import types
    from mcp.server import Server

    config = get_config()
    server = Server(
        config.server_name,
        instructions=config.instructions,
    )
    proxy = get_proxy()
    tool_descriptions = [
        tool for tool in proxy.describe_tools()
        if tool.get("exposure") == "agent"
    ]
    agent_tool_names = {tool["name"] for tool in tool_descriptions}
    agent_tool_risks = {
        tool["name"]: str(tool.get("risk", "read"))
        for tool in tool_descriptions
    }
    governed_long_running_tools = _governed_long_running_tools(
        tool_descriptions
    )

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=tool["name"],
                description=tool.get("description"),
                inputSchema=tool["input_schema"],
                outputSchema=tool.get("output_schema"),
                annotations=types.ToolAnnotations(
                    readOnlyHint=tool.get("risk") == "read",
                    destructiveHint=tool.get("risk") in {
                        "write",
                        "filesystem-write",
                        "session",
                        "process-control",
                        "long-running",
                    },
                ),
            )
            for tool in tool_descriptions
        ]

    @server.call_tool(validate_input=True)
    async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in agent_tool_names:
            return {
                "ok": False,
                "status": "error",
                "error_type": "tool_not_exposed",
                "message": f"工具未获准通过 MCP Agent 调用: {name}",
                "error": {
                    "type": "tool_not_exposed",
                    "message": f"工具未获准通过 MCP Agent 调用: {name}",
                    "phase": "validation",
                },
                "context": {},
            }
        timeout = _timeout_for_risk(
            agent_tool_risks.get(name, "read"),
            request_timeout=config.request_timeout,
            simulation_timeout=config.simulation_timeout,
            session_timeout=config.session_timeout,
        )
        governance = _governance_rejection(
            governed_long_running_tools,
            name,
            arguments,
            timeout,
        )
        if governance is not None:
            return governance
        return await asyncio.to_thread(
            _call_tool_with_transport_envelope,
            proxy,
            name,
            arguments,
            timeout=timeout,
        )

    return server


async def _run_stdio() -> None:
    from mcp.server.stdio import stdio_server

    server = create_mcp_server()
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    finally:
        await asyncio.to_thread(get_proxy().shutdown)


def main() -> None:
    """运行 stdio MCP 服务。"""
    asyncio.run(_run_stdio())


if __name__ == "__main__":
    main()
