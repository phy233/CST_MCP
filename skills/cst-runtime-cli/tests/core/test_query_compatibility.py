from __future__ import annotations

from types import SimpleNamespace

from cst_runtime.core.compatibility import queries, results, tree
from cst_runtime.core.errors import UnsupportedFeatureError


def test_result_exists_prefers_result_tree_api() -> None:
    checker = SimpleNamespace(DoesTreeItemExist=lambda path: path == "1D Results\\S-Parameters")
    project = SimpleNamespace(model3d=SimpleNamespace(ResultTree=checker))

    assert tree.result_item_exists(project, "1D Results\\S-Parameters") is True


def test_result_exists_falls_back_to_vba(monkeypatch) -> None:
    monkeypatch.setattr(tree, "execute_text_query", lambda _project, _lines: ["1"])

    assert tree.result_item_exists(object(), "1D Results\\S-Parameters") is True


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
