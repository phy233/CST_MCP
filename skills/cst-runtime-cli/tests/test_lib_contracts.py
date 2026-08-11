"""lib 公开结果契约测试。"""
from __future__ import annotations

import json

import pytest

from cst_runtime.lib.contracts import (
    CSTOperationError,
    OperationResult,
    as_result,
    error_result,
    success_result,
)


def test_operation_result_is_json_dict() -> None:
    result = success_result(value=3.5)

    assert isinstance(result, dict)
    assert json.loads(json.dumps(result)) == {"status": "success", "value": 3.5}


def test_raise_for_error_preserves_complete_result() -> None:
    result = error_result("project_not_open", "工程未打开", project_path="a.cst")

    with pytest.raises(CSTOperationError) as caught:
        result.raise_for_error()

    assert caught.value.result == result
    assert caught.value.result["project_path"] == "a.cst"


def test_unwrap_fast_fails_and_returns_semantic_field() -> None:
    assert success_result(value=12).unwrap("value") == 12
    with pytest.raises(CSTOperationError):
        error_result("read_failed", "读取失败").unwrap("value")


def test_as_result_normalizes_plain_values_and_statuses() -> None:
    assert as_result(False, field="exists") == {
        "status": "success",
        "exists": False,
    }
    assert isinstance(as_result({"status": "success"}), OperationResult)


def test_close_project_forwards_process_cleanup_choice(monkeypatch) -> None:
    from cst_runtime.lib import session

    received = {}

    def fake_close_project(project_path, **kwargs):
        received["project_path"] = project_path
        received.update(kwargs)
        return {"status": "success"}

    monkeypatch.setattr(session, "_close_project", fake_close_project)

    result = session.close_project("model.cst", kill_processes=True)

    assert result["status"] == "success"
    assert received["kill_processes"] is True


def test_session_is_locked_uses_companion_directory_lok_files(tmp_path) -> None:
    from cst_runtime.lib import session

    project_path = tmp_path / "antenna.cst"
    legacy_lock = tmp_path / "antenna.cst.lock"
    legacy_lock.touch()

    assert session.is_locked(str(project_path))["locked"] is False

    companion_dir = tmp_path / "antenna" / "Model3D"
    companion_dir.mkdir(parents=True)
    (companion_dir / "Project.lok").touch()

    assert session.is_locked(str(project_path))["locked"] is True


def test_existing_geometry_api_no_longer_throws_business_error(monkeypatch) -> None:
    from cst_runtime.lib import geometry

    monkeypatch.setattr(
        geometry,
        "_define_brick",
        lambda *args, **kwargs: {
            "status": "error",
            "error_type": "material_not_found",
            "message": "材料不存在",
        },
    )

    result = geometry.brick(
        "model.cst",
        "component1",
        "brick1",
        "missing",
        (0, 1),
        (0, 1),
        (0, 1),
    )

    assert isinstance(result, OperationResult)
    assert result["status"] == "error"
    assert result["error_type"] == "material_not_found"
    with pytest.raises(CSTOperationError):
        result.raise_for_error()


@pytest.mark.parametrize("operation", ["cylinder", "cone"])
def test_geometry_axial_solid_forwards_coordinates_by_keyword(monkeypatch, operation: str) -> None:
    """几何门面必须显式转发轴向范围和两个横向中心。"""
    from cst_runtime.lib import geometry

    received = {}

    def fake_define(*args, **kwargs):
        received["args"] = args
        received.update(kwargs)
        return {"status": "success"}

    if operation == "cylinder":
        monkeypatch.setattr(geometry, "_define_cylinder", fake_define)
        result = geometry.cylinder(
            "model.cst", "component1", "solid", "PEC", "x",
            (2, 3), 4, (1, 9),
        )
    else:
        monkeypatch.setattr(geometry, "_define_cone", fake_define)
        result = geometry.cone(
            "model.cst", "component1", "solid", "PEC", "x",
            (2, 3), 4, 1, (1, 9),
        )

    assert result["status"] == "success"
    assert received["args"] == ()
    assert received["axis"] == "x"
    assert received["axis_min"] == 1
    assert received["axis_max"] == 9
    assert received["center1"] == 2
    assert received["center2"] == 3


def test_wrap_public_preserves_nested_error_envelope() -> None:
    from cst_runtime.lib._facade import wrap_public
    from cst_runtime.lib.contracts import raise_result_error

    def operation():
        raise_result_error(
            {
                "ok": False,
                "status": "error",
                "error_type": "vba_runtime_error",
                "message": "missing material",
                "error": {
                    "type": "vba_runtime_error",
                    "message": "missing material",
                    "phase": "execution",
                },
                "context": {"operation_id": "op-1"},
            },
            "fallback",
        )

    result = wrap_public(operation)()

    assert result["error_type"] == "vba_runtime_error"
    assert result["error"]["phase"] == "execution"
    assert result["context"]["operation_id"] == "op-1"


def test_parameter_scalar_is_exposed_as_semantic_value(monkeypatch) -> None:
    from cst_runtime.lib import parameters

    monkeypatch.setattr(
        parameters,
        "_list_parameters",
        lambda project_path: {
            "status": "success",
            "parameters": {"length": {"value": 12.5}},
        },
    )

    assert parameters.get_param("model.cst", "length").unwrap("value") == 12.5


def test_parameter_read_error_is_not_converted_to_false_or_empty(monkeypatch) -> None:
    from cst_runtime.lib import parameters

    monkeypatch.setattr(
        parameters,
        "_list_parameters",
        lambda project_path: {
            "status": "error",
            "error_type": "project_not_open",
            "message": "工程未打开",
        },
    )

    result = parameters.param_exists("model.cst", "length")
    assert result["status"] == "error"
    assert result["error_type"] == "project_not_open"
