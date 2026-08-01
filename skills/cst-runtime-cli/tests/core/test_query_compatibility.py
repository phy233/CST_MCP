from __future__ import annotations

from types import SimpleNamespace

from cst_runtime.core import project as project_core
from cst_runtime.core.compatibility import materials, queries, results, tree
from cst_runtime.core.errors import UnsupportedFeatureError


def test_result_exists_prefers_result_tree_api() -> None:
    checker = SimpleNamespace(DoesTreeItemExist=lambda path: path == "1D Results\\S-Parameters")
    project = SimpleNamespace(model3d=SimpleNamespace(ResultTree=checker))

    assert tree.result_item_exists(project, "1D Results\\S-Parameters") is True


def test_result_exists_falls_back_to_vba(monkeypatch) -> None:
    captured: list[str] = []

    def query(_project, lines):
        captured.extend(lines)
        return ["1"]

    monkeypatch.setattr(tree, "execute_text_query", query)

    assert tree.result_item_exists(object(), "1D Results\\S-Parameters") is True
    assert any("ResultTree.DoesTreeItemExist" in line for line in captured)


def test_tree_items_fall_back_to_recursive_result_tree_vba(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def query(_project, lines, *, timeout):
        captured["lines"] = list(lines)
        captured["timeout"] = timeout
        return [
            "Components\\antenna",
            "Components\\antenna\\substrate",
            "Components\\antenna\\substrate",
        ]

    monkeypatch.setattr(tree, "execute_text_query", query)

    items = tree.get_tree_items(object())

    assert items == ["Components\\antenna", "Components\\antenna\\substrate"]
    assert captured["timeout"] == 5.0
    script = "\n".join(captured["lines"])
    assert "ResultTree.GetFirstChildName" in script
    assert "ResultTree.GetNextItemName" in script
    assert "ResultTree.DoesTreeItemExist" in script


def test_filtered_tree_items_use_get_tree_results(monkeypatch) -> None:
    captured: list[str] = []

    def query(_project, lines, *, timeout):
        assert timeout == 5.0
        captured.extend(lines)
        return ["1D Results\\S-Parameters\\S1,1"]

    monkeypatch.setattr(tree, "execute_text_query", query)

    items = tree.get_tree_items(object(), filter="0D/1D")

    assert items == ["1D Results\\S-Parameters\\S1,1"]
    assert "GetTreeResults" in "\n".join(captured)
    assert '"0D/1D recursive"' in "\n".join(captured)


def test_material_names_use_zero_based_material_vba(monkeypatch) -> None:
    captured: list[str] = []

    def query(_project, lines):
        captured.extend(lines)
        return ["Vacuum", "FR-4 (loss free)", "Vacuum"]

    monkeypatch.setattr(materials, "execute_text_query", query)

    names = materials.list_material_names(object())

    assert names == ["Vacuum", "FR-4 (loss free)"]
    script = "\n".join(captured)
    assert "Material.GetNumberOfMaterials" in script
    assert "For cstRtMaterialIndex = 0 To cstRtMaterialCount - 1" in script
    assert "Material.GetNameOfMaterialFromIndex(cstRtMaterialIndex)" in script


def test_list_entities_uses_legacy_tree_results(monkeypatch) -> None:
    project = object()
    monkeypatch.setattr(
        project_core,
        "attach_expected_project",
        lambda _project_path: (project, {}),
    )
    monkeypatch.setattr(
        project_core,
        "get_tree_items",
        lambda _project: [
            "Components\\antenna",
            "Components\\antenna\\substrate",
            "Components\\antenna\\patch",
            "Materials\\FR-4 (loss free)",
        ],
    )

    result = project_core.list_entities("D:/work/working.cst", component="antenna")

    assert result["status"] == "success"
    assert result["entities"] == [
        {"component": "antenna", "name": "substrate"},
        {"component": "antenna", "name": "patch"},
    ]


def test_delete_results_falls_back_to_immediate_vba(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(queries, "execute_immediate_vba", lambda project, lines: calls.append(lines))

    metadata = queries.delete_project_results(object())

    assert calls == [["DeleteResults"]]
    assert metadata["transport"] == "immediate_vba"


def test_solver_type_falls_back_to_text_query(monkeypatch) -> None:
    monkeypatch.setattr(queries, "execute_text_query", lambda _project, _lines: ["HF Time Domain"])

    solver_type, metadata = queries.get_project_solver_type(object())

    assert solver_type == "HF Time Domain"
    assert metadata["transport"] == "immediate_vba"


def test_list_all_results_is_explicitly_unsupported_without_capability() -> None:
    try:
        results.list_all_result_items(object())
    except UnsupportedFeatureError as exc:
        response = exc.to_response()
    else:
        raise AssertionError("缺少全量枚举接口时必须返回不支持错误")

    assert response["error_type"] == "unsupported_feature"
    assert response["error"]["phase"] == "compatibility"
