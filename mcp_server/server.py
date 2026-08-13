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
        timeout = (
            config.simulation_timeout
            if name in {"quick-sweep", "cross-process-sweep", "wait-simulation"}
            else config.request_timeout
        )
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
