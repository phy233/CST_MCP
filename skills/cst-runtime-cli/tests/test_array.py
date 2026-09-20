"""阵列 workflow 的无 CST 单元测试。"""
from __future__ import annotations

import pytest

from cst_runtime.workflows import array


def _fake_batch(monkeypatch):
    events: list[str] = []
    monkeypatch.setattr(
        array.batch,
        "begin",
        lambda project_path, summary: events.append("begin") or {"status": "success"},
    )
    monkeypatch.setattr(
        array.batch,
        "flush",
        lambda project_path: events.append("flush") or {"status": "success"},
    )
    monkeypatch.setattr(
        array.batch,
        "discard",
        lambda project_path: events.append("discard") or {"status": "success"},
    )
    return events


def test_array_groups_codes_and_uses_only_one_reference(monkeypatch) -> None:
    events = _fake_batch(monkeypatch)
    translations: list[tuple[str, tuple[float, float, float], dict]] = []
    deletions: list[str] = []
    monkeypatch.setattr(
        array,
        "translate",
        lambda project_path, name, vector, **kwargs: translations.append(
            (name, vector, kwargs)
        ),
    )
    monkeypatch.setattr(
        array,
        "delete_entity",
        lambda project_path, name, component="": deletions.append(name),
    )

    registry = array.UnitBuilderRegistry(load_entry_points=False)
    built_codes: list[str] = []

    def builder(project_path, code, parameters):
        built_codes.append(code)
        return array.BuildResult("cells", [f"ref_{code}"])

    registry.register("test", builder)
    result = array.build_array(
        "model.cst",
        units={
            "a": {"builder_id": "test"},
            "b": {"builder_id": "test"},
        },
        elements=[
            {"code": "a", "x": 0, "y": 0, "z": 0},
            {"code": "a", "x": 10, "y": 0, "z": 0},
            {"code": "b", "x": 0, "y": 5, "z": 0},
        ],
        registry=registry,
    )

    assert result.status == "success"
    assert result.groups_built == 2
    assert result.instances_created == 3
    assert built_codes == ["a", "b"]
    assert events == ["begin", "flush"]
    assert len(translations) == 2
    assert all("destination" not in kwargs for _, _, kwargs in translations)
    assert deletions == ["ref_b"]


def test_array_rejects_unknown_builder_before_batch(monkeypatch) -> None:
    events = _fake_batch(monkeypatch)
    registry = array.UnitBuilderRegistry(load_entry_points=False)
    result = array.build_array(
        "model.cst",
        units={"a": {"builder_id": "missing"}},
        elements=[{"code": "a", "x": 0, "y": 0, "z": 0}],
        registry=registry,
    )
    assert result.status == "error"
    assert "未知 builder_id" in result.message
    assert events == []


def test_zero_code_is_an_ordinary_unknown_builder_key() -> None:
    from cst_runtime.workflows import array

    result = array.build_array(
        "model.cst",
        units={"1": {"builder_id": "create-brick-template"}},
        elements=[{"code": "0", "x": 0, "y": 0, "z": 0}],
    )

    assert result.status == "error"
    assert "code 0 缺少 UnitSpec" in result.message


def test_array_keeps_batch_when_flush_fails(monkeypatch) -> None:
    events = _fake_batch(monkeypatch)
    monkeypatch.setattr(
        array.batch,
        "flush",
        lambda project_path: events.append("flush") or {
            "status": "error",
            "message": "VBA failed",
            "batch_retained": True,
            "error_type": "vba_runtime_error",
            "execution": "failed",
            "terminal": True,
        },
    )
    registry = array.UnitBuilderRegistry(load_entry_points=False)
    registry.register(
        "test",
        lambda project_path, code, parameters: array.BuildResult("cells", ["ref"]),
    )

    result = array.build_array(
        "model.cst",
        units={"a": {"builder_id": "test"}},
        elements=[{"code": "a", "x": 0, "y": 0, "z": 0}],
        registry=registry,
    )

    assert result.status == "error"
    assert "仅保留用于诊断" in result.message
    assert "请勿直接重试" in result.message
    assert events == ["begin", "flush"]
    assert result.groups_built == result.instances_created == 0
    assert result.groups_planned == result.instances_planned == 1
    assert result.to_dict()["error_type"] == "vba_runtime_error"
    assert result.to_dict()["execution"] == "failed"
    assert result.to_dict()["terminal"] is True


