from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path

import pytest

from cst_runtime.core.error_gateway import (
    parse_vba_status,
    resolve_cst_temp_directory,
    submit_vba_history,
    wait_for_vba_status,
    wrap_vba_with_status_channel,
)
from cst_runtime.core.errors import (
    CSTSubmissionError,
    VBACompileOrHostError,
    VBARuntimeError,
    error_response,
    normalize_response,
)


class _FakeModeler:
    def __init__(self, callback):
        self.callback = callback
        self.calls = []

    def add_to_history(self, history_label, script):
        self.calls.append((history_label, script))
        return self.callback(history_label, script)


class _FakeProject:
    def __init__(self, callback):
        self.modeler = _FakeModeler(callback)


def test_error_envelope_is_json_serializable_and_legacy_compatible(tmp_path: Path) -> None:
    result = error_response(
        "verification_failed",
        "brick was not created",
        feature="geometry.brick",
        project_path=tmp_path / "model.cst",
        cst_raw={"expected": {"component1:brick"}},
    )

    round_trip = json.loads(json.dumps(result, ensure_ascii=False))

    assert round_trip["ok"] is False
    assert round_trip["status"] == "error"
    assert round_trip["error_type"] == "verification_failed"
    assert round_trip["error"]["phase"] == "verification"
    assert round_trip["context"]["project_path"].endswith("model.cst")
    assert round_trip["context"]["cst_raw"]["expected"] == ["component1:brick"]


def test_structured_exception_preserves_details() -> None:
    result = VBARuntimeError(
        "Material does not exist.",
        code=1004,
        source="Brick.Create",
        line=120,
        feature="geometry.brick",
    ).to_response(operation_id="op-1")

    assert result["error_type"] == "vba_runtime_error"
    assert result["error"] == {
        "type": "vba_runtime_error",
        "message": "Material does not exist.",
        "phase": "execution",
        "code": 1004,
        "source": "Brick.Create",
        "line": 120,
        "feature": "geometry.brick",
    }
    assert result["context"]["operation_id"] == "op-1"


def test_normalize_legacy_error_and_success() -> None:
    error = normalize_response(
        {"status": "error", "error_type": "invalid_arguments", "message": "missing name"}
    )
    success = normalize_response({"status": "success", "value": 3})

    assert error["ok"] is False
    assert error["error"]["phase"] == "validation"
    assert success["ok"] is True
    assert success["submission"] == "not_applicable"
    assert success["verification"] == "not_run"


def test_parse_ok_status(tmp_path: Path) -> None:
    status_path = tmp_path / "ok.status"
    status_path.write_text("OK\r\n", encoding="utf-8")

    status = parse_vba_status(status_path)

    assert status.state == "ok"


def test_parse_runtime_error_status(tmp_path: Path) -> None:
    status_path = tmp_path / "error.status"
    status_path.write_text(
        "ERROR\n1004\nBrick.Create\nMaterial does not exist.\n120\n",
        encoding="utf-8",
    )

    with pytest.raises(VBARuntimeError) as caught:
        parse_vba_status(status_path)

    assert caught.value.code == 1004
    assert caught.value.source == "Brick.Create"
    assert caught.value.line == 120
    assert str(caught.value) == "Material does not exist."


@pytest.mark.parametrize("content", [None, "", "ERROR\n1004\nsource\n"])
def test_missing_or_malformed_status_is_never_success(tmp_path: Path, content: str | None) -> None:
    status_path = tmp_path / "missing-or-broken.status"
    if content is not None:
        status_path.write_text(content, encoding="utf-8")

    with pytest.raises(VBACompileOrHostError) as caught:
        parse_vba_status(status_path)

    assert caught.value.error_type == "vba_compile_or_host_error"
    assert caught.value.context["status_state"] in {"missing", "malformed"}


def test_wrapper_contains_runtime_error_channel(tmp_path: Path) -> None:
    wrapped = wrap_vba_with_status_channel(
        'With Brick\n.Name "demo"\n.Create\nEnd With',
        "operation.status",
        "operation.arm",
        "operation-123",
        status_directory_expression='GetProjectPathName("Temp")',
    )

    assert "On Error GoTo CSTRuntimeErroroperation123" in wrapped
    assert 'Print #cstRtoperation123FileNumber, "OK"' in wrapped
    assert 'Print #cstRtoperation123FileNumber, "ERROR"' in wrapped
    assert 'GetProjectPathName("Temp") & "\\operation.status"' in wrapped
    assert "C:/" not in wrapped
    assert "If cstRtoperation123Armed Then" in wrapped
    assert "Then Kill cstRtoperation123ArmFile" in wrapped
    assert (
        "If Not cstRtoperation123Armed Then "
        "ReportError cstRtoperation123ErrorDescription"
    ) in wrapped
    assert "Err.Raise" not in wrapped
    assert "Err.Source" not in wrapped
    assert "Erl" not in wrapped


