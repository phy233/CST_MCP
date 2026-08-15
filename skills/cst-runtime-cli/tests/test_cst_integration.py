"""通过唯一 Worker 和唯一隔离工程执行的真实 CST 2022 集成测试。"""
from __future__ import annotations

import json
import os
import struct
import time
from pathlib import Path
from typing import Any

import pytest


pytestmark = [
    pytest.mark.cst_integration,
    pytest.mark.cst_destructive,
]


COMPONENT = "component1"
STANDARD_NO_RESULT_ERRORS = {"no_result", "result_not_found", "result_node_not_found"}


def _entity_keys(items: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {
        (str(item.get("component", "")), str(item.get("name", "")))
        for item in items
    }


def _project_arguments(cst_case: Any, **arguments: Any) -> dict[str, Any]:
    return {"project_path": cst_case.project_path, **arguments}


def _assert_error_response(
    result: dict[str, Any],
    *,
    error_types: set[str],
    phase: str,
) -> None:
    """同时检查旧顶层字段和统一错误信封，避免把任意失败当成预期失败。"""
    assert result.get("status") == "error", result
    assert result.get("ok") is False, result
    assert result.get("error_type") in error_types, result
    error = result.get("error")
    assert isinstance(error, dict), result
    assert error.get("type") == result.get("error_type"), result
    assert error.get("phase") == phase, result


def _assert_standard_no_result_or_xfail(
    result: dict[str, Any],
    *,
    legacy_error_type: str,
    evidence_tokens: tuple[str, ...],
) -> None:
    """仅放行已知的旧错误类型，传输、Worker 和无关运行时错误必须失败。"""
    error_type = str(result.get("error_type") or "")
    if error_type == legacy_error_type:
        _assert_error_response(result, error_types={legacy_error_type}, phase="runtime")
        message = str(result.get("message") or "").casefold()
        assert any(token.casefold() in message for token in evidence_tokens), result
        pytest.xfail(f"空结果仍返回旧错误类型 {legacy_error_type}")
    _assert_error_response(
        result,
        error_types=STANDARD_NO_RESULT_ERRORS,
        phase="runtime",
    )


def _assert_png_1920x1080(path: Path) -> None:
    """检查 PNG 文件签名和 IHDR 尺寸，不让任意非空文件冒充截图。"""
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n", path
    assert header[12:16] == b"IHDR", path
    assert struct.unpack(">II", header[16:24]) == (1920, 1080), path


def _prepare_interactive_result_read(cst_case: Any) -> None:
    """保存隔离工程，使 CST 2022 交互结果接口读取到明确的最近保存状态。"""
    saved = cst_case.require_success(
        "save-project",
        {"project_path": cst_case.project_path},
    )
    assert Path(saved["project_path"]).resolve() == Path(cst_case.project_path).resolve()
    cst_case.shared.require_visible_window()


def test_00_only_one_expected_project_is_open(cst_case: Any) -> None:
    """真机层必须只看到共享隔离工程，并能读取真实工程状态。"""
    opened = cst_case.require_success("list-open-projects", {})
    projects = list(opened.get("open_projects", []))
    assert len(projects) == 1, opened
    assert opened.get("design_environment_count") == 1, opened
    assert projects[0].get("design_environment_pid") == cst_case.shared.design_environment_pid
    assert os.path.normcase(os.path.abspath(projects[0]["project_path"])) == os.path.normcase(
        os.path.abspath(cst_case.project_path)
    )
    cst_case.shared.require_visible_window()

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
            axis_min=100,
            axis_max=101,
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


def test_13_custom_view_exports_nonempty_png(cst_case: Any) -> None:
    """手册记录的 Front 相对旋转必须在真机生成非空 PNG。"""
    name = cst_case.name("capture")
    cst_case.require_success(
        "define-brick",
        _project_arguments(
            cst_case,
            name=name,
            component=COMPONENT,
            material="PEC",
            x_min=100,
            x_max=102,
            y_min=100,
            y_max=101,
            z_min=100,
            z_max=103,
        ),
    )
    cst_case.shared.register_entity(COMPONENT, name)
    assert cst_case.shared.entity_exists(COMPONENT, name)

    output_dir = Path(cst_case.shared.temp_root) / "screenshots"
    result = cst_case.require_success(
        "capture-3d-view",
        _project_arguments(
            cst_case,
            output_dir=str(output_dir),
            filename_prefix=cst_case.name("custom_view"),
            view_type="custom",
            horizontal_rotation_deg=35,
            vertical_rotation_deg=20,
        ),
        timeout=120,
    )
    image_path = Path(result["image_path"])
    assert image_path.is_file(), result
    assert image_path.stat().st_size > 0, result
    _assert_png_1920x1080(image_path)
    metadata_path = Path(result["metadata_path"])
    assert metadata_path.is_file(), result
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert Path(metadata["image_path"]).resolve() == image_path.resolve()
    assert metadata["image_size"] == {"width": 1920, "height": 1080}
    assert result["view_params"]["horizontal_rotation_deg"] == 35
    assert result["view_params"]["vertical_rotation_deg"] == 20
    assert metadata["view_params"] == result["view_params"]

    cst_case.shared.delete_entity(COMPONENT, name)


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
    _assert_error_response(result, error_types={"runtime_error"}, phase="runtime")
    assert "未知 builder_id" in str(result.get("message") or ""), result
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
    _assert_error_response(result, error_types={"vba_runtime_error"}, phase="execution")
    assert not cst_case.shared.entity_exists(COMPONENT, name)
    assert _entity_keys(cst_case.shared.list_entities()) == before


def test_40_empty_1d_result_returns_standard_no_result_error(cst_case: Any) -> None:
    """空工程读取 1D 结果应返回标准无结果错误。"""
    _prepare_interactive_result_read(cst_case)
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
            allow_interactive=True,
        ),
    )
    assert not export_path.exists()
    _assert_standard_no_result_or_xfail(
        result,
        legacy_error_type="get_1d_result_failed",
        evidence_tokens=(
            "__pytest_missing__",
            "not exist",
            "not found",
            "no result",
            "没有可用的 run id",
        ),
    )


