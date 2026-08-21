"""面向 Python 开发者的 History 版本管理公共 API 门面。

协调 core、history 领域模块与文件系统操作，提供完整的快照导出、diff 比对、
恢复计划计算、物理工程一致性备份、隔离副本逐步重放与人工对齐处置。
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Mapping

from ..context import get_current_execution_context
from ..core.compatibility import (
    activate_project,
    active_project,
    create_design_environment,
    detect_history_capabilities,
    get_open_project,
    get_raw_history,
)
from ..core.error_gateway import submit_vba_history
from ..core.identity import (
    _project_companion_dir,
    attach_expected_project,
    normalize_project_path,
    wait_project_unlocked,
)
from ..core.project import save_project
from ..core.session import (
    close_project,
    open_project,
)
from ..history.checkpoint import (
    generate_restore_plan,
    list_history_checkpoints,
    save_history_checkpoint,
)
from ..history.diff import diff_snapshots
from ..history.journal import (
    get_operation,
    list_operations,
    list_snapshots,
    load_snapshot,
    resolve_history_root,
    save_snapshot,
)
from ..history.models import HistoryOperationRecord, HistorySnapshot
from ..history.recovery import evaluate_interrupted_operation, reconcile_operation


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _dir_summary(cst_path: Path) -> dict[str, Any]:
    comp = _project_companion_dir(str(cst_path))
    file_count = 1 if cst_path.is_file() else 0
    total_size = cst_path.stat().st_size if cst_path.is_file() else 0
    if comp.is_dir():
        for root, _, files in os.walk(comp):
            for f in files:
                fp = Path(root) / f
                file_count += 1
                try:
                    total_size += fp.stat().st_size
                except OSError:
                    pass
    return {"file_count": file_count, "total_size_bytes": total_size}


def export_history_snapshot(
    project_path: str | None = None,
    *,
    reason: str = "manual_export",
    storage_root: Path | None = None,
) -> dict[str, Any]:
    """读取当前 CST 工程的真实 History 并持久化为快照。"""
    ctx = get_current_execution_context()
    target_path = project_path or ctx.get("project_path")
    if not target_path:
        cur = active_project()
        target_path = getattr(cur, "filename", None) if cur else None
    if not target_path:
        raise ValueError("需要提供 project_path 或确保存在活跃工程")

    norm_path = normalize_project_path(target_path)
    prj = get_open_project(str(norm_path))
    if prj is None:
        prj = open_project(str(norm_path))

    raw_data = get_raw_history(prj)
    caps = detect_history_capabilities(prj)
    snapshot = HistorySnapshot.from_raw_cst(
        raw_data,
        project_path=str(norm_path),
        cst_version=caps.get("cst_version"),
        reason=reason,
        operation_id=ctx.get("interaction_id"),
    )

    saved_file = save_snapshot(
        snapshot,
        storage_root=storage_root,
        project_path=str(norm_path),
    )

    return {
        "status": "success",
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_sha256": snapshot.snapshot_sha256,
        "block_count": len(snapshot.blocks),
        "snapshot_file": str(saved_file),
        "snapshot": snapshot.to_dict(),
    }


def diff_history_snapshots(
    before_snapshot_id: str,
    after_snapshot_id: str,
    *,
    project_path: str | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    """比对任意两个已保存的 History 快照并输出差异报告。"""
    root = storage_root or resolve_history_root(project_path=project_path)
    before = load_snapshot(before_snapshot_id, storage_root=root, project_path=project_path)
    if before is None:
        raise FileNotFoundError(f"找不到 before 快照: {before_snapshot_id}")

    after = load_snapshot(after_snapshot_id, storage_root=root, project_path=project_path)
    if after is None:
        raise FileNotFoundError(f"找不到 after 快照: {after_snapshot_id}")

    return diff_snapshots(before, after)


def list_history_log(
    *,
    project_path: str | None = None,
    execution_state: str | None = None,
    reconciliation_state: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查询操作历史流水。"""
    return list_operations(
        project_path=project_path,
        execution_state=execution_state,
        reconciliation_state=reconciliation_state,
        limit=limit,
    )


