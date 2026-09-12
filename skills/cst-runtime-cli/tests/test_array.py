"""阵列 workflow 的无 CST 单元测试。"""
from __future__ import annotations

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


def test_array_rolls_back_on_unknown_builder(monkeypatch) -> None:
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
    assert events == ["begin", "discard"]


def test_zero_code_is_an_ordinary_unknown_builder_key() -> None:
    from cst_runtime.workflows import array

    result = array.build_array(
        "model.cst",
        units={"1": {"builder_id": "brick-v1"}},
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


def test_builtin_brick_builder(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(array, "brick", lambda project_path, **kwargs: calls.append(kwargs))
    result = array._build_brick(
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
        "builder_id": "brick-v1", "parameters": {
            "origin": ["-w/2", 0, 0], "size": ["w", "h", "t"],
        },
    }}, elements=[{"code": "A", "x": 0, "y": 0, "z": 0},
                  {"code": "A", "x": "p", "y": 0, "z": 0}])
    assert result.status == "success"
    assert bricks[0]["x_range"] == ("-w/2", "(-w/2)+(w)")
    assert translations == [("p", 0.0, 0.0)]
