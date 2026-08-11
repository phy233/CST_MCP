"""实体删除名称规范化测试。"""
from __future__ import annotations


def test_delete_entity_accepts_component_and_bare_name(monkeypatch) -> None:
    from cst_runtime.core import modeling

    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        modeling,
        "_single_vba",
        lambda project_path, history_name, vba: calls.append((history_name, vba))
        or {"status": "success"},
    )

    result = modeling.delete_entity("model.cst", "cells", "unit1")

    assert result["status"] == "success"
    assert calls == [("delete entity: cells:unit1", 'Solid.Delete "cells:unit1"')]


def test_delete_entity_accepts_qualified_name_without_component(monkeypatch) -> None:
    from cst_runtime.core import modeling

    calls: list[str] = []
    monkeypatch.setattr(
        modeling,
        "_single_vba",
        lambda project_path, history_name, vba: calls.append(vba)
        or {"status": "success"},
    )

    result = modeling.delete_entity("model.cst", "", "cells:unit1")

    assert result["status"] == "success"
    assert calls == ['Solid.Delete "cells:unit1"']


def test_delete_entity_rejects_ambiguous_names(monkeypatch) -> None:
    from cst_runtime.core import modeling

    monkeypatch.setattr(
        modeling,
        "_single_vba",
        lambda *args: (_ for _ in ()).throw(AssertionError("非法输入不得提交 VBA")),
    )

    cases = [
        ("", "unit1"),
        ("cells", "cells:unit1"),
        ("", "cells:"),
        ("", ""),
    ]
    for component, name in cases:
        result = modeling.delete_entity("model.cst", component, name)
        assert result["status"] == "error"
        assert result["error_type"] == "invalid_arguments"