def plan_restore(
    baseline_project_path: str,
    target_snapshot_id: str,
    *,
    project_path: str | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    """纯只读分析基线与目标快照的前缀关系，生成恢复计划。"""
    norm_base = normalize_project_path(baseline_project_path)
    prj = get_open_project(str(norm_base))
    if prj is None:
        prj = open_project(str(norm_base))

    raw_base = get_raw_history(prj)
    caps = detect_history_capabilities(prj)
    baseline_snapshot = HistorySnapshot.from_raw_cst(
        raw_base,
        project_path=str(norm_base),
        cst_version=caps.get("cst_version"),
        reason="plan_baseline_check",
    )

    root = storage_root or resolve_history_root(project_path=project_path or str(norm_base))
    target_snapshot = load_snapshot(target_snapshot_id, storage_root=root, project_path=str(norm_base))
    if target_snapshot is None:
        raise FileNotFoundError(f"找不到目标快照: {target_snapshot_id}")

    ops_list = list_operations(storage_root=root, project_path=str(norm_base), limit=200)
    ops_records = [HistoryOperationRecord.from_dict(o) for o in ops_list]

    return generate_restore_plan(baseline_snapshot, target_snapshot, ops_records)


def inspect_capabilities(project_path: str | None = None) -> dict[str, Any]:
    """探测当前工程的 History 接口能力。"""
    if project_path:
        np = normalize_project_path(project_path)
        prj = get_open_project(str(np)) or open_project(str(np))
    else:
        prj = active_project()
    return detect_history_capabilities(prj)


def inspect_status(project_path: str | None = None) -> dict[str, Any]:
    """检查当前工程未完成或中断的操作。"""
    ops = list_history_log(project_path=project_path, limit=20)
    interrupted = [
        o for o in ops
        if o.get("execution_state") in ("pending", "submitted", "interrupted")
        and o.get("reconciliation_state") not in ("reconciled", "applied")
    ]
    return {
        "has_interrupted_operations": len(interrupted) > 0,
        "interrupted_count": len(interrupted),
        "interrupted_operations": interrupted,
        "recommendation": (
            "存在未闭合操作，请使用 evaluate/reconcile 工具处置。"
            if interrupted else "所有操作已正常闭合。"
        ),
    }


def create_checkpoint(
    checkpoint_name: str,
    description: str = "",
    project_path: str | None = None,
) -> dict[str, Any]:
    """创建轻量快照检查点。"""
    snap_res = export_history_snapshot(
        project_path=project_path,
        reason="create_checkpoint",
    )
    snapshot = HistorySnapshot.from_dict(snap_res["snapshot"])
    return save_history_checkpoint(
        snapshot,
        checkpoint_name=checkpoint_name,
        description=description,
        project_path=project_path,
    )


def create_physical_checkpoint(
    checkpoint_dir: str | Path,
    description: str = "",
    project_path: str | None = None,
) -> dict[str, Any]:
    """创建物理工程全量副本（.cst 与伴随目录）。"""
    p = project_path
    if not p:
        cur = active_project()
        p = getattr(cur, "filename", None) if cur else None
    if not p:
        raise ValueError("需要提供 project_path 或确保存在活跃工程")

    src_cst = Path(normalize_project_path(p))
    if not src_cst.is_file():
        raise FileNotFoundError(f"工程主文件不存在: {src_cst}")

    src_companion = _project_companion_dir(str(src_cst))
    dest_dir = Path(checkpoint_dir).expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_cst = dest_dir / src_cst.name
    dest_companion = dest_dir / src_companion.name

    save_res = save_project(str(src_cst))
    if save_res.get("status") == "error":
        code = save_res.get("code", "")
        msg = str(save_res.get("message", "")).lower()
        if code not in {"no_matching_project", "no_cst_sessions"} and "only python" not in msg and "not supported" not in msg and "cannot connect" not in msg:
            raise RuntimeError(f"物理检查点前保存工程失败: {save_res.get('message')}")

    wait_res = wait_project_unlocked(str(src_cst), timeout_seconds=10.0)
    if wait_res.get("status") != "success" or wait_res.get("locked") is True:
        raise TimeoutError(
            f"物理检查点锁文件等待超时或释放失败: {wait_res.get('message', 'locked')}, "
            f"锁文件: {wait_res.get('lock_files')}"
        )

    shutil.copy2(src_cst, dest_cst)
    if dest_companion.exists():
        shutil.rmtree(dest_companion)
    if src_companion.is_dir():
        shutil.copytree(src_companion, dest_companion)

    src_summary = _dir_summary(src_cst)
    dest_summary = _dir_summary(dest_cst)
    cst_sha256 = _file_sha256(dest_cst)

    from ..history.models import _now_iso
    manifest = {
        "created_at": _now_iso(),
        "source_project_path": str(src_cst),
        "checkpoint_project_path": str(dest_cst),
        "description": description.strip(),
        "cst_file_sha256": cst_sha256,
        "source_summary": src_summary,
        "checkpoint_summary": dest_summary,
    }

    manifest_file = dest_dir / "checkpoint_manifest.json"
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "checkpoint_cst_path": str(dest_cst),
        "checkpoint_companion_path": str(dest_companion) if src_companion.is_dir() else None,
        "manifest_file": str(manifest_file),
        "manifest": manifest,
    }


