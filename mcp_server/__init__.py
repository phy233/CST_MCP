"""CST Runtime MCP Server.

Provides MCP (Model Context Protocol) interface for CST Studio Suite automation.
Exposes 113+ tools for electromagnetic simulation: modeling, solver control,
results extraction, farfield analysis, optimization.

Usage:
    # Direct run (stdio)
    python -m mcp_server

    # MCP Inspector debug
    mcp dev mcp_server/server.py

    # Install to Claude Desktop
    mcp install mcp_server/server.py --name "CST Runtime"
"""
