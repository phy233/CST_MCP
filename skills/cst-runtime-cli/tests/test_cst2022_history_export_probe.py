"""CST 2022 ``_GetHistory`` 最小真机实验。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


pytestmark = [
    pytest.mark.cst_integration,
    pytest.mark.cst_destructive,
]


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_private_get_history_exports_new_history_vba(cst_case: Any) -> None:
    """提交固定参数指令后，私有接口应导出包含新增 VBA 的线性 History。"""
    marker = cst_case.name("history_export")
    evidence_dir = (
        REPO_ROOT
        / ".cst_runtime"
        / "evidence"
        / f"cst2022-history-export-{marker}"
    )
    assert Path(cst_case.project_path).resolve() != cst_case.shared.source_path.resolve()

    result = cst_case.shared.proxy.request(
        "_test_cst2022_history_export_probe",
        timeout=60,
        project_path=cst_case.project_path,
        evidence_dir=str(evidence_dir),
        marker=marker,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str), flush=True)

    assert result.get("status") == "success", result
    assert result.get("ok") is True, result
    assert result["submission"]["execution"] == "reported_ok", result
    assert result["history_before_type"] == result["history_after_type"], result
    assert result["observations"] == {
        "history_changed": True,
        "history_label_present_after": True,
        "business_vba_present_after": True,
        "marker_present_before": False,
        "marker_present_after": True,
    }, result

    report_path = Path(result["report_path"])
    assert report_path.is_file(), result
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["forbidden_methods_called"] == []
    assert report["saved_project"] is False
    for evidence_path in report["evidence"].values():
        assert Path(evidence_path).is_file(), report
    cst_case.shared.require_visible_window()
