"""solver_diagnostics 求解日志诊断通道的单元测试。"""
from __future__ import annotations

import os
import time

from cst_runtime.core.solver_diagnostics import (
    _extract_error_blocks,
    capture_solver_log_baseline,
    read_appended_solver_logs,
    solver_log_files,
)

# 真实失败现场的日志文本（tasks/task_cp_patch_boolean_20260809 的 Model.log）
REAL_ERROR_LOG = """\
13/Aug/2026 23:08:30  Defined reference frequency for open boundary condition (2.45 GHz) is larger
                      than the lowest relevant system frequency (monitor at 2.4 GHz).
                      Please check open boundary settings to ensure accurate monitor results for the
                      lowest frequency of interest.

                      ------------------------------------------------------------------------------
13/Aug/2026 23:08:30  *** Error ***

                      Farfield monitors are not supported with pec, dispersive, lossy or surface
                      impedance as background material.

                      ------------------------------------------------------------------------------
"""

WARNING_ONLY_LOG = """\
13/Aug/2026 23:08:30  Defined reference frequency for open boundary condition (2.45 GHz) is larger
                      than the lowest relevant system frequency (monitor at 2.4 GHz).
                      Please check open boundary settings to ensure accurate monitor results for the
                      lowest frequency of interest.

                      ------------------------------------------------------------------------------
"""


def _write_model_log(tmp_path, text: str, encoding: str = "utf-8") -> str:
    project = tmp_path / "working.cst"
    result_dir = tmp_path / "working" / "Result"
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "Model.log").write_text(text, encoding=encoding)
    return str(project)


def test_solver_log_files_lists_result_logs(tmp_path):
    project = _write_model_log(tmp_path, "x")
    paths = solver_log_files(project)
    assert len(paths) == 1
    assert paths[0].name == "Model.log"
    assert paths[0].parent.name == "Result"


def test_solver_log_files_missing_companion_returns_empty(tmp_path):
    assert solver_log_files(str(tmp_path / "missing.cst")) == []


def test_extract_error_blocks_from_real_fixture():
    blocks = _extract_error_blocks(REAL_ERROR_LOG)
    assert len(blocks) == 1
    joined = "\n".join(blocks)
    assert "*** Error ***" in joined
    assert "Farfield monitors are not supported with pec, dispersive, lossy or surface" in joined
    # 缩进的 ---- 分隔线属于块边界，不应混入错误文本
    assert "-----" not in blocks[0]


def test_extract_error_blocks_ignores_warnings_only():
    assert _extract_error_blocks(WARNING_ONLY_LOG) == []


def test_extract_error_line_marker_fallback():
    text = "13/Aug/2026 23:08:30  1 error occurred."
    blocks = _extract_error_blocks(text)
    assert blocks == ["13/Aug/2026 23:08:30  1 error occurred."]


def test_extract_error_line_marker_ignores_zero_errors():
    assert _extract_error_blocks("13/Aug/2026 23:08:30  0 errors occurred.") == []


def test_baseline_incremental_only_reads_appended(tmp_path):
    project = _write_model_log(tmp_path, WARNING_ONLY_LOG)
    baseline = capture_solver_log_baseline(project)
    assert len(baseline) == 1

    # 基线之后没有新增内容 → 不报错误
    result = read_appended_solver_logs(project, baseline=baseline)
    assert result["errors"] == []

    # 追加一个错误块 → 只报新错误
    with open(list(baseline)[0], "ab") as file_handle:
        file_handle.write(REAL_ERROR_LOG.encode("utf-8"))
    result = read_appended_solver_logs(project, baseline=baseline)
    assert len(result["errors"]) == 1
    assert "Farfield monitors are not supported" in result["errors"][0]
    assert any("Farfield monitors" in line for line in result["error_lines"])
    assert list(result["log_tails"]) == list(baseline)


def test_shrunk_file_treated_as_fully_new(tmp_path):
    project = _write_model_log(tmp_path, REAL_ERROR_LOG)
    bogus_baseline = {list(capture_solver_log_baseline(project))[0]: 10 ** 6}
    result = read_appended_solver_logs(project, baseline=bogus_baseline)
    assert len(result["errors"]) == 1


def test_since_filters_stale_logs(tmp_path):
    project = _write_model_log(tmp_path, REAL_ERROR_LOG)
    log_path = list(capture_solver_log_baseline(project))[0]
    past = time.time() - 3600
    os.utime(log_path, (past, past))

    result = read_appended_solver_logs(project, baseline=None, since=time.time())
    assert result["errors"] == []

    os.utime(log_path, (time.time(), time.time()))
    result = read_appended_solver_logs(project, baseline=None, since=time.time() - 10)
    assert len(result["errors"]) == 1


def test_utf16_log_decodes(tmp_path):
    project = _write_model_log(tmp_path, REAL_ERROR_LOG, encoding="utf-16")
    result = read_appended_solver_logs(project)
    assert len(result["errors"]) == 1


def test_missing_result_dir_is_empty(tmp_path):
    result = read_appended_solver_logs(str(tmp_path / "noop.cst"))
    assert result["errors"] == []
    assert result["log_files"] == []
    assert result["log_tails"] == {}