def checkout_and_replay_copy(
    baseline_project_path: str,
    target_snapshot: HistorySnapshot,
    new_copy_path: str,
    *,
    operations: list[HistoryOperationRecord] | Mapping[str, HistoryOperationRecord] | None = None,
) -> dict[str, Any]:
    """在新工程副本中，基于基线 History 与目标快照的严格前缀差异逐步重放业务 VBA。"""
    src_cst = Path(normalize_project_path(baseline_project_path))
    if not src_cst.is_file():
        raise FileNotFoundError(f"基线工程不存在: {src_cst}")

    dest_cst = Path(normalize_project_path(new_copy_path))
    if dest_cst.exists():
        raise FileExistsError(f"目标重放工程路径已存在，请指定一个新路径: {dest_cst}")

    dest_dir = dest_cst.parent
    dest_dir.mkdir(parents=True, exist_ok=True)

    base_prj, _ = attach_expected_project(str(src_cst))
    if base_prj is None:
        open_res = open_project(str(src_cst))
        if open_res.get("status") != "success":
            raise RuntimeError(f"打开基线工程失败: {open_res.get('message')}")
        base_prj, _ = attach_expected_project(str(src_cst))
    if base_prj is None:
        base_prj = active_project()

    raw_base = get_raw_history(base_prj)
    baseline_snapshot = HistorySnapshot.from_raw_cst(
        raw_base,
        project_path=str(src_cst),
        reason="checkout_baseline_check",
    )

    plan = generate_restore_plan(baseline_snapshot, target_snapshot, operations)
    if not plan.get("can_execute"):
        return {
            "status": "error",
            "error_type": "restore_plan_unexecutable",
            "message": plan.get("message", "恢复计划无法执行"),
            "plan": plan,
        }

    src_companion = _project_companion_dir(str(src_cst))
    dest_companion = _project_companion_dir(str(dest_cst))

    save_res = save_project(str(src_cst))
    if save_res.get("status") == "error":
        code = save_res.get("code", "")
        msg = str(save_res.get("message", "")).lower()
        if code not in {"no_matching_project", "no_cst_sessions"} and "only python" not in msg and "not supported" not in msg and "cannot connect" not in msg:
            raise RuntimeError(f"保存基线工程失败: {save_res.get('message')}")

    wait_res = wait_project_unlocked(str(src_cst), timeout_seconds=10.0)
    if wait_res.get("status") != "success" or wait_res.get("locked") is True:
        raise TimeoutError(f"基线工程锁释放失败: {wait_res.get('message', 'locked')}")

    shutil.copy2(src_cst, dest_cst)
    if src_companion.is_dir():
        shutil.copytree(src_companion, dest_companion)

    open_replay_res = open_project(str(dest_cst))
    if open_replay_res.get("status") != "success":
        raise RuntimeError(f"打开重放工程副本失败: {open_replay_res.get('message')}")
    replay_prj = get_open_project(str(dest_cst)) or active_project()
    activate_project(replay_prj)

    replayed_steps: list[dict[str, Any]] = []
    steps = plan.get("steps", [])

    try:
        for step in steps:
            step_num = step["step"]
            label = step["label"]
            business_vba = step["business_vba"]
            expected_before = step.get("expected_before_snapshot_sha256")
            expected_after = step.get("expected_after_snapshot_sha256")

            raw_curr = get_raw_history(replay_prj)
            curr_snapshot = HistorySnapshot.from_raw_cst(
                raw_curr,
                project_path=str(dest_cst),
                reason=f"step_{step_num}_before_check",
            )

            if expected_before and curr_snapshot.snapshot_sha256 != expected_before:
                return {
                    "status": "error",
                    "error_type": "before_hash_mismatch",
                    "message": (
                        f"步骤 {step_num} [{label}] 前置快照哈希不匹配！"
                        f"期望 {expected_before}，实际 {curr_snapshot.snapshot_sha256}。"
                        "为防止几何冲突，已立即停止重放，故障副本现场已保留。"
                    ),
                    "new_copy_path": str(dest_cst),
                    "failed_step": step,
                    "replayed_steps": replayed_steps,
                }

            submit_res = submit_vba_history(
                replay_prj,
                label,
                business_vba.splitlines() if isinstance(business_vba, str) else business_vba,
                project_path=str(dest_cst),
                operation_id=step.get("operation_id"),
            )

            if submit_res.get("status") != "success":
                return {
                    "status": "error",
                    "error_type": "vba_submission_failed",
                    "message": f"步骤 {step_num} [{label}] VBA 提交执行失败: {submit_res.get('message')}",
                    "new_copy_path": str(dest_cst),
                    "failed_step": step,
                    "replayed_steps": replayed_steps,
                    "error_details": submit_res,
                }

            raw_after = get_raw_history(replay_prj)
            after_snapshot = HistorySnapshot.from_raw_cst(
                raw_after,
                project_path=str(dest_cst),
                reason=f"step_{step_num}_after_check",
            )

            if expected_after and after_snapshot.snapshot_sha256 != expected_after:
                return {
                    "status": "error",
                    "error_type": "after_hash_mismatch",
                    "message": (
                        f"步骤 {step_num} [{label}] 后置快照哈希不匹配！"
                        f"期望 {expected_after}，实际 {after_snapshot.snapshot_sha256}。"
                        "重放已被强制终止，故障副本现场已保留。"
                    ),
                    "new_copy_path": str(dest_cst),
                    "failed_step": step,
                    "replayed_steps": replayed_steps,
                }

            replayed_steps.append({
                "step": step_num,
                "label": label,
                "before_sha256": curr_snapshot.snapshot_sha256,
                "after_sha256": after_snapshot.snapshot_sha256,
                "operation_id": submit_res.get("operation_id"),
            })

        save_res = save_project(str(dest_cst))
        if save_res.get("status") != "success":
            raise RuntimeError(f"保存重放后的工程副本失败: {save_res.get('message')}")

        final_raw = get_raw_history(replay_prj)
        final_snapshot = HistorySnapshot.from_raw_cst(
            final_raw,
            project_path=str(dest_cst),
            reason="checkout_replay_completed",
        )

        return {
            "status": "success",
            "message": f"成功在隔离副本中完成 {len(replayed_steps)} 个步骤的严格前缀重放。",
            "new_copy_path": str(dest_cst),
            "replayed_steps_count": len(replayed_steps),
            "replayed_steps": replayed_steps,
            "final_snapshot_sha256": final_snapshot.snapshot_sha256,
            "final_block_count": len(final_snapshot.blocks),
        }

    except Exception as exc:
        return {
            "status": "error",
            "error_type": "replay_execution_exception",
            "message": f"重放执行过程中发生异常: {exc}；副本已保留在 {dest_cst}。",
            "new_copy_path": str(dest_cst),
            "replayed_steps": replayed_steps,
        }


def replay_to_copy(
    baseline_project_path: str,
    target_snapshot_id: str,
    new_copy_path: str,
    *,
    project_path: str | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    """在新副本中逐步重放至目标快照。"""
    root = storage_root or resolve_history_root(project_path=project_path or baseline_project_path)
    target_snap = load_snapshot(target_snapshot_id, storage_root=root, project_path=baseline_project_path)
    if target_snap is None:
        raise FileNotFoundError(f"找不到目标快照: {target_snapshot_id}")

    ops_list = list_operations(storage_root=root, project_path=baseline_project_path, limit=200)
    ops_records = [HistoryOperationRecord.from_dict(o) for o in ops_list]

    return checkout_and_replay_copy(
        baseline_project_path=baseline_project_path,
        target_snapshot=target_snap,
        new_copy_path=new_copy_path,
        operations=ops_records,
    )
