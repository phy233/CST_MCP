"""CST 2022 VBA 错误网关的人工验收用例。

只有操作者同时提供源工程并显式启用时才会执行这些测试。整个测试模块只打开
一个共享的隔离工程副本；History/Undo 观察具有探索性和破坏性，因此必须串行运行。
"""
from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

import pytest


pytestmark = [
    pytest.mark.cst_integration,
    pytest.mark.cst_destructive,
    pytest.mark.skipif(
        os.environ.get("CST_RUN_ERROR_GATEWAY_TESTS") != "1",
        reason="设置 CST_RUN_ERROR_GATEWAY_TESTS=1 后才执行 CST 2022 人工验收",
    ),
]


@pytest.fixture(scope="module")
def shared_isolated_cst_project(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, Any]:
    """创建、打开并在全部用例结束后关闭唯一的隔离工程副本。"""
    source_value = os.environ.get("CST_TEST_PROJECT")
    if not source_value:
        pytest.skip("请把 CST_TEST_PROJECT 设置为可复制使用的 .cst 源工程")

    from cst_runtime.lib.session import close_project, open_project

    source = Path(source_value).expanduser().resolve()
    if not source.is_file():
        pytest.skip(f"CST_TEST_PROJECT 不存在：{source}")
    working_dir = tmp_path_factory.mktemp("cst2022-error-gateway-shared")
    working = working_dir / source.name
    shutil.copy2(str(source), str(working))
    companion = source.with_suffix("")
    if companion.is_dir():
        shutil.copytree(str(companion), str(working.with_suffix("")))

    opened = open_project(str(working))
    opened.raise_for_error()
    try:
        yield {
            "project_path": str(working),
            "report_dir": working_dir,
            "name_prefix": f"gateway_{uuid.uuid4().hex[:8]}",
        }
    finally:
        close_project(
            str(working),
            save=False,
            kill_processes=True,
        ).raise_for_error()


def _project_path(shared_project: dict[str, Any]) -> str:
    return str(shared_project["project_path"])


def _case_name(shared_project: dict[str, Any], suffix: str) -> str:
    return f'{shared_project["name_prefix"]}_{suffix}'


def test_case_1_normal_brick(shared_isolated_cst_project: dict[str, Any]) -> None:
    from cst_runtime.core.modeling import define_brick

    result = define_brick(
        _project_path(shared_isolated_cst_project),
        _case_name(shared_isolated_cst_project, "ok"),
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


def test_case_2_missing_material(shared_isolated_cst_project: dict[str, Any]) -> None:
    from cst_runtime.core.modeling import define_brick

    result = define_brick(
        _project_path(shared_isolated_cst_project),
        _case_name(shared_isolated_cst_project, "missing_material"),
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


def test_case_3_explicit_err_raise(shared_isolated_cst_project: dict[str, Any]) -> None:
    from cst_runtime.core.modeling import add_to_history

    result = add_to_history(
        _project_path(shared_isolated_cst_project),
        'Err.Raise 513, "CSTRuntimeTest", "forced runtime error"',
        "Gateway forced Err.Raise",
    )

    assert result["ok"] is False
    assert result["error_type"] == "vba_runtime_error"
    assert result["error"]["source"] == "CSTRuntimeTest"


def test_case_4_vba_syntax_error(shared_isolated_cst_project: dict[str, Any]) -> None:
    from cst_runtime.core.modeling import add_to_history

    result = add_to_history(
        _project_path(shared_isolated_cst_project),
        "If Then\n    Brick.Reset\nEnd If",
        "Gateway forced syntax error",
    )

    assert result["ok"] is False
    # 状态文件缺失时无法区分编译失败与宿主拒绝，因此公共错误类型不做虚假细分。
    assert result["error_type"] == "vba_compile_or_host_error"
    assert result["context"]["vba_script"].startswith("If Then")


def test_case_5_observe_history_and_private_undo(
    shared_isolated_cst_project: dict[str, Any],
) -> None:
    from cst_runtime.core.identity import attach_expected_project
    from cst_runtime.core.modeling import define_brick

    project_path = _project_path(shared_isolated_cst_project)
    project, status = attach_expected_project(project_path)
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
        project_path,
        _case_name(shared_isolated_cst_project, "history_probe"),
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
        "project_path": project_path,
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
    report_path = Path(shared_isolated_cst_project["report_dir"]) / (
        "cst2022_error_gateway_history_observation.json"
    )
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    assert failed["status"] == "error"
    assert failed["error_type"] == "vba_runtime_error"
    assert failed["error"]["phase"] == "execution"
    assert report_path.is_file()
