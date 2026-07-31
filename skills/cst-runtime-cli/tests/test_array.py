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
    translations: list[tuple[str, tuple[float, float, float]]] = []
    deletions: list[str] = []
    monkeypatch.setattr(
        array,
        "translate",
        lambda project_path, name, vector, **kwargs: translations.append((name, vector)),
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
