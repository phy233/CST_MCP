"""MCP Server configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MCPConfig:
    """Configuration for CST Runtime MCP Server."""

    server_name: str = "cst-runtime"
    transport: str = "stdio"

    # Paths
    cst_runtime_root: Path = field(default_factory=lambda: _find_cst_runtime_root())
    log_dir: Path = field(default_factory=lambda: Path.home() / ".cst-mcp" / "logs")

    # Tool settings
    enable_write_tools: bool = True
    enable_session_tools: bool = True
    risk_tag_format: str = "[{risk}]"

    # Simulation
    default_poll_interval: int = 10
    default_timeout: int = 3600

    @property
    def instructions(self) -> str:
        return (
            "CST Studio Suite automation server. "
            "113+ tools for electromagnetic simulation: modeling, solver control, "
            "results extraction, farfield analysis, optimization. "
            "Tools tagged with [WRITE] modify CST projects; [READ] tools are safe. "
            "Always run 'inspect-session' first to check environment. "
            "Use 'start-simulation' + 'sim-status' for non-blocking simulation workflow."
        )


def _find_cst_runtime_root() -> Path:
    """Find the cst_runtime package root."""
    # Try relative to this file
    candidates = [
        Path(__file__).parent.parent / "skills" / "cst-runtime-cli" / "scripts",
        Path(__file__).parent.parent / "cst_runtime",
    ]
    for candidate in candidates:
        if (candidate / "cst_runtime" / "__init__.py").exists():
            return candidate
        if (candidate / "__init__.py").exists() and candidate.name == "cst_runtime":
            return candidate.parent
    return Path(__file__).parent.parent / "skills" / "cst-runtime-cli" / "scripts"


def get_config() -> MCPConfig:
    """Get MCP configuration instance."""
    return MCPConfig()