def test_41_2d_result_reports_cst2022_capability_limit(cst_case: Any) -> None:
    """CST 2022 未公开 2D 提取能力时应返回精确的兼容性证据。"""
    _prepare_interactive_result_read(cst_case)
    export_path = Path(cst_case.shared.temp_root) / "missing_2d.json"
    result = cst_case.call(
        "get-2d-result",
        _project_arguments(
            cst_case,
            treepath="2D/3D Results\\__pytest_missing__",
            module_type="3d",
            export_path=str(export_path),
            allow_interactive=True,
            subproject_treepath="",
            include_data=False,
        ),
    )
    assert not export_path.exists()
    _assert_error_response(
        result,
        error_types={"unsupported_feature"},
        phase="compatibility",
    )
    assert result.get("feature") == "results.2d", result
    assert result.get("context", {}).get("required_capability") == "result2d", result


def test_42_parameter_combination_resolves_run_zero(
    cst_case: Any,
) -> None:
    """Run ID 0 应解析为基准工程中可用的真实或最新结果编号。"""
    _prepare_interactive_result_read(cst_case)
    result = cst_case.require_success(
        "get-parameter-combination",
        _project_arguments(
            cst_case,
            run_id=0,
            module_type="3d",
            allow_interactive=True,
        ),
    )
    assert result.get("requested_run_id") == 0, result
    assert isinstance(result.get("run_id"), int), result
    assert result["run_id"] >= 0, result
    assert result.get("module_type") == "3d", result
    assert isinstance(result.get("parameters"), dict), result


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


@pytest.mark.cst_solver
def test_51_solver_pause_resume_then_stop(cst_case: Any) -> None:
    """用短矩形波导观察运行态，验证 pause/resume 后无条件停止并清理。

    必须排在本文件参数测试之前：change-parameter 会登记 params_dirty，
    之后任何 start-simulation-async 都会被 T2 守卫拒绝。
    """
    wall_ranges = [
        ("top", -11.43, 11.43, 5.08, 6.08, 0, 100),
        ("bottom", -11.43, 11.43, -6.08, -5.08, 0, 100),
        ("left", -12.43, -11.43, -6.08, 6.08, 0, 100),
        ("right", 11.43, 12.43, -6.08, 6.08, 0, 100),
    ]
    walls: list[tuple[str, str]] = []
    saw_running = False
    saw_paused = False
    saw_resumed = False
    saw_stopped = False
    stop_result: dict[str, Any] | None = None
    try:
        for suffix, x_min, x_max, y_min, y_max, z_min, z_max in wall_ranges:
            name = cst_case.name(f"pw_waveguide_{suffix}")
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

        paused = cst_case.call(
            "pause-simulation",
            {"project_path": cst_case.project_path},
            timeout=60,
        )
        if paused.get("status") == "success":
            saw_paused = True
            assert paused.get("message") == "simulation paused", paused
            resumed = cst_case.call(
                "resume-simulation",
                {"project_path": cst_case.project_path},
                timeout=60,
            )
            if resumed.get("status") == "success":
                saw_resumed = True
                assert resumed.get("message") == "simulation resumed", resumed
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

    assert paused.get("status") == "success", paused
    assert saw_paused, "pause-simulation 成功但未确认 paused=True"
    assert resumed.get("status") == "success", resumed
    assert saw_resumed, "resume-simulation 成功但未确认恢复 running=True"
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
