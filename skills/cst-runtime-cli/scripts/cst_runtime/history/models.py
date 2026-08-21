"""CST History 版本管理领域数据模型与哈希计算。

本模块属于纯 Python 领域逻辑，不依赖 CST COM 或 Python 接口，可在任何环境下离线运行。
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


KNOWN_BLOCK_FIELDS = frozenset({
    "name",
    "contents",
    "version",
    "error",
    "exclude",
    "hide",
    "has_undo",
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class HistoryBlock:
    """线性 History List 中的一个不可变 History 块。"""

    index: int
    name: str
    contents: str
    version: str = ""
    error: bool = False
    exclude: bool = False
    hide: bool = False
    has_undo: bool = False
    extra_fields: dict[str, Any] = field(default_factory=dict)
    contents_sha256: str = field(default="")

    def __post_init__(self) -> None:
        if not self.contents_sha256:
            object.__setattr__(self, "contents_sha256", _sha256_text(self.contents))

    @classmethod
    def from_raw(cls, index: int, raw: Mapping[str, Any]) -> "HistoryBlock":
        """从 CST _GetHistory 导出的单项原始字典构建 HistoryBlock。"""
        raw_dict = dict(raw)
        name = str(raw_dict.get("name", ""))
        contents = str(raw_dict.get("contents", ""))
        version = str(raw_dict.get("version", ""))
        error = bool(raw_dict.get("error", False))
        exclude = bool(raw_dict.get("exclude", False))
        hide = bool(raw_dict.get("hide", False))
        has_undo = bool(raw_dict.get("has_undo", False))

        extra = {k: v for k, v in raw_dict.items() if k not in KNOWN_BLOCK_FIELDS}
        return cls(
            index=index,
            name=name,
            contents=contents,
            version=version,
            error=error,
            exclude=exclude,
            hide=hide,
            has_undo=has_undo,
            extra_fields=extra,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HistoryBlock":
        """从 to_dict 序列化的标准字典还原 HistoryBlock，保持 extra_fields 与元数据不被二次污染。"""
        data_dict = dict(data)
        index = int(data_dict.get("index", 0))
        name = str(data_dict.get("name", ""))
        contents = str(data_dict.get("contents", ""))
        version = str(data_dict.get("version", ""))
        error = bool(data_dict.get("error", False))
        exclude = bool(data_dict.get("exclude", False))
        hide = bool(data_dict.get("hide", False))
        has_undo = bool(data_dict.get("has_undo", False))
        contents_sha256 = str(data_dict.get("contents_sha256", ""))
        extra = dict(data_dict.get("extra_fields", {}))
        return cls(
            index=index,
            name=name,
            contents=contents,
            version=version,
            error=error,
            exclude=exclude,
            hide=hide,
            has_undo=has_undo,
            contents_sha256=contents_sha256,
            extra_fields=extra,
        )

    def to_dict(self) -> dict[str, Any]:
        """序列化为标准 JSON 字典。"""
        res: dict[str, Any] = {
            "index": self.index,
            "name": self.name,
            "contents": self.contents,
            "version": self.version,
            "error": self.error,
            "exclude": self.exclude,
            "hide": self.hide,
            "has_undo": self.has_undo,
            "contents_sha256": self.contents_sha256,
        }
        if self.extra_fields:
            res["extra_fields"] = self.extra_fields
        return res

    def to_cst_raw(self) -> dict[str, Any]:
        """还原为 CST _GetHistory 风格的原始字典。"""
        res: dict[str, Any] = {
            "name": self.name,
            "contents": self.contents,
            "version": self.version,
            "error": self.error,
            "exclude": self.exclude,
            "hide": self.hide,
            "has_undo": self.has_undo,
        }
        res.update(self.extra_fields)
        return res

    def canonical_dict(self) -> dict[str, Any]:
        """用于快照哈希计算的规范字典表示。"""
        return {
            "index": self.index,
            "name": self.name,
            "contents": self.contents,
            "version": self.version,
            "error": self.error,
            "exclude": self.exclude,
            "hide": self.hide,
            "has_undo": self.has_undo,
            "extra_fields": self.extra_fields,
        }


def compute_snapshot_sha256(blocks: list[HistoryBlock]) -> str:
    """计算 History 块序列的确定性 SHA-256 哈希。"""
    canonical_list = [block.canonical_dict() for block in blocks]
    canonical_bytes = _canonical_json(canonical_list).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


@dataclass(frozen=True)
class HistorySnapshot:
    """某一时刻工程 History 完整状态的快照。"""

    snapshot_id: str
    project_path: str
    project_name: str
    cst_version: str | None
    captured_at: str
    blocks: list[HistoryBlock]
    snapshot_sha256: str
    parent_snapshot_id: str | None = None
    reason: str = "manual"
    operation_id: str | None = None
    schema_version: str = "1.0.0"

    @classmethod
    def from_raw_cst(
        cls,
        raw_cst_data: Mapping[str, Any] | None,
        *,
        project_path: str,
        cst_version: str | None = None,
        reason: str = "capture",
        parent_snapshot_id: str | None = None,
        operation_id: str | None = None,
        snapshot_id: str | None = None,
        captured_at: str | None = None,
    ) -> "HistorySnapshot":
        """从 CST _GetHistory 返回的原始字典（如 {'list': None} 或 {'list': [...]}）构建快照。"""
        blocks: list[HistoryBlock] = []
        if raw_cst_data is not None:
            raw_list = raw_cst_data.get("list")
            if isinstance(raw_list, (list, tuple)):
                for idx, item in enumerate(raw_list):
                    if isinstance(item, Mapping):
                        blocks.append(HistoryBlock.from_raw(idx, item))

        p = Path(project_path)
        project_name = p.stem if project_path else ""
        resolved_snapshot_id = snapshot_id or uuid.uuid4().hex
        resolved_captured_at = captured_at or _now_iso()
        sha256 = compute_snapshot_sha256(blocks)

        return cls(
            snapshot_id=resolved_snapshot_id,
            project_path=str(p),
            project_name=project_name,
            cst_version=cst_version,
            captured_at=resolved_captured_at,
            blocks=blocks,
            snapshot_sha256=sha256,
            parent_snapshot_id=parent_snapshot_id,
            reason=reason,
            operation_id=operation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """序列化为可持久化的 JSON 字典。"""
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "project_path": self.project_path,
            "project_name": self.project_name,
            "cst_version": self.cst_version,
            "captured_at": self.captured_at,
            "block_count": len(self.blocks),
            "snapshot_sha256": self.snapshot_sha256,
            "parent_snapshot_id": self.parent_snapshot_id,
            "reason": self.reason,
            "operation_id": self.operation_id,
            "blocks": [b.to_dict() for b in self.blocks],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HistorySnapshot":
        """从字典还原 HistorySnapshot。"""
        blocks = [
            HistoryBlock.from_dict(b) if ("contents_sha256" in b or "extra_fields" in b)
            else HistoryBlock.from_raw(b.get("index", idx), b)
            for idx, b in enumerate(data.get("blocks", []))
        ]
        return cls(
            snapshot_id=str(data["snapshot_id"]),
            project_path=str(data.get("project_path", "")),
            project_name=str(data.get("project_name", "")),
            cst_version=data.get("cst_version"),
            captured_at=str(data.get("captured_at", "")),
            blocks=blocks,
            snapshot_sha256=str(data.get("snapshot_sha256") or compute_snapshot_sha256(blocks)),
            parent_snapshot_id=data.get("parent_snapshot_id"),
            reason=str(data.get("reason", "")),
            operation_id=data.get("operation_id"),
            schema_version=str(data.get("schema_version", "1.0.0")),
        )


@dataclass
class HistoryOperationRecord:
    """记录一次向 CST 提交 History 操作的全过程与状态。"""

    operation_id: str
    history_label: str
    business_vba: str                  # 干净的可重放原始业务 VBA
    business_vba_sha256: str
    project_path: str
    intent: str = "submit"
    parent_operation_id: str | None = None
    interaction_id: str | None = None
    task_id: str | None = None
    run_id: str | None = None
    wrapped_vba: str | None = None      # 提交给 CST 的包装后完整 VBA
    before_snapshot_id: str | None = None
    before_snapshot_sha256: str | None = None
    after_snapshot_id: str | None = None
    after_snapshot_sha256: str | None = None
    execution_state: str = "pending"   # pending, submitted, succeeded, failed, interrupted
    recording_status: str = "complete" # complete, incomplete
    reconciliation_state: str = "not_required"  # not_required, not_applied, applied, ambiguous, reconciled
    cst_error_envelope: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    timestamp: str = field(default_factory=_now_iso)
    evidence_paths: list[str] = field(default_factory=list)
    reconciliation_notes: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.business_vba_sha256 and self.business_vba:
            self.business_vba_sha256 = _sha256_text(self.business_vba)

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "operation_id": self.operation_id,
            "parent_operation_id": self.parent_operation_id,
            "interaction_id": self.interaction_id,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "intent": self.intent,
            "history_label": self.history_label,
            "business_vba": self.business_vba,
            "business_vba_sha256": self.business_vba_sha256,
            "wrapped_vba": self.wrapped_vba,
            "project_path": self.project_path,
            "before_snapshot_id": self.before_snapshot_id,
            "before_snapshot_sha256": self.before_snapshot_sha256,
            "after_snapshot_id": self.after_snapshot_id,
            "after_snapshot_sha256": self.after_snapshot_sha256,
            "execution_state": self.execution_state,
            "recording_status": self.recording_status,
            "reconciliation_state": self.reconciliation_state,
            "cst_error_envelope": self.cst_error_envelope,
            "error": self.error,
            "timestamp": self.timestamp,
            "evidence_paths": self.evidence_paths,
            "reconciliation_notes": self.reconciliation_notes,
        }
        if self.extra:
            res["extra"] = self.extra
        return res

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HistoryOperationRecord":
        return cls(
            operation_id=str(data["operation_id"]),
            parent_operation_id=data.get("parent_operation_id"),
            interaction_id=data.get("interaction_id"),
            task_id=data.get("task_id"),
            run_id=data.get("run_id"),
            intent=str(data.get("intent", "submit")),
            history_label=str(data.get("history_label", "")),
            business_vba=str(data.get("business_vba", "")),
            business_vba_sha256=str(data.get("business_vba_sha256", "")),
            project_path=str(data.get("project_path", "")),
            wrapped_vba=data.get("wrapped_vba"),
            before_snapshot_id=data.get("before_snapshot_id"),
            before_snapshot_sha256=data.get("before_snapshot_sha256"),
            after_snapshot_id=data.get("after_snapshot_id"),
            after_snapshot_sha256=data.get("after_snapshot_sha256"),
            execution_state=str(data.get("execution_state", data.get("state", "pending"))),
            recording_status=str(data.get("recording_status", "complete")),
            reconciliation_state=str(data.get("reconciliation_state", "not_required")),
            cst_error_envelope=data.get("cst_error_envelope"),
            error=data.get("error"),
            timestamp=str(data.get("timestamp", "")),
            evidence_paths=list(data.get("evidence_paths", [])),
            reconciliation_notes=data.get("reconciliation_notes"),
            extra=dict(data.get("extra", {})),
        )