def test_gateway_reports_ok_and_removes_status_file(tmp_path: Path) -> None:
    status_path = tmp_path / "cst-runtime-opok.status"

    def write_ok(_label, _script):
        status_path.write_text("OK\n", encoding="utf-8")
        return True

    project = _FakeProject(write_ok)
    result = submit_vba_history(
        project,
        "Define Brick:demo",
        ["With Brick", "End With"],
        project_path="C:/model.cst",
        operation_id="op-ok",
        _status_directory=tmp_path,
    )

    assert result["ok"] is True
    assert result["submission"] == "accepted"
    assert result["execution"] == "reported_ok"
    assert result["verification"] == "not_run"
    assert not status_path.exists()


def test_gateway_reports_runtime_error(tmp_path: Path) -> None:
    status_path = tmp_path / "cst-runtime-operror.status"

    def write_error(_label, _script):
        status_path.write_text(
            "ERROR\n1004\nBrick.Create\nMaterial does not exist.\n0\n",
            encoding="utf-8",
        )
        return True

    result = submit_vba_history(
        _FakeProject(write_error),
        "Define Brick:demo",
        ['.Material "missing"'],
        project_path="C:/model.cst",
        operation_id="op-error",
        _status_directory=tmp_path,
    )

    assert result["ok"] is False
    assert result["error_type"] == "vba_runtime_error"
    assert "vba_script" not in result["context"]


def test_gateway_prefers_runtime_status_when_cst_returns_false(tmp_path: Path) -> None:
    status_path = tmp_path / "cst-runtime-opfalse.status"

    def write_error_and_return_false(_label, _script):
        status_path.write_text(
            "ERROR\n5\n\nCST 2022 ReportError\n0\n",
            encoding="utf-8",
        )
        return False

    result = submit_vba_history(
        _FakeProject(write_error_and_return_false),
        "ReportError",
        ['ReportError "CST 2022 ReportError"'],
        project_path="C:/model.cst",
        operation_id="op-false",
        _status_directory=tmp_path,
    )

    assert result["error_type"] == "vba_runtime_error"
    assert result["message"] == "CST 2022 ReportError"


def test_gateway_treats_missing_status_as_compile_or_host_error(tmp_path: Path) -> None:
    result = submit_vba_history(
        _FakeProject(lambda _label, _script: True),
        "Broken syntax",
        ["This Is Not VBA"],
        project_path="C:/model.cst",
        operation_id="op-missing",
        status_timeout=0,
        _status_directory=tmp_path,
    )

    assert result["ok"] is False
    assert result["error_type"] == "vba_compile_or_host_error"
    assert result["error"]["phase"] == "execution"
    assert result["context"]["vba_script"] == "This Is Not VBA"


def test_gateway_classifies_com_exception_as_submission_error(tmp_path: Path) -> None:
    def fail_submission(_label, _script):
        raise RuntimeError("COM disconnected")

    result = submit_vba_history(
        _FakeProject(fail_submission),
        "Define Brick:demo",
        ["With Brick", "End With"],
        project_path="C:/model.cst",
        _status_directory=tmp_path,
    )

    assert result["error_type"] == CSTSubmissionError.error_type
    assert result["error"]["phase"] == "submission"


def test_gateway_converts_temp_probe_exception_to_submission_error(monkeypatch) -> None:
    def fail_probe(*args, **kwargs):
        raise CSTSubmissionError("temp probe failed")

    monkeypatch.setattr(
        "cst_runtime.core.error_gateway.resolve_cst_temp_context",
        fail_probe,
    )

    result = submit_vba_history(
        _FakeProject(lambda _label, _script: True),
        "Probe failure",
        ["With Brick", "End With"],
        project_path="C:/model.cst",
    )

    assert result["ok"] is False
    assert result["error_type"] == "cst_submission_error"
    assert result["error"]["phase"] == "submission"


def test_wait_accepts_delayed_status_write(tmp_path: Path) -> None:
    status_path = tmp_path / "delayed.status"

    def delayed_write():
        time.sleep(0.03)
        status_path.write_text("OK\n", encoding="utf-8")

    thread = threading.Thread(target=delayed_write)
    thread.start()
    try:
        assert wait_for_vba_status(status_path, timeout=1, poll_interval=0.005).state == "ok"
    finally:
        thread.join()


