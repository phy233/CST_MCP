"""通过唯一 Worker 和唯一隔离工程执行的真实 CST 2022 集成测试。"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import pytest


pytestmark = [
    pytest.mark.cst_integration,
    pytest.mark.cst_destructive,
]


COMPONENT = "component1"


def _entity_keys(items: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {
        (str(item.get("component", "")), str(item.get("name", "")))
        for item in items
    }


def _project_arguments(cst_case: Any, **arguments: Any) -> dict[str, Any]:
    return {"project_path": cst_case.project_path, **arguments}


def test_00_only_one_expected_project_is_open(cst_case: Any) -> None:
    """真机层必须只看到共享隔离工程，并能读取真实工程状态。"""
    opened = cst_case.require_success("list-open-projects", {})
    projects = list(opened.get("open_projects", []))
    assert len(projects) == 1, opened
    assert os.path.normcase(os.path.abspath(projects[0]["project_path"])) == os.path.normcase(
        os.path.abspath(cst_case.project_path)
    )

    parameters = cst_case.require_success(
        "list-parameters",
        {"project_path": cst_case.project_path},
    )
    assert parameters.get("parameters"), parameters
    entities = cst_case.require_success(
        "list-entities",
        {"project_path": cst_case.project_path, "component": ""},
    )
    assert isinstance(entities.get("entities"), list), entities


def test_10_brick_create_query_delete_query(cst_case: Any) -> None:
    """砖体必须经过创建、存在确认、删除和消失确认。"""
    name = cst_case.name("brick")
    assert not cst_case.shared.entity_exists(COMPONENT, name)

    cst_case.require_success(
        "define-brick",
        _project_arguments(
            cst_case,
            name=name,
            component=COMPONENT,
            material="PEC",
            x_min=100,
            x_max=101,
            y_min=100,
            y_max=101,
            z_min=100,
            z_max=101,
        ),
    )
    cst_case.shared.register_entity(COMPONENT, name)
    assert cst_case.shared.entity_exists(COMPONENT, name)

    cst_case.shared.delete_entity(COMPONENT, name)


def test_11_cylinder_create_query_delete_query(cst_case: Any) -> None:
    """圆柱体使用真实 CST 创建，并通过实体树验证和清理。"""
    name = cst_case.name("cylinder")
    assert not cst_case.shared.entity_exists(COMPONENT, name)

    cst_case.require_success(
        "define-cylinder",
        _project_arguments(
            cst_case,
            name=name,
            component=COMPONENT,
            material="PEC",
            outer_radius=0.5,
            inner_radius=0,
            axis="z",
            z_min=100,
            z_max=101,
            x_center=103,
            y_center=103,
        ),
    )
    cst_case.shared.register_entity(COMPONENT, name)
    assert cst_case.shared.entity_exists(COMPONENT, name)

    cst_case.shared.delete_entity(COMPONENT, name)


def test_12_boolean_add_consumes_operand_and_result_can_be_deleted(cst_case: Any) -> None:
    """布尔加应保留第一个实体、消耗第二个实体，并允许删除结果。"""
    first = cst_case.name("union_a")
    second = cst_case.name("union_b")
    for index, name in enumerate((first, second)):
        cst_case.require_success(
            "define-brick",
            _project_arguments(
                cst_case,
                name=name,
                component=COMPONENT,
                material="PEC",
                x_min=110 + index * 0.5,
                x_max=111 + index * 0.5,
                y_min=110,
                y_max=111,
                z_min=110,
                z_max=111,
            ),
        )
        cst_case.shared.register_entity(COMPONENT, name)
        assert cst_case.shared.entity_exists(COMPONENT, name)

    cst_case.require_success(
        "boolean-add",
        _project_arguments(
            cst_case,
            shape1=f"{COMPONENT}:{first}",
            shape2=f"{COMPONENT}:{second}",
        ),
    )
    assert cst_case.shared.entity_exists(COMPONENT, first)
    assert not cst_case.shared.entity_exists(COMPONENT, second)
    cst_case.shared.forget_entity(COMPONENT, second)
    cst_case.shared.delete_entity(COMPONENT, first)


def test_20_array_batch_creates_and_deletes_every_instance(cst_case: Any) -> None:
    """公开阵列工作流应真实提交批次，全部新增实体随后逐个删除。"""
    reference_name = cst_case.name("array_ref")
    before = _entity_keys(cst_case.shared.list_entities())
    result = cst_case.require_success(
        "build-array",
        _project_arguments(
            cst_case,
            units={
                "a": {
                    "builder_id": "brick-v1",
                    "parameters": {
                        "component": COMPONENT,
                        "name": reference_name,
                        "material": "PEC",
                        "size": [0.4, 0.4, 0.4],
                        "origin": [120, 120, 120],
                    },
                }
            },
            elements=[
                {"code": "a", "x": 0, "y": 0, "z": 0},
                {"code": "a", "x": 2, "y": 0, "z": 0},
                {"code": "a", "x": 0, "y": 2, "z": 0},
            ],
            summary=f"Pytest array {cst_case.prefix}",
        ),
    )
    assert result.get("groups_built") == 1, result
    assert result.get("instances_created") == 3, result

    after = _entity_keys(cst_case.shared.list_entities())
    created = sorted(after - before)
    assert len(created) == 3, {"before": before, "after": after, "result": result}
    for component, name in created:
        cst_case.shared.register_entity(component, name)
        assert cst_case.shared.entity_exists(component, name)
    for component, name in reversed(created):
        cst_case.shared.delete_entity(component, name)


def test_21_failed_array_batch_leaves_no_entity(cst_case: Any) -> None:
    """未知 builder 的失败批次必须丢弃，不能留下部分实体。"""
    before = _entity_keys(cst_case.shared.list_entities())
    result = cst_case.call(
        "build-array",
        _project_arguments(
            cst_case,
            units={"a": {"builder_id": "__missing_builder__"}},
            elements=[{"code": "a", "x": 0, "y": 0, "z": 0}],
            summary=f"Pytest failed array {cst_case.prefix}",
        ),
    )
    assert result.get("status") == "error", result
    assert _entity_keys(cst_case.shared.list_entities()) == before


def test_30_missing_material_reports_error_without_entity(cst_case: Any) -> None:
    """网关报告缺失材料错误后，实体树必须保持无副作用。"""
    name = cst_case.name("missing_material")
    before = _entity_keys(cst_case.shared.list_entities())
    result = cst_case.call(
        "define-brick",
        _project_arguments(
            cst_case,
            name=name,
            component=COMPONENT,
            material="__CST_RUNTIME_MATERIAL_DOES_NOT_EXIST__",
            x_min=130,
            x_max=131,
            y_min=130,
            y_max=131,
            z_min=130,
            z_max=131,
        ),
    )
    assert result.get("status") == "error", result
    assert not cst_case.shared.entity_exists(COMPONENT, name)
    assert _entity_keys(cst_case.shared.list_entities()) == before


@pytest.mark.xfail(
    strict=True,
    reason="空结果尚未标准化为 no_result/result_not_found 错误",
)
def test_40_empty_1d_result_returns_standard_no_result_error(cst_case: Any) -> None:
    """空工程读取 1D 结果应返回标准无结果错误。"""
    export_path = Path(cst_case.shared.temp_root) / "missing_1d.json"
    result = cst_case.call(
        "get-1d-result",
        _project_arguments(
            cst_case,
            treepath="1D Results\\__pytest_missing__",
            module_type="3d",
            run_id=0,
            load_impedances=True,
            export_path=str(export_path),
            allow_interactive=False,
        ),
    )
    assert result.get("status") == "error", result
    assert result.get("error_type") in {"no_result", "result_not_found"}, result
    assert not export_path.exists()


@pytest.mark.xfail(
    strict=True,
    reason="空结果尚未标准化为 no_result/result_not_found 错误",
)
def test_41_empty_2d_result_returns_standard_no_result_error(cst_case: Any) -> None:
    """空工程读取 2D 结果应返回标准无结果错误。"""
    export_path = Path(cst_case.shared.temp_root) / "missing_2d.json"
    result = cst_case.call(
        "get-2d-result",
        _project_arguments(
            cst_case,
            treepath="2D/3D Results\\__pytest_missing__",
            module_type="3d",
            export_path=str(export_path),
            allow_interactive=False,
            subproject_treepath="",
            include_data=False,
        ),
    )
    assert result.get("status") == "error", result
    assert result.get("error_type") in {"no_result", "result_not_found"}, result
    assert not export_path.exists()


@pytest.mark.xfail(
    strict=True,
    reason="空结果尚未标准化为 no_result/result_not_found 错误",
)
def test_42_empty_parameter_combination_returns_standard_no_result_error(
    cst_case: Any,
) -> None:
    """空工程读取参数组合应返回标准无结果错误。"""
    result = cst_case.call(
        "get-parameter-combination",
        _project_arguments(
            cst_case,
            run_id=0,
            module_type="3d",
            allow_interactive=False,
        ),
    )
    assert result.get("status") == "error", result
    assert result.get("error_type") in {"no_result", "result_not_found"}, result


@pytest.mark.cst_solver
def test_50_solver_reaches_running_state_then_is_forcibly_stopped(cst_case: Any) -> None:
    """用短矩形波导负载观察真实运行态，随后无条件停止并删除几何体。"""
    wall_ranges = [
        ("top", -11.43, 11.43, 5.08, 6.08, 0, 100),
        ("bottom", -11.43, 11.43, -6.08, -5.08, 0, 100),
        ("left", -12.43, -11.43, -6.08, 6.08, 0, 100),
        ("right", 11.43, 12.43, -6.08, 6.08, 0, 100),
    ]
    walls: list[tuple[str, str]] = []
    saw_running = False
    saw_stopped = False
    stop_result: dict[str, Any] | None = None
    try:
        for suffix, x_min, x_max, y_min, y_max, z_min, z_max in wall_ranges:
            name = cst_case.name(f"waveguide_{suffix}")
            assert not cst_case.shared.entity_exists(COMPONENT, name)
            cst_case.require_success(
                "define-brick",
                _project_arguments(
                    cst_case,
                    name=name,
                    component=COMPONENT,
                    material="PEC",
                    x_min=x_min,
                    x_max=x_max,
                    y_min=y_min,
                    y_max=y_max,
                    z_min=z_min,
                    z_max=z_max,
                ),
            )
            cst_case.shared.register_entity(COMPONENT, name)
            walls.append((COMPONENT, name))
            assert cst_case.shared.entity_exists(COMPONENT, name)

        cst_case.require_success(
            "define-frequency-range",
            _project_arguments(cst_case, start_freq=8.0, end_freq=12.0),
        )
        for port_number, z_value, orientation in (
            ("1", 0, "zmin"),
            ("2", 100, "zmax"),
        ):
            cst_case.require_success(
                "define-port",
                _project_arguments(
                    cst_case,
                    port_number=port_number,
                    x_min=-11.43,
                    x_max=11.43,
                    y_min=-5.08,
                    y_max=5.08,
                    z_min=z_value,
                    z_max=z_value,
                    orientation=orientation,
                ),
            )

        cst_case.require_success(
            "start-simulation-async",
            {"project_path": cst_case.project_path},
            timeout=60,
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            state = cst_case.require_success(
                "is-simulation-running",
                {"project_path": cst_case.project_path},
            )
            if state.get("running") is True:
                saw_running = True
                break
            time.sleep(0.25)
        assert saw_running, "求解器启动后 30 秒内未观察到 running=True"
    finally:
        stop_result = cst_case.call(
            "stop-simulation",
            {"project_path": cst_case.project_path},
            timeout=60,
        )
        if stop_result.get("status") == "success":
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                state = cst_case.require_success(
                    "is-simulation-running",
                    {"project_path": cst_case.project_path},
                )
                if state.get("running") is False:
                    saw_stopped = True
                    break
                time.sleep(0.25)
        for component, name in reversed(walls):
            if cst_case.shared.entity_exists(component, name):
                cst_case.shared.delete_entity(component, name)

    assert stop_result.get("status") == "success", stop_result
    assert saw_stopped, "强制停止后 30 秒内求解器仍处于运行状态"


def test_80_material_definition_is_accepted_by_real_geometry(cst_case: Any) -> None:
    """材料定义必须由后续真实建模接受，而不是只检查提交状态。"""
    material_name = "FR-4 (loss free)"
    cst_case.require_success(
        "define-material-from-mtd",
        {"project_path": cst_case.project_path, "material_name": material_name},
    )
    name = cst_case.name("material_probe")
    cst_case.require_success(
        "define-brick",
        _project_arguments(
            cst_case,
            name=name,
            component=COMPONENT,
            material=material_name,
            x_min=140,
            x_max=141,
            y_min=140,
            y_max=141,
            z_min=140,
            z_max=141,
        ),
    )
    cst_case.shared.register_entity(COMPONENT, name)
    assert cst_case.shared.entity_exists(COMPONENT, name)
    cst_case.shared.delete_entity(COMPONENT, name)


def test_90_parameter_scan_writes_reads_and_restores_values(cst_case: Any) -> None:
    """参数扫描只验证真实写入、逐次回读和原值恢复，不启动求解器。"""
    listed = cst_case.require_success(
        "list-parameters",
        {"project_path": cst_case.project_path},
    )
    parameters = dict(listed.get("parameters", {}))
    selected_name = ""
    original = 0.0
    for name, entry in parameters.items():
        value = entry.get("value") if isinstance(entry, dict) else entry
        try:
            original = float(value)
        except (TypeError, ValueError):
            continue
        selected_name = str(name)
        break
    assert selected_name, f"基准工程没有可写的数值参数：{parameters}"

    first = original + (0.5 if original == 0 else abs(original) * 0.01)
    second = original + (1.0 if original == 0 else abs(original) * 0.02)
    try:
        for expected in (first, second):
            cst_case.require_success(
                "change-parameter",
                {
                    "project_path": cst_case.project_path,
                    "name": selected_name,
                    "value": expected,
                },
            )
            readback = cst_case.require_success(
                "list-parameters",
                {"project_path": cst_case.project_path},
            )
            actual_entry = readback["parameters"][selected_name]
            actual = actual_entry.get("value") if isinstance(actual_entry, dict) else actual_entry
            assert float(actual) == pytest.approx(expected)
    finally:
        restored = cst_case.call(
            "change-parameter",
            {
                "project_path": cst_case.project_path,
                "name": selected_name,
                "value": original,
            },
        )
        assert restored.get("status") == "success", restored

    final = cst_case.require_success(
        "list-parameters",
        {"project_path": cst_case.project_path},
    )
    final_entry = final["parameters"][selected_name]
    final_value = final_entry.get("value") if isinstance(final_entry, dict) else final_entry
    assert float(final_value) == pytest.approx(original)
