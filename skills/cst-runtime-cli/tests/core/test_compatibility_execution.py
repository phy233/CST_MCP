"""compatibility/execution.py 离线契约测试（不连接 CST）。"""
from __future__ import annotations

from pathlib import Path

import pytest

from cst_runtime.core.compatibility import execution
from cst_runtime.core.compatibility.base import CompatibilityProfile
from cst_runtime.core.errors import CSTSubmissionError


class _FakeSchematic:
    """按表达式字典写入探测结果文件；未命中的表达式不生成文件。"""

    def __init__(self, outcomes: dict[str, Path] | None = None) -> None:
        self.outcomes = outcomes or {}
        self.scripts: list[str] = []

    def execute_vba_code(self, macro: str) -> None:
        self.scripts.append(macro)
        expression = ""
        output_path = ""
        for line in macro.splitlines():
            if "cstRtTempPath = " in line:
                expression = line.split("cstRtTempPath = ", 1)[1].strip()
            if line.startswith('Open "') and '" For Output' in line:
                output_path = line.split('"', 2)[1]
        if expression not in self.outcomes or not output_path:
            return
        Path(output_path).write_text(str(self.outcomes[expression]), encoding="utf-8")


class _FakeProject:
    def __init__(self, schematic: _FakeSchematic) -> None:
        self.schematic = schematic


@pytest.fixture(autouse=True)
def _clear_temp_expression_cache():
    """execution 的 Temp 表达式缓存是模块级状态，逐测试隔离。"""
    execution._TEMP_EXPRESSION_CACHE.clear()
    yield
    execution._TEMP_EXPRESSION_CACHE.clear()


def test_execute_text_query_reads_generated_file(monkeypatch) -> None:
    def fake_execute(_project, body: list[str]) -> None:
        for line in body:
            if line.startswith('Open "') and '" For Output' in line:
                Path(line.split('"', 2)[1]).write_text("alpha\nbeta", encoding="utf-8")
                return

    monkeypatch.setattr(execution, "execute_immediate_vba", fake_execute)

    result = execution.execute_text_query(object(), ['Print #cstRtQueryFile, "x"'])

    assert result == ["alpha", "beta"]


def test_execute_text_query_times_out_when_file_missing(monkeypatch) -> None:
    monkeypatch.setattr(execution, "execute_immediate_vba", lambda _project, _body: None)

    with pytest.raises(CSTSubmissionError, match="没有生成查询结果文件"):
        execution.execute_text_query(object(), [], timeout=0.05)


def test_temp_context_unknown_profile_probes_modern_first(monkeypatch, tmp_path: Path) -> None:
    unknown = CompatibilityProfile(major=0, version="unknown", source="test")
    monkeypatch.setattr(execution, "profile_for", lambda _project: unknown)
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    schematic = _FakeSchematic({'GetProjectPathName("Temp")': temp_dir})

    resolved, expression = execution.resolve_cst_temp_context(
        _FakeProject(schematic), "model.cst"
    )

    assert resolved == temp_dir.resolve()
    assert expression == 'GetProjectPathName("Temp")'
    assert any('GetProjectPathName("Temp")' in script for script in schematic.scripts)


def test_temp_context_falls_back_to_legacy_expression(monkeypatch, tmp_path: Path) -> None:
    unknown = CompatibilityProfile(major=0, version="unknown", source="test")
    monkeypatch.setattr(execution, "profile_for", lambda _project: unknown)
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    schematic = _FakeSchematic({'GetProjectPath("Temp")': temp_dir})

    resolved, expression = execution.resolve_cst_temp_context(
        _FakeProject(schematic), "model.cst"
    )

    assert resolved == temp_dir.resolve()
    assert expression == 'GetProjectPath("Temp")'
    assert any('GetProjectPath("Temp")' in script for script in schematic.scripts)


def test_temp_context_reports_all_probe_failures(monkeypatch, tmp_path: Path) -> None:
    unknown = CompatibilityProfile(major=0, version="unknown", source="test")
    monkeypatch.setattr(execution, "profile_for", lambda _project: unknown)
    schematic = _FakeSchematic({})

    with pytest.raises(CSTSubmissionError, match="无法验证") as caught:
        execution.resolve_cst_temp_context(
            _FakeProject(schematic), "model.cst", timeout=0.05
        )

    failures = caught.value.context["probe_failures"]
    assert len(failures) == 2
    assert all("未生成探测文件" in item for item in failures)