def test_gateway_prefers_written_runtime_error_when_com_also_raises(tmp_path: Path) -> None:
    status_path = tmp_path / "cst-runtime-opraise.status"

    def write_then_raise(_label, _script):
        status_path.write_text("ERROR\n5\nTest\nraised in VBA\n0\n", encoding="utf-8")
        raise RuntimeError("COM surfaced VBA failure")

    result = submit_vba_history(
        _FakeProject(write_then_raise),
        "Raise",
        ['ReportError "raised in VBA"'],
        project_path="C:/model.cst",
        operation_id="op-raise",
        _status_directory=tmp_path,
    )

    assert result["error_type"] == "vba_runtime_error"
    assert result["message"] == "raised in VBA"


def test_gateway_refuses_stale_status_collision(tmp_path: Path) -> None:
    status_path = tmp_path / "cst-runtime-stale.status"
    status_path.write_text("OK\n", encoding="utf-8")

    result = submit_vba_history(
        _FakeProject(lambda _label, _script: True),
        "Stale",
        ["With Brick", "End With"],
        project_path="C:/model.cst",
        operation_id="stale",
        _status_directory=tmp_path,
    )

    assert result["error_type"] == "cst_submission_error"
    assert status_path.read_text(encoding="utf-8").strip() == "OK"


def test_cst_temp_probe_matches_history_directory_expression(tmp_path: Path) -> None:
    class FakeSchematic:
        def __init__(self):
            self.macro = ""

        def execute_vba_code(self, macro):
            self.macro = macro
            match = re.search(r'Open "([^"]+)" For Output', macro)
            assert match is not None
            Path(match.group(1)).write_text(str(tmp_path), encoding="utf-8")

    project = _FakeProject(lambda _label, _script: True)
    project.schematic = FakeSchematic()
    project_path = "C:/probe-contract.cst"

    resolved = resolve_cst_temp_directory(project, project_path)
    wrapped = wrap_vba_with_status_channel(
        "business command",
        "probe.status",
        "probe.arm",
        "probe",
        status_directory_expression='GetProjectPathName("Temp")',
    )

    assert resolved == tmp_path.resolve()
    assert 'cstRtTempPath = GetProjectPathName("Temp")' in project.schematic.macro
    assert "Print #cstRtProbeFile, cstRtTempPath" in project.schematic.macro
    assert 'Print #cstRtProbeFile, GetProjectPathName("Temp")' not in project.schematic.macro
    assert 'GetProjectPathName("Temp") & "\\probe.status"' in wrapped


def test_cst_2022_temp_probe_uses_legacy_expression(monkeypatch, tmp_path: Path) -> None:
    class FakeSchematic:
        def __init__(self):
            self.macro = ""

        def execute_vba_code(self, macro):
            self.macro = macro
            match = re.search(r'Open "([^"]+)" For Output', macro)
            assert match is not None
            Path(match.group(1)).write_text(str(tmp_path), encoding="utf-8")

    project = _FakeProject(lambda _label, _script: True)
    project.schematic = FakeSchematic()
    monkeypatch.setattr(
        "cst_runtime.core.compatibility.execution.profile_for",
        lambda _project: __import__(
            "cst_runtime.core.compatibility.base",
            fromlist=["CompatibilityProfile"],
        ).CompatibilityProfile(major=2022, version="2022", source="test"),
    )

    resolved = resolve_cst_temp_directory(project, "C:/legacy.cst")

    assert resolved == tmp_path.resolve()
    assert 'cstRtTempPath = GetProjectPath("Temp")' in project.schematic.macro
    assert "GetProjectPathName" not in project.schematic.macro


def test_cst_temp_probe_is_repeated_for_reopened_project(tmp_path: Path) -> None:
    first_temp = tmp_path / "first"
    second_temp = tmp_path / "second"
    first_temp.mkdir()
    second_temp.mkdir()

    class FakeSchematic:
        def __init__(self, reported_path: Path):
            self.reported_path = reported_path
            self.calls = 0

        def execute_vba_code(self, macro):
            self.calls += 1
            match = re.search(r'Open "([^"]+)" For Output', macro)
            assert match is not None
            Path(match.group(1)).write_text(str(self.reported_path), encoding="utf-8")

    first_project = _FakeProject(lambda _label, _script: True)
    first_project.schematic = FakeSchematic(first_temp)
    second_project = _FakeProject(lambda _label, _script: True)
    second_project.schematic = FakeSchematic(second_temp)

    first = resolve_cst_temp_directory(first_project, "C:/same-project.cst")
    second = resolve_cst_temp_directory(second_project, "C:/same-project.cst")

    assert first == first_temp.resolve()
    assert second == second_temp.resolve()
    assert first_project.schematic.calls == 1
    assert second_project.schematic.calls == 1