def test_create_brick_template_builder(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(array, "brick", lambda project_path, **kwargs: calls.append(kwargs))
    result = array._create_brick_template(
        "model.cst",
        "cube",
        {
            "component": "demo",
            "name": "cube",
            "material": "PEC",
            "size": [2, 3, 4],
        },
    )
    assert result == array.BuildResult("demo", ["cube"])
    assert calls[0]["x_range"] == (0.0, 2.0)


def test_array_keeps_geometry_and_translation_expressions(monkeypatch) -> None:
    """尺寸、原点和周期表达式必须保留到历史，不能冻结为浮点值。"""
    _fake_batch(monkeypatch)
    bricks, translations = [], []
    monkeypatch.setattr(array, "brick", lambda path, **kw: bricks.append(kw))
    monkeypatch.setattr(array, "translate", lambda path, name, vector, **kw: translations.append(vector))
    result = array.build_array("model.cst", units={"A": {
        "builder_id": "create-brick-template", "parameters": {
            "origin": ["-w/2", 0, 0], "size": ["w", "h", "t"],
        },
    }}, elements=[{"code": "A", "x": 0, "y": 0, "z": 0},
                  {"code": "A", "x": "p", "y": 0, "z": 0}])
    assert result.status == "success"
    assert bricks[0]["x_range"] == ("-w/2", "(-w/2)+(w)")
    assert translations == [("p", 0.0, 0.0)]


@pytest.mark.parametrize("parameters,elements", [
    ({"sizes": [1, 1, 1]}, [{"code": "A", "x": 0, "y": 0, "z": 0}]),
    ({"size": [1, 0, 1]}, [{"code": "A", "x": 0, "y": 0, "z": 0}]),
    ({}, [{"code": "A", "x": 0, "y": 0, "z": 0},
          {"code": "A", "x": "0", "y": 0, "z": 0}]),
    ({}, [array.ArrayElement("A", float("nan"), 0, 0)]),
])
def test_bad_template_inputs_never_start_batch(monkeypatch, parameters, elements) -> None:
    events = _fake_batch(monkeypatch)
    result = array.build_array("model.cst", {"A": {
        "builder_id": "create-brick-template", "parameters": parameters}}, elements)
    assert result.status == "error"
    assert result.instances_created == 0
    assert events == []


def test_copy_template_preserves_all_source_solids(monkeypatch) -> None:
    events = _fake_batch(monkeypatch)
    translations = []
    monkeypatch.setattr(array, "translate", lambda path, **kw: translations.append(kw))
    monkeypatch.setattr(array, "delete_entity", lambda *a, **kw: pytest.fail("不得删除源模板"))
    monkeypatch.setattr(array, "brick", lambda *a, **kw: pytest.fail("不得重建源模板"))
    result = array.build_array("model.cst", {"A": {"builder_id": "copy-template",
        "parameters": {"component": "cell", "reference_names": ["patch", "substrate"]}}},
        [{"code": "A", "x": 0, "y": 0, "z": 0},
         {"code": "A", "x": "p", "y": 0, "z": 0}])
    assert result.status == "success"
    assert result.instances_created == result.instances_reused == 1
    assert result.instances_planned == 2
    assert [item["name"] for item in translations] == ["cell:patch", "cell:substrate"]
    assert events == ["begin", "flush"]


def test_templates_cannot_reuse_the_same_entity_name(monkeypatch) -> None:
    events = _fake_batch(monkeypatch)
    result = array.build_array("model.cst", {
        code: {"builder_id": "create-brick-template", "parameters": {"name": "same"}} for code in ("A", "B")},
        [{"code": "A", "x": 0, "y": 0, "z": 0}, {"code": "B", "x": 5, "y": 0, "z": 0}])
    assert result.status == "error"
    assert "多个 code" in result.message
    assert events == []


def test_tiny_nonzero_translation_is_not_treated_as_origin(monkeypatch) -> None:
    _fake_batch(monkeypatch)
    vectors = []
    monkeypatch.setattr(array, "translate", lambda path, **kw: vectors.append(kw["vector"]))
    result = array.build_array("model.cst", {"A": {"builder_id": "copy-template",
        "parameters": {"component": "cell", "reference_names": ["patch"]}}},
        [{"code": "A", "x": 1e-12, "y": 0, "z": 0}])
    assert result.status == "success"
    assert vectors == [(1e-12, 0.0, 0.0)]
    assert result.instances_reused == 0


def test_public_template_example_reaches_one_history_submission(monkeypatch) -> None:
    """覆盖生成模板到 VBA 提交的代码链；替换 CST 连接、版本探测与执行。"""
    import jsonschema
    from cst_runtime.api import tools
    from cst_runtime.cli.dispatch import _tool_args_template
    from cst_runtime.core import buffer, modeling
    from cst_runtime.core.errors import success_response
    from cst_runtime.core.compatibility.base import CompatibilityProfile
    from cst_runtime.worker import handle_request

    args = _tool_args_template("build-array")
    args["project_path"] = "model.cst"
    schema = tools()["build-array"]
    jsonschema.validate(args, schema.input_schema)
    captured = []
    monkeypatch.setattr(modeling, "detect_compatibility_profile", lambda: CompatibilityProfile(major=2022))
    monkeypatch.setattr(modeling, "attach_expected_project", lambda path: (object(), {}))
    monkeypatch.setattr(modeling, "submit_vba_history", lambda project, label, lines, **kw:
                        captured.append(lines) or success_response(submission="accepted", execution="reported_ok"))
    try:
        result = handle_request({"id": "example", "action": "call_tool", "name": "build-array", "arguments": args})
        jsonschema.validate(result, schema.output_schema)
        assert result["status"] == "success"
        assert result["instances_created"] == 2
        assert len(captured) == 1
        assert "With Brick" in captured[0][0]
        assert 'Transform "Shape", "Translate"' in captured[0][0]
        assert not buffer.is_batch_mode(modeling._abs_project_path("model.cst"))
    finally:
        buffer.discard_batch(modeling._abs_project_path("model.cst"))
