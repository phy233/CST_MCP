"""Manual CST 2022 acceptance cases for the VBA Error Gateway.

These tests are intentionally disabled unless the operator supplies both a
source project and an explicit opt-in. They must run serially on a disposable
copy because the History/Undo observation is exploratory and destructive.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest


pytestmark = [
    pytest.mark.cst_integration,
    pytest.mark.cst_destructive,
    pytest.mark.skipif(
        os.environ.get("CST_RUN_ERROR_GATEWAY_TESTS") != "1",
        reason="set CST_RUN_ERROR_GATEWAY_TESTS=1 for manual CST 2022 acceptance",
    ),
]


@pytest.fixture
def disposable_cst_project(tmp_path: Path):
    source_value = os.environ.get("CST_TEST_PROJECT")
    if not source_value:
        pytest.skip("set CST_TEST_PROJECT to a disposable-compatible .cst source")

    from cst_runtime.lib.session import close_project, open_project

    source = Path(source_value).expanduser().resolve()
    if not source.is_file():
        pytest.skip(f"CST_TEST_PROJECT does not exist: {source}")
    working = tmp_path / source.name
    shutil.copy2(str(source), str(working))
    companion = source.with_suffix("")
    if companion.is_dir():
        shutil.copytree(str(companion), str(working.with_suffix("")))

    opened = open_project(str(working))
    opened.raise_for_error()
    try:
        yield str(working)
    finally:
        close_project(
            str(working),
            save=False,
            kill_processes=True,
        ).raise_for_error()


def test_case_1_normal_brick(disposable_cst_project: str) -> None:
    from cst_runtime.core.modeling import define_brick

    result = define_brick(
        disposable_cst_project,
        "gateway_ok",
        "component1",
        "PEC",
        0,
        1,
        0,
        1,
        0,
        1,
    )

    assert result["ok"] is True
    assert result["submission"] == "accepted"
    assert result["execution"] == "reported_ok"


def test_case_2_missing_material(disposable_cst_project: str) -> None:
    from cst_runtime.core.modeling import define_brick

    result = define_brick(
        disposable_cst_project,
        "gateway_missing_material",
        "component1",
        "__CST_RUNTIME_MATERIAL_DOES_NOT_EXIST__",
        2,
        3,
        0,
        1,
        0,
        1,
    )

    assert result["ok"] is False
    assert result["error_type"] == "vba_runtime_error"
    assert result["error"]["phase"] == "execution"


def test_case_3_explicit_err_raise(disposable_cst_project: str) -> None:
    from cst_runtime.core.modeling import add_to_history

    result = add_to_history(
        disposable_cst_project,
        'Err.Raise 513, "CSTRuntimeTest", "forced runtime error"',
        "Gateway forced Err.Raise",
    )

    assert result["ok"] is False
    assert result["error_type"] == "vba_runtime_error"
    assert result["error"]["source"] == "CSTRuntimeTest"


def test_case_4_vba_syntax_error(disposable_cst_project: str) -> None:
    from cst_runtime.core.modeling import add_to_history

    result = add_to_history(
        disposable_cst_project,
        "If Then\n    Brick.Reset\nEnd If",
        "Gateway forced syntax error",
    )

    assert result["ok"] is False
    # A missing side-channel cannot distinguish compile failure from host
    # rejection, so the public type deliberately avoids false precision.
    assert result["error_type"] == "vba_compile_or_host_error"
    assert result["context"]["vba_script"].startswith("If Then")


def test_case_5_observe_history_and_private_undo(
    disposable_cst_project: str,
    tmp_path: Path,
) -> None:
    from cst_runtime.core.identity import attach_expected_project
    from cst_runtime.core.modeling import define_brick

    project, status = attach_expected_project(disposable_cst_project)
    assert project is not None, status
    modeler = project.modeler

    def snapshot():
        method = getattr(modeler, "_GetHistory", None)
        if not callable(method):
            return {"supported": False}
        try:
            return {"supported": True, "value": str(method())}
        except Exception as exc:
            return {"supported": True, "error": str(exc)}

    before = snapshot()
    failed = define_brick(
        disposable_cst_project,
        "gateway_history_probe",
        "component1",
        "__CST_RUNTIME_MATERIAL_DOES_NOT_EXIST__",
        4,
        5,
        0,
        1,
        0,
        1,
    )
    after_failure = snapshot()

    undo = {"supported": False, "attempted": False}
    undo_method = getattr(modeler, "_TryToUndoNTimes", None)
    if callable(undo_method):
        undo["supported"] = True
        undo["attempted"] = True
        try:
            undo["return_value"] = str(undo_method(1))
        except Exception as exc:
            undo["error"] = str(exc)
    after_undo = snapshot()

    report = {
        "project_path": disposable_cst_project,
        "failed_result": failed,
        "history_before": before,
        "history_after_failure": after_failure,
        "undo": undo,
        "history_after_undo": after_undo,
        "questions": {
            "history_node_added": before != after_failure,
            "undo_changed_history": after_failure != after_undo,
        },
    }
    report_path = tmp_path / "cst2022_error_gateway_history_observation.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    assert failed["status"] == "error"
    assert failed["error_type"] == "vba_runtime_error"
    assert failed["error"]["phase"] == "execution"
    assert report_path.is_file()
