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
    worker_script: Path = field(default_factory=lambda: _find_worker_script())
    log_dir: Path = field(default_factory=lambda: Path.home() / ".cst-mcp" / "logs")

    # Tool settings
    enable_write_tools: bool = True
    enable_session_tools: bool = True
    risk_tag_format: str = "[{risk}]"

    # Simulation
    default_poll_interval: int = 10
    default_timeout: int = 120

    @property
    def instructions(self) -> str:
        return (
            "CST Studio Suite automation server. "
            "Tools for electromagnetic simulation: session management, "
            "geometry modeling, parameter control, solver operations. "
            "Tools tagged with [WRITE] modify CST projects; [READ] tools are safe. "
            "Always run 'inspect-session' first to check environment. "
            "Use 'start-simulation' + 'sim-status' for non-blocking simulation workflow."
        )


def _find_worker_script() -> Path:
    """Locate cst_worker.py relative to the project root.

    Layout:
        project_root/
        ├── mcp_server/config.py   (this file)
        └── skills/cst-runtime-cli/scripts/cst_worker.py
    """
    project_root = Path(__file__).resolve().parent.parent
    candidates = [
        project_root / "skills" / "cst-runtime-cli" / "scripts" / "cst_worker.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    # Fallback: return first candidate path (will fail at runtime with clear error)
    return candidates[0]


def get_config() -> MCPConfig:
    """Get MCP configuration instance."""
    return MCPConfig()
