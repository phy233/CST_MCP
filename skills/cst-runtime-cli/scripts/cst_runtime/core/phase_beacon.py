"""长任务阶段信标（phase beacon）。

供 runtime 写、MCP proxy 读的双端契约文件：
worker 在关键生命周期节点把当前阶段原子写入
``<cwd>/.cst_runtime/tmp/phase-<sha1(project_path)[:12]>.json``；
proxy 在 detach 终止前读取该文件决定是否给予优雅收尾宽限。

契约要点：
- 两端以同一公式计算路径（abs+resolve+casefold 归一化的 project_path
  的 sha1 前 12 位），任何一端修改公式必须同步另一端；
- 全部 IO 失败静默返回 False/None：信标缺失时 proxy 按未知阶段处理，
  行为退化为"直接终止"，不会因可观测性故障阻塞业务流；
- CLI 直调同样会产生信标文件（无副作用，仓库 .gitignore 已忽略 *.json）。
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

# 生命周期阶段常量：runtime 写入方使用。
OPENING = "opening"
PREFLIGHT = "preflight"
POLLING = "polling"
SOLVER_DONE = "solver_done"
POSTFLIGHT = "postflight"
CLOSING = "closing"

# 这些阶段属于"正在清理/收尾"，proxy 到点终止前若读到且信标新鲜，
# 应给一次性宽限而不是立刻 kill。
GRACE_PHASES = frozenset({POSTFLIGHT, CLOSING})

# 信标新鲜度上限（秒）；超期视为陈旧，不参与宽限判定。
FRESHNESS_SECONDS = 30.0


def _beacon_path(project_path: str | Path) -> Path:
    normalized = Path(project_path).expanduser().resolve()
    key = hashlib.sha1(str(normalized).casefold().encode("utf-8")).hexdigest()[:12]
    tmp_dir = Path.cwd() / ".cst_runtime" / "tmp"
    return tmp_dir / f"phase-{key}.json"


def write_phase(project_path: str | Path, phase: str) -> bool:
    """原子写入当前阶段；任何失败静默返回 False。"""
    try:
        target = _beacon_path(project_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "phase": str(phase),
            "updated_at": time.time(),
            "pid": os.getpid(),
        }
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
        os.replace(tmp, target)
        return True
    except OSError:
        return False


def read_phase(project_path: str | Path) -> dict[str, Any] | None:
    """读取信标内容；缺失或损坏返回 None。"""
    try:
        raw = _beacon_path(project_path).read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        return data
    except (OSError, ValueError):
        return None


def phase_allows_grace(project_path: str | Path) -> bool:
    """proxy 宽限判定：信标存在、新鲜且处于收尾阶段时为 True。"""
    data = read_phase(project_path)
    if not data:
        return False
    updated_at = data.get("updated_at")
    try:
        age = time.time() - float(updated_at)
    except (TypeError, ValueError):
        return False
    if age < 0 or age > FRESHNESS_SECONDS:
        return False
    return str(data.get("phase")) in GRACE_PHASES
