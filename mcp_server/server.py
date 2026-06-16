"""CST Runtime MCP Server entry point.

Usage:
    # Direct run (stdio transport)
    python -m mcp_server

    # MCP Inspector debug
    mcp dev mcp_server/server.py

    # Install to Claude Desktop
    mcp install mcp_server/server.py --name "CST Runtime"
"""
from __future__ import annotations

import sys
from typing import Any

from .config import get_config


def create_mcp_server():
    """Create and configure the MCP server instance.

    Returns:
        Configured FastMCP instance
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print(
            "Error: mcp package not installed. Run: pip install 'mcp[cli]>=1.20'",
            file=sys.stderr,
        )
        sys.exit(1)

    config = get_config()

    mcp = FastMCP(
        config.server_name,
        instructions=config.instructions,
    )

    # Register all tools from lib layer
    from .adapter import register_all_tools

    count = register_all_tools(mcp)
    print(
        f"CST Runtime MCP Server: {count} tools registered",
        file=sys.stderr,
    )

    return mcp


def main():
    """Run the MCP server with stdio transport."""
    mcp = create_mcp_server()
    config = get_config()
    mcp.run(transport=config.transport)


if __name__ == "__main__":
    main()
