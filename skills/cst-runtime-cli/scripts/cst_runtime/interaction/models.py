"""Agent 与 MCP 交互日志及显式工作笔记领域数据模型。

本模块属于纯 Python 领域逻辑，独立于 History 版本管理与 CST COM。
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class PayloadReference:
    """大 payload 内容寻址存储引用。"""

    storage_path: str
    size_bytes: int
    sha256: str
    is_external: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "storage_path": self.storage_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "is_external": self.is_external,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PayloadReference":
        return cls(
            storage_path=str(data["storage_path"]),
            size_bytes=int(data["size_bytes"]),
            sha256=str(data["sha256"]),
            is_external=bool(data.get("is_external", True)),
        )


@dataclass
class MCPInteractionRecord:
    """记录一次 Agent 调用 MCP 工具的完整生命周期。"""

    interaction_id: str
    tool_name: str
    tool_args: dict[str, Any] = field(default_factory=dict)
    task_id: str | None = None
    run_id: str | None = None
    workspace: str | None = None
    server_name: str = "cst-mcp"
    server_version: str = "0.1.0"
    state: str = "requested"  # requested, running, succeeded, failed, timeout, transport_error
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    started_at: str = field(default_factory=_now_iso)
    ended_at: str | None = None
    duration_ms: float | None = None
    operation_id: str | None = None
    project_path: str | None = None
    before_snapshot_id: str | None = None
    before_snapshot_sha256: str | None = None
    after_snapshot_id: str | None = None
    after_snapshot_sha256: str | None = None
    request_payload_ref: PayloadReference | None = None
    response_payload_ref: PayloadReference | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "interaction_id": self.interaction_id,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "workspace": self.workspace,
            "server_name": self.server_name,
            "server_version": self.server_version,
            "state": self.state,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "operation_id": self.operation_id,
            "project_path": self.project_path,
            "before_snapshot_id": self.before_snapshot_id,
            "before_snapshot_sha256": self.before_snapshot_sha256,
            "after_snapshot_id": self.after_snapshot_id,
            "after_snapshot_sha256": self.after_snapshot_sha256,
        }
        if self.request_payload_ref:
            res["request_payload_ref"] = self.request_payload_ref.to_dict()
        if self.response_payload_ref:
            res["response_payload_ref"] = self.response_payload_ref.to_dict()
        if self.extra:
            res["extra"] = self.extra
        return res

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MCPInteractionRecord":
        req_ref = None
        if data.get("request_payload_ref"):
            req_ref = PayloadReference.from_dict(data["request_payload_ref"])
        resp_ref = None
        if data.get("response_payload_ref"):
            resp_ref = PayloadReference.from_dict(data["response_payload_ref"])

        return cls(
            interaction_id=str(data["interaction_id"]),
            tool_name=str(data["tool_name"]),
            tool_args=dict(data.get("tool_args", {})),
            task_id=data.get("task_id"),
            run_id=data.get("run_id"),
            workspace=data.get("workspace"),
            server_name=str(data.get("server_name", "cst-mcp")),
            server_version=str(data.get("server_version", "0.1.0")),
            state=str(data.get("state", "requested")),
            result=data.get("result"),
            error=data.get("error"),
            started_at=str(data.get("started_at", "")),
            ended_at=data.get("ended_at"),
            duration_ms=data.get("duration_ms"),
            operation_id=data.get("operation_id"),
            project_path=data.get("project_path"),
            before_snapshot_id=data.get("before_snapshot_id"),
            before_snapshot_sha256=data.get("before_snapshot_sha256"),
            after_snapshot_id=data.get("after_snapshot_id"),
            after_snapshot_sha256=data.get("after_snapshot_sha256"),
            request_payload_ref=req_ref,
            response_payload_ref=resp_ref,
            extra=dict(data.get("extra", {})),
        )


@dataclass
class AgentWorkNote:
    """Agent 或用户显式提交的工作说明、设计决策或人工处置结论。"""

    note_id: str
    content: str
    category: str = "general"  # plan, decision, user_confirmation, milestone, reconciliation, general
    timestamp: str = field(default_factory=_now_iso)
    task_id: str | None = None
    run_id: str | None = None
    project_path: str | None = None
    interaction_id: str | None = None
    operation_id: str | None = None
    snapshot_id: str | None = None
    user_confirmed: bool | None = None
    author: str = "agent"  # agent, user, reconciler
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "note_id": self.note_id,
            "category": self.category,
            "content": self.content,
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "project_path": self.project_path,
            "interaction_id": self.interaction_id,
            "operation_id": self.operation_id,
            "snapshot_id": self.snapshot_id,
            "user_confirmed": self.user_confirmed,
            "author": self.author,
        }
        if self.extra:
            res["extra"] = self.extra
        return res

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AgentWorkNote":
        return cls(
            note_id=str(data["note_id"]),
            content=str(data.get("content", "")),
            category=str(data.get("category", "general")),
            timestamp=str(data.get("timestamp", "")),
            task_id=data.get("task_id"),
            run_id=data.get("run_id"),
            project_path=data.get("project_path"),
            interaction_id=data.get("interaction_id"),
            operation_id=data.get("operation_id"),
            snapshot_id=data.get("snapshot_id"),
            user_confirmed=data.get("user_confirmed"),
            author=str(data.get("author", "agent")),
            extra=dict(data.get("extra", {})),
        )
