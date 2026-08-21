"""Agent/MCP 交互记录的追加式日志管理与内容寻址存储。

负责记录所有工具调用的完整请求/响应生命周期，支持大 Payload 内容寻址保存与跨上下文追溯。
所有会话交互数据与同级 payloads 存放于全局确定性根目录：
  .cst_runtime/interactions/<server_session_id>/
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Mapping

from .models import MCPInteractionRecord, PayloadReference, _now_iso, _sha256_bytes

_INTERACTION_LOCK = threading.RLock()
PAYLOAD_THRESHOLD_BYTES = 16384  # 16 KB
_DEFAULT_SESSION_ID = "default_session"


def get_session_storage_root(
    session_id: str | None = None,
    workspace: str | None = None,
) -> Path:
    """解析会话级交互日志和 Payload 的根存储目录。"""
    sid = session_id or os.environ.get("CST_SERVER_SESSION_ID") or _DEFAULT_SESSION_ID

    if workspace:
        ws = Path(workspace).expanduser().resolve()
        root = ws / ".cst_runtime" / "interactions" / sid
    else:
        env_ws = os.environ.get("CST_WORKSPACE")
        if env_ws:
            root = Path(env_ws).expanduser().resolve() / ".cst_runtime" / "interactions" / sid
        else:
            root = Path.cwd().resolve() / ".cst_runtime" / "interactions" / sid

    root.mkdir(parents=True, exist_ok=True)
    return root


def store_payload_if_large(
    data: Any,
    storage_root: Path,
    threshold: int = PAYLOAD_THRESHOLD_BYTES,
) -> tuple[Any, PayloadReference | None]:
    """若 payload 序列化后超出阈值，写入内容寻址文件并返回引用。"""
    if data is None:
        return None, None
    try:
        raw_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
    except Exception:
        raw_bytes = str(data).encode("utf-8")

    if len(raw_bytes) <= threshold:
        return data, None

    sha256 = _sha256_bytes(raw_bytes)
    payloads_dir = storage_root / "payloads"
    payloads_dir.mkdir(parents=True, exist_ok=True)
    payload_file = payloads_dir / f"{sha256}.json"

    if not payload_file.exists():
        temp_file = payloads_dir / f"{sha256}.tmp"
        temp_file.write_bytes(raw_bytes)
        temp_file.replace(payload_file)

    ref = PayloadReference(
        storage_path=str(payload_file),
        size_bytes=len(raw_bytes),
        sha256=sha256,
    )
    summary_preview = {
        "_payload_ref": ref.to_dict(),
        "_preview": f"<External payload stored at {payload_file.name}, size {len(raw_bytes)} bytes>",
    }
    return summary_preview, ref


def read_payload_reference(ref_data: Mapping[str, Any] | PayloadReference) -> Any:
    """从内容寻址文件读取完整的原始 payload。"""
    if isinstance(ref_data, PayloadReference):
        path = Path(ref_data.storage_path)
    else:
        path = Path(ref_data["storage_path"])
    if not path.is_file():
        raise FileNotFoundError(f"找不到 Payload 文件: {path}")
    raw = path.read_bytes()
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return raw.decode("utf-8", errors="replace")


def get_interaction_journal_path(storage_root: Path) -> Path:
    """获取 interactions 日志文件路径。"""
    return storage_root / "mcp_interactions.jsonl"


def append_interaction_event(
    record: MCPInteractionRecord,
    *,
    session_id: str | None = None,
    workspace: str | None = None,
) -> str:
    """追加一条交互记录到 JSONL 日志文件。"""
    storage_root = get_session_storage_root(
        session_id=session_id,
        workspace=workspace or record.workspace,
    )

    # 检查 args 与 result 是否过大
    if record.request_payload_ref is None and record.tool_args:
        preview, ref = store_payload_if_large(record.tool_args, storage_root)
        if ref is not None:
            record.tool_args = preview
            record.request_payload_ref = ref

    if record.response_payload_ref is None and record.result:
        preview, ref = store_payload_if_large(record.result, storage_root)
        if ref is not None:
            record.result = preview
            record.response_payload_ref = ref

    journal_path = get_interaction_journal_path(storage_root)
    payload_line = json.dumps(record.to_dict(), ensure_ascii=False, default=str)

    with _INTERACTION_LOCK:
        with journal_path.open("a", encoding="utf-8") as handle:
            handle.write(payload_line + "\n")
            handle.flush()

    return str(journal_path)


def list_interactions(
    *,
    session_id: str | None = None,
    workspace: str | None = None,
    task_id: str | None = None,
    run_id: str | None = None,
    project_path: str | None = None,
    tool_name: str | None = None,
    interaction_id: str | None = None,
    operation_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查询匹配的交互记录（最新排在前面）。"""
    storage_root = get_session_storage_root(session_id=session_id, workspace=workspace)
    journal_path = get_interaction_journal_path(storage_root)
    if not journal_path.is_file():
        return []

    lines: list[str] = []
    with _INTERACTION_LOCK:
        raw_text = journal_path.read_text(encoding="utf-8")
        lines = raw_text.splitlines()

    seen_ids: dict[str, dict[str, Any]] = {}
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            iid = item.get("interaction_id")
            if iid:
                seen_ids[iid] = item
        except Exception:
            if idx == len(lines) - 1:
                continue
            continue

    sorted_items = list(seen_ids.values())
    sorted_items.sort(key=lambda x: x.get("started_at") or "", reverse=True)

    filtered: list[dict[str, Any]] = []
    for item in sorted_items:
        if interaction_id and item.get("interaction_id") != interaction_id:
            continue
        if operation_id and item.get("operation_id") != operation_id:
            continue
        if task_id and item.get("task_id") != task_id:
            continue
        if run_id and item.get("run_id") != run_id:
            continue
        if tool_name and item.get("tool_name") != tool_name:
            continue
        if project_path:
            p1 = item.get("project_path")
            if p1 and Path(p1).resolve() != Path(project_path).resolve():
                continue
        filtered.append(item)
        if len(filtered) >= limit:
            break

    return filtered
