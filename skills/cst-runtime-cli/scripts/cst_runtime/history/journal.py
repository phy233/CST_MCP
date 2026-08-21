"""CST History 快照与操作日志的存储管理。

负责持久化 History 快照（原子临时文件+替换）、追加式 operation 日志流与容错读取。
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path
from typing import Any, Mapping

from .models import HistoryOperationRecord, HistorySnapshot

_HISTORY_JOURNAL_LOCK = threading.RLock()


def resolve_history_root(
    project_path: str | None = None,
    run_dir: str | Path | None = None,
    workspace: str | None = None,
) -> Path:
    """解析 History 数据存储的根目录（单一确定性归属）。"""
    if run_dir:
        rd = Path(run_dir).expanduser().resolve()
        if rd.is_dir():
            return rd / "history"

    if project_path:
        from ..core.identity import infer_run_dir_from_project
        inferred = infer_run_dir_from_project(project_path)
        if inferred and inferred.is_dir():
            return inferred / "history"
        p = Path(project_path).expanduser().resolve()
        return p.parent / ".cst_history"

    if workspace:
        ws = Path(workspace).expanduser().resolve()
        return ws / ".cst_runtime" / "history"

    env_ws = os.environ.get("CST_WORKSPACE")
    if env_ws:
        return Path(env_ws).expanduser().resolve() / ".cst_runtime" / "history"

    return Path.cwd().resolve() / ".cst_runtime" / "history"


def save_snapshot(
    snapshot: HistorySnapshot,
    *,
    storage_root: Path | None = None,
    project_path: str | None = None,
) -> Path:
    """通过临时文件 + os.replace 原子保存一份 History 快照为 JSON 文件。"""
    root = storage_root or resolve_history_root(project_path=project_path or snapshot.project_path)
    snapshots_dir = root / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    snapshot_file = snapshots_dir / f"{snapshot.snapshot_id}.json"
    temp_file = snapshots_dir / f"{snapshot.snapshot_id}.tmp.{uuid.uuid4().hex[:8]}"

    data_bytes = json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2).encode("utf-8")
    with _HISTORY_JOURNAL_LOCK:
        temp_file.write_bytes(data_bytes)
        temp_file.replace(snapshot_file)

    return snapshot_file


def load_snapshot(
    snapshot_id: str,
    *,
    storage_root: Path | None = None,
    project_path: str | None = None,
) -> HistorySnapshot | None:
    """从磁盘加载指定 ID 的快照。"""
    root = storage_root or resolve_history_root(project_path=project_path)
    snapshot_file = root / "snapshots" / f"{snapshot_id}.json"
    if not snapshot_file.is_file():
        return None

    with _HISTORY_JOURNAL_LOCK:
        content = snapshot_file.read_text(encoding="utf-8")
    data = json.loads(content)
    return HistorySnapshot.from_dict(data)


def list_snapshots(
    *,
    storage_root: Path | None = None,
    project_path: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """列出保存的快照索引。"""
    root = storage_root or resolve_history_root(project_path=project_path)
    snapshots_dir = root / "snapshots"
    if not snapshots_dir.is_dir():
        return []

    snapshots: list[dict[str, Any]] = []
    with _HISTORY_JOURNAL_LOCK:
        files = sorted(snapshots_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                snapshots.append({
                    "snapshot_id": data.get("snapshot_id", f.stem),
                    "captured_at": data.get("captured_at"),
                    "project_path": data.get("project_path"),
                    "project_name": data.get("project_name"),
                    "block_count": data.get("block_count", len(data.get("blocks", []))),
                    "snapshot_sha256": data.get("snapshot_sha256"),
                    "parent_snapshot_id": data.get("parent_snapshot_id"),
                    "reason": data.get("reason"),
                    "operation_id": data.get("operation_id"),
                    "file_path": str(f),
                })
                if len(snapshots) >= limit:
                    break
            except Exception:
                continue

    return snapshots


def get_operations_journal_path(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    return root / "operations.jsonl"


def append_operation(
    record: HistoryOperationRecord,
    *,
    storage_root: Path | None = None,
    project_path: str | None = None,
) -> str:
    """追加一条 History 操作记录。"""
    root = storage_root or resolve_history_root(project_path=project_path or record.project_path)
    journal_path = get_operations_journal_path(root)
    line = json.dumps(record.to_dict(), ensure_ascii=False, default=str)

    with _HISTORY_JOURNAL_LOCK:
        with journal_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()

    return str(journal_path)


def _read_operations_jsonl(journal_path: Path) -> list[dict[str, Any]]:
    """容错读取 JSONL，自动忽略末尾因崩溃截断的不完整行。"""
    if not journal_path.is_file():
        return []

    lines: list[str] = []
    with _HISTORY_JOURNAL_LOCK:
        raw_text = journal_path.read_text(encoding="utf-8")
        lines = raw_text.splitlines()

    records: list[dict[str, Any]] = []
    for idx, line in enumerate(lines):
        line_str = line.strip()
        if not line_str:
            continue
        try:
            records.append(json.loads(line_str))
        except json.JSONDecodeError:
            # 若是最后一行残损（例如断电或崩溃），静默忽略并记录
            if idx == len(lines) - 1:
                continue
            continue

    return records


def get_operation(
    operation_id: str,
    *,
    storage_root: Path | None = None,
    project_path: str | None = None,
) -> HistoryOperationRecord | None:
    """获取指定 operation_id 的最新操作记录。"""
    root = storage_root or resolve_history_root(project_path=project_path)
    journal_path = get_operations_journal_path(root)
    raw_records = _read_operations_jsonl(journal_path)

    latest_record: HistoryOperationRecord | None = None
    for data in raw_records:
        if data.get("operation_id") == operation_id:
            latest_record = HistoryOperationRecord.from_dict(data)

    return latest_record


def list_operations(
    *,
    storage_root: Path | None = None,
    project_path: str | None = None,
    execution_state: str | None = None,
    reconciliation_state: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查询操作历史列表（最新排在前面，去重保留最新状态）。"""
    root = storage_root or resolve_history_root(project_path=project_path)
    journal_path = get_operations_journal_path(root)
    raw_records = _read_operations_jsonl(journal_path)

    seen: dict[str, dict[str, Any]] = {}
    for data in raw_records:
        op_id = data.get("operation_id")
        if op_id:
            seen[op_id] = data

    sorted_records = sorted(
        seen.values(),
        key=lambda x: x.get("timestamp") or "",
        reverse=True,
    )

    filtered: list[dict[str, Any]] = []
    for rec in sorted_records:
        if execution_state and rec.get("execution_state") != execution_state:
            continue
        if reconciliation_state and rec.get("reconciliation_state") != reconciliation_state:
            continue
        if project_path:
            p1 = rec.get("project_path")
            if p1 and Path(p1).resolve() != Path(project_path).resolve():
                continue
        filtered.append(rec)
        if len(filtered) >= limit:
            break

    return filtered
