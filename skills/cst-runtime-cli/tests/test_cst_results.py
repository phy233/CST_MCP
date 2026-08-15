"""结果查询与导出的真实 CST 2022 集成测试。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from cst_helpers import (
    assert_error_response,
    prepare_interactive_result_read,
    project_arguments,
)


pytestmark = [
    pytest.mark.cst_integration,
    pytest.mark.cst_destructive,
]


def test_get_version_info_reads(cst_case: Any) -> None:
    result = cst_case.require_success("get-version-info", {})
    assert result.get("version_info"), result


def test_list_result_items_0d1d(cst_case: Any) -> None:
    prepare_interactive_result_read(cst_case)
    result = cst_case.require_success(
        "list-result-items",
        project_arguments(
            cst_case,
            module_type="3d",
            filter_type="0D/1D",
            allow_interactive=True,
            subproject_treepath="",
        ),
    )
    assert isinstance(result.get("items"), list), result
    assert result["count"] == len(result["items"]), result


def test_list_result_items_all_unsupported(cst_case: Any) -> None:
    prepare_interactive_result_read(cst_case)
    result = cst_case.call(
        "list-result-items",
        project_arguments(
            cst_case,
            module_type="3d",
            filter_type="all",
            allow_interactive=True,
            subproject_treepath="",
        ),
    )
    assert_error_response(
        result,
        error_types={"unsupported_feature"},
        phase="compatibility",
    )
    assert result.get("feature") == "results.list_all", result
    assert result.get("context", {}).get("required_capability") == "results_all_items", result


def test_list_run_ids_returns_list_or_documented_missing(cst_case: Any) -> None:
    prepare_interactive_result_read(cst_case)
    result = cst_case.call(
        "list-run-ids",
        project_arguments(
            cst_case,
            treepath="1D Results\\S-Parameters\\S1,1",
            module_type="3d",
            allow_interactive=True,
            skip_nonparametric=False,
            max_mesh_passes_only=False,
        ),
    )
    if result.get("status") == "error":
        # 首次仿真的正常初始状态：节点尚不存在，使用稳定错误码。
        assert result.get("error_type") == "result_node_not_found", result
        return
    assert result.get("status") == "success", result
    assert isinstance(result.get("run_ids"), list), result


def test_list_sparameter_results(cst_case: Any) -> None:
    prepare_interactive_result_read(cst_case)
    result = cst_case.require_success(
        "list-sparameter-results",
        project_arguments(cst_case),
    )
    assert isinstance(result.get("results"), list), result
    assert result["count"] == len(result["results"]), result


def test_list_field_results(cst_case: Any) -> None:
    prepare_interactive_result_read(cst_case)
    result = cst_case.require_success(
        "list-field-results",
        project_arguments(cst_case),
    )
    assert isinstance(result.get("results"), list), result


def test_list_subprojects(cst_case: Any) -> None:
    prepare_interactive_result_read(cst_case)
    result = cst_case.require_success(
        "list-subprojects",
        project_arguments(cst_case, allow_interactive=True),
    )
    assert isinstance(result.get("subprojects"), list), result


def test_open_results_project_validates(cst_case: Any) -> None:
    prepare_interactive_result_read(cst_case)
    result = cst_case.require_success(
        "open-results-project",
        project_arguments(
            cst_case,
            allow_interactive=True,
            subproject_treepath="",
        ),
    )
    assert str(result.get("filename", "")).endswith(".cst"), result


def test_export_sparameter_missing_path_error(cst_case: Any) -> None:
    prepare_interactive_result_read(cst_case)
    export_path = Path(cst_case.shared.temp_root) / "missing_sparam.json"
    result = cst_case.call(
        "export-sparameter",
        project_arguments(
            cst_case,
            run_id=0,
            output_path=str(export_path),
            result_path="__pytest_missing__",
        ),
    )
    assert not export_path.exists(), result
    assert_error_response(
        result,
        error_types={"sparameter_result_not_found"},
        phase="runtime",
    )


def test_export_touchstone_empty_project_is_structured(cst_case: Any) -> None:
    """基准工程可能没有 S 参数：成功必须是完整文件，失败必须是结构化错误。"""
    prepare_interactive_result_read(cst_case)
    output_base = Path(cst_case.shared.temp_root) / "touchstone_export"
    result = cst_case.call(
        "export-touchstone",
        project_arguments(
            cst_case,
            output_base_path=str(output_base),
            parameter_type="S",
            data_format="MA",
        ),
    )
    if result.get("status") == "success":
        output_file = Path(result["output_file"])
        assert output_file.is_file(), result
        assert result["file_size"] > 0, result
        assert output_file.name.startswith(output_base.name), result
        assert any(header.startswith("!") for header in result.get("header_lines", []))
        return
    assert_error_response(
        result,
        error_types={"vba_runtime_error", "touchstone_file_not_found", "touchstone_file_invalid"},
        phase="execution" if result.get("error_type") == "vba_runtime_error" else "runtime",
    )
    assert not list(output_base.parent.glob(output_base.name + "*")), result
