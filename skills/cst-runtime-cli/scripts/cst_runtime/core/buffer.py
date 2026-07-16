"""buffer.py — Pure data module for VBA command buffering.

Manages buffered VBA commands per project session.
Does not interact with COM or CST — the actual "send to CST"
is the caller's responsibility (see modeling.flush_batch).
"""
from __future__ import annotations

from typing import Dict, List, Tuple


class CommandBuffer:
    """Buffered VBA commands for a single project session."""

    def __init__(self, summary: str) -> None:
        self.summary = summary
        self._scripts: List[str] = []

    def append(self, vba_script: str) -> None:
        self._scripts.append(vba_script)

    def get_vba_script(self) -> str:
        scripts = [s for s in self._scripts if s.strip()]
        if not scripts:
            return ""
        return "\n".join(scripts) + "\n"


# session_id (normalized project path) -> CommandBuffer
_buffers: Dict[str, CommandBuffer] = {}


def begin_batch(session_id: str, summary: str = "Batch Execution") -> None:
    """Start a new batch. Raises RuntimeError if already active."""
    if session_id in _buffers:
        raise RuntimeError(f"Batch already active for session: {session_id}")
    _buffers[session_id] = CommandBuffer(summary=summary)


def is_batch_mode(session_id: str) -> bool:
    """Check whether the given session has an active batch."""
    return session_id in _buffers


def append_to_batch(session_id: str, vba_lines: List[str]) -> None:
    """Append VBA lines to the active batch. Raises if no active batch."""
    buf = _buffers.get(session_id)
    if buf is None:
        raise RuntimeError(f"No active batch for session: {session_id}")
    buf.append("\n".join(vba_lines))


def pop_batch(session_id: str) -> Tuple[str, str]:
    """Remove and return (summary, vba_script). Raises if no active batch."""
    buf = _buffers.pop(session_id, None)
    if buf is None:
        raise RuntimeError(f"No active batch for session: {session_id}")
    return buf.summary, buf.get_vba_script()


def discard_batch(session_id: str) -> None:
    """Discard the batch. No-op if not active (idempotent)."""
    _buffers.pop(session_id, None)
