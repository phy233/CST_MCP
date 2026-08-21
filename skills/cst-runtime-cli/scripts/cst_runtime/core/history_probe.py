"""CST 2022 私有 History 导出能力的最小真机探针。"""
from __future__ import annotations

import difflib
import json
from pathlib import Path
from typing import Any

from .error_gateway import submit_vba_history
from .identity import attach_expected_project


def _history_text(value: Any) -> str:
    """把私有接口返回值稳定转换成可保存、可比较的文本。"""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _error(error_type: str, message: str, **context: Any) -> dict[str, Any]:
    """返回与 Worker 统一信封兼容的实验错误。"""
    return {
        "ok": False,
        "status": "error",
        "error_type": error_type,
        "message": message,
        "error": {
            "type": error_type,
            "message": message,
            "phase": "runtime",
        },
        "context": context,
    }


def run_cst2022_history_export_probe(
    project_path: str,
    evidence_dir: str,
    marker: str,
) -> dict[str, Any]:
    """在已打开的隔离工程中比较提交 VBA 前后的 ``_GetHistory``。

    该函数只执行固定的 ``StoreParameter`` 指令，不提供任意 VBA 入口，也不调用
    ``_ResizeHistory``、``_TryToUndoNTimes`` 或保存工程。
    """
    normalized_marker = "".join(character for character in marker if character.isalnum() or character == "_")
    if not normalized_marker or normalized_marker != marker:
        return _error(
            "invalid_history_probe_marker",
            "History 探针标记只能包含字母、数字和下划线。",
            marker=marker,
        )

    project_file = Path(project_path).expanduser().resolve()
    output_dir = Path(evidence_dir).expanduser().resolve()
    project, attach_status = attach_expected_project(str(project_file))
    if project is None:
        return _error(
            "history_probe_attach_failed",
            "无法附着到指定的 CST 工程。",
            project_path=str(project_file),
            attach_status=attach_status,
        )

    modeler = project.modeler
    get_history = getattr(modeler, "_GetHistory", None)
    if not callable(get_history):
        return _error(
            "private_get_history_unavailable",
            "当前 CST Modeler 没有可调用的 _GetHistory。",
            project_path=str(project_file),
        )

    output_dir.mkdir(parents=True, exist_ok=False)
    before_raw = get_history()
    before_text = _history_text(before_raw)
    before_path = output_dir / "history_before.txt"
    before_path.write_text(before_text, encoding="utf-8")

    history_label = f"CST Runtime History Export Probe {normalized_marker}"
    parameter_name = f"cst_runtime_history_probe_{normalized_marker}"
    business_vba = f'StoreParameter "{parameter_name}", "1"'
    submission = submit_vba_history(
        project,
        history_label,
        [business_vba],
        project_path=str(project_file),
        feature="diagnostics.private_history_export_probe",
        operation_id=normalized_marker,
    )

    if submission.get("status") != "success":
        report = {
            "status": "error",
            "project_path": str(project_file),
            "history_method": "_GetHistory",
            "history_before_type": type(before_raw).__name__,
            "history_before_length": len(before_text),
            "history_label": history_label,
            "business_vba": business_vba,
            "submission": submission,
            "forbidden_methods_called": [],
        }
        report_path = output_dir / "history_probe_report.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        return _error(
            "history_probe_submission_failed",
            "最小 History VBA 提交失败。",
            report_path=str(report_path),
            submission=submission,
        )

    after_raw = get_history()
    after_text = _history_text(after_raw)
    after_path = output_dir / "history_after.txt"
    diff_path = output_dir / "history.diff"
    after_path.write_text(after_text, encoding="utf-8")
    history_diff = "".join(
        difflib.unified_diff(
            before_text.splitlines(keepends=True),
            after_text.splitlines(keepends=True),
            fromfile="history_before.txt",
            tofile="history_after.txt",
        )
    )
    diff_path.write_text(history_diff, encoding="utf-8")

    observations = {
        "history_changed": before_text != after_text,
        "history_label_present_after": history_label in after_text,
        "business_vba_present_after": business_vba in after_text,
        "marker_present_before": normalized_marker in before_text,
        "marker_present_after": normalized_marker in after_text,
    }
    report = {
        "status": "success",
        "project_path": str(project_file),
        "history_method": "_GetHistory",
        "history_before_type": type(before_raw).__name__,
        "history_after_type": type(after_raw).__name__,
        "history_before_length": len(before_text),
        "history_after_length": len(after_text),
        "history_label": history_label,
        "business_vba": business_vba,
        "submission": submission,
        "observations": observations,
        "forbidden_methods_called": [],
        "saved_project": False,
        "evidence": {
            "history_before": str(before_path),
            "history_after": str(after_path),
            "history_diff": str(diff_path),
        },
    }
    report_path = output_dir / "history_probe_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "status": "success",
        "project_path": str(project_file),
        "report_path": str(report_path),
        "evidence_dir": str(output_dir),
        "observations": observations,
        "history_before_length": len(before_text),
        "history_after_length": len(after_text),
        "history_before_type": type(before_raw).__name__,
        "history_after_type": type(after_raw).__name__,
        "submission": submission,
    }
