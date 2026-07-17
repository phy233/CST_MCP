"""Adapter: Register explicitly defined MCP tools to FastMCP server.

This module acts as the Tool Registry. It imports the rigidly defined tool schemas
from the `tools` package and registers them, acting as the interface boundary.
"""
from __future__ import annotations

from typing import Any

from .tools import ALL_TOOLS


def register_all_tools(mcp) -> int:
    """Register all modular tools to the MCP server.

    Args:
        mcp: FastMCP server instance

    Returns:
        Number of tools registered
    """
    registered = 0

    for tool_def in ALL_TOOLS:
        name = tool_def["name"]
        handler = tool_def["handler"]

        mcp.tool(name=name)(handler)
        registered += 1

    return registered
