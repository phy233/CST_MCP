"""Adapter: Register explicitly defined MCP tools to FastMCP server.

This module acts as the Tool Registry. It imports the rigidly defined tool schemas
from the `tools` package and registers them, acting as the interface boundary.
"""
from __future__ import annotations

import sys
import json
from typing import Any

from .config import get_config

# Ensure cst_runtime is importable before importing tools (so proxy can be resolved)
_config = get_config()
_crt_scripts = str(_config.cst_runtime_root)
if _crt_scripts not in sys.path:
    sys.path.insert(0, _crt_scripts)

from .tools import ALL_TOOLS

def register_all_tools(mcp) -> int:
    """Register all modular tools to the MCP server.

    Args:
        mcp: FastMCP server instance

    Returns:
        Number of tools registered
    """
    registered = 0
    config = get_config()

    for tool_def in ALL_TOOLS:
        name = tool_def["name"]
        handler = tool_def["handler"]
        
        # Risk control checking can be added here if we define a "risk" field in the dict.
        # For this MVP, we just register all tools defined in the modular lists.
        
        mcp.tool(name=name)(handler)
        registered += 1

    return registered

def list_available_tools() -> list[dict[str, Any]]:
    """List all available MCP tools without registering.

    Returns:
        List of tool info dicts
    """
    return ALL_TOOLS
