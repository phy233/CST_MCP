"""几何建模与变换工具的真实 CST 2022 集成测试。"""
from __future__ import annotations

from typing import Any

import pytest

from cst_helpers import (
    COMPONENT,
    assert_error_response,
    entity_keys,
    project_arguments,
)


pytestmark = [
    pytest.mark.cst_integration,
    pytest.mark.cst_destructive,
]


def _brick(cst_case: Any, name: str, *, x_min: float, x_max: float) -> None:
    cst_case.require_success(
        "define-brick",
        project_arguments(
            cst_case,
            name=name,
            component=COMPONENT,
            material="PEC",
            x_min=x_min,
            x_max=x_max,
            y_min=100,
            y_max=101,
            z_min=100,
            z_max=101,
        ),
    )
    cst_case.shared.register_entity(COMPONENT, name)
    assert cst_case.shared.entity_exists(COMPONENT, name)


def _delete_all_new(cst_case: Any, before: set[tuple[str, str]]) -> None:
    created = sorted(entity_keys(cst_case.shared.list_entities()) - before)
    assert created, "变换后没有出现新实体"
    for component, name in created:
        cst_case.shared.register_entity(component, name)
        assert cst_case.shared.entity_exists(component, name)
    for component, name in reversed(created):
        cst_case.shared.delete_entity(component, name)


def test_cone_create_query_delete_query(cst_case: Any) -> None:
    name = cst_case.name("cone")
    assert not cst_case.shared.entity_exists(COMPONENT, name)
    cst_case.require_success(
        "define-cone",
        project_arguments(
            cst_case,
            name=name,
            component=COMPONENT,
            material="PEC",
            bottom_radius=0.5,
            top_radius=1.5,
            axis="z",
            axis_min=100,
            axis_max=102,
            x_center=103,
            y_center=103,
        ),
    )
    cst_case.shared.register_entity(COMPONENT, name)
    assert cst_case.shared.entity_exists(COMPONENT, name)
    cst_case.shared.delete_entity(COMPONENT, name)


def test_polygon_extrude_creates_solid(cst_case: Any) -> None:
    polygon = cst_case.name("poly")
    solid = cst_case.name("extrude")
    cst_case.require_success(
        "define-polygon-3d",
        project_arguments(
            cst_case,
            name=polygon,
            curve="curve1",
            points=[
                [150, 150, 0],
                [152, 150, 0],
                [152, 152, 0],
                [150, 152, 0],
                [150, 150, 0],
            ],
        ),
    )
    cst_case.require_success(
        "define-extrude-curve",
        project_arguments(
            cst_case,
            name=solid,
            component=COMPONENT,
            material="PEC",
            curve=f"curve1:{polygon}",
            thickness=1,
        ),
    )
    cst_case.shared.register_entity(COMPONENT, solid)
    assert cst_case.shared.entity_exists(COMPONENT, solid)
    cst_case.shared.delete_entity(COMPONENT, solid)


def test_boolean_subtract_consumes_tool(cst_case: Any) -> None:
    target = cst_case.name("sub_target")
    tool = cst_case.name("sub_tool")
    _brick(cst_case, target, x_min=110, x_max=112)
    _brick(cst_case, tool, x_min=110.5, x_max=111.5)
    cst_case.require_success(
        "boolean-subtract",
        project_arguments(
            cst_case,
            target=f"{COMPONENT}:{target}",
            tool=f"{COMPONENT}:{tool}",
        ),
    )
    assert cst_case.shared.entity_exists(COMPONENT, target)
    assert not cst_case.shared.entity_exists(COMPONENT, tool)
    cst_case.shared.forget_entity(COMPONENT, tool)
    cst_case.shared.delete_entity(COMPONENT, target)


def test_boolean_intersect_consumes_shape2(cst_case: Any) -> None:
    first = cst_case.name("isect_a")
    second = cst_case.name("isect_b")
    _brick(cst_case, first, x_min=120, x_max=122)
    _brick(cst_case, second, x_min=121, x_max=123)
    cst_case.require_success(
        "boolean-intersect",
        project_arguments(
            cst_case,
            shape1=f"{COMPONENT}:{first}",
            shape2=f"{COMPONENT}:{second}",
        ),
    )
    assert cst_case.shared.entity_exists(COMPONENT, first)
    assert not cst_case.shared.entity_exists(COMPONENT, second)
    cst_case.shared.forget_entity(COMPONENT, second)
    cst_case.shared.delete_entity(COMPONENT, first)


def test_boolean_insert_consumes_shape2(cst_case: Any) -> None:
    outer = cst_case.name("insert_outer")
    inner = cst_case.name("insert_inner")
    _brick(cst_case, outer, x_min=130, x_max=134)
    _brick(cst_case, inner, x_min=131, x_max=133)
    cst_case.require_success(
        "boolean-insert",
        project_arguments(
            cst_case,
            shape1=f"{COMPONENT}:{outer}",
            shape2=f"{COMPONENT}:{inner}",
        ),
    )
    # CST Insert 在目标上挖腔但保留工具实体，两个实体都必须仍存在。
    assert cst_case.shared.entity_exists(COMPONENT, outer)
    assert cst_case.shared.entity_exists(COMPONENT, inner)
    cst_case.shared.delete_entity(COMPONENT, inner)
    cst_case.shared.delete_entity(COMPONENT, outer)


def test_transform_shape_mirror_adds_copy(cst_case: Any) -> None:
    name = cst_case.name("mirror_src")
    _brick(cst_case, name, x_min=140, x_max=141)
    before = entity_keys(cst_case.shared.list_entities())
    cst_case.require_success(
        "transform-shape",
        project_arguments(
            cst_case,
            shape_name=f"{COMPONENT}:{name}",
            transform_type="mirror",
            center_x="0",
            center_y="0",
            center_z="0",
            plane_normal_x="0",
            plane_normal_y="1",
            plane_normal_z="0",
        ),
    )
    _delete_all_new(cst_case, before)
    cst_case.shared.delete_entity(COMPONENT, name)


def test_transform_shape_rotate_adds_copy(cst_case: Any) -> None:
    name = cst_case.name("rotate_src")
    _brick(cst_case, name, x_min=145, x_max=146)
    before = entity_keys(cst_case.shared.list_entities())
    cst_case.require_success(
        "transform-shape",
        project_arguments(
            cst_case,
            shape_name=f"{COMPONENT}:{name}",
            transform_type="rotate",
            center_x="0",
            center_y="0",
            center_z="0",
            plane_normal_x="0",
            plane_normal_y="0",
            plane_normal_z="1",
            angle_z="90",
        ),
    )
    _delete_all_new(cst_case, before)
    cst_case.shared.delete_entity(COMPONENT, name)


def test_transform_shape_nonempty_destination_unsupported(cst_case: Any) -> None:
    name = cst_case.name("dest_src")
    _brick(cst_case, name, x_min=148, x_max=149)
    before = entity_keys(cst_case.shared.list_entities())
    result = cst_case.call(
        "transform-shape",
        project_arguments(
            cst_case,
            shape_name=f"{COMPONENT}:{name}",
            transform_type="translate",
            center_x="0",
            center_y="0",
            center_z="0",
            plane_normal_x="0",
            plane_normal_y="0",
            plane_normal_z="1",
            destination="other_component",
        ),
    )
    assert_error_response(
        result,
        error_types={"unsupported_feature"},
        phase="compatibility",
    )
    assert result["feature"] == "transform.destination", result
    assert result["context"]["required_capability"] == "transform.destination", result
    assert entity_keys(cst_case.shared.list_entities()) == before
    cst_case.shared.delete_entity(COMPONENT, name)


def test_rename_entity_old_to_new(cst_case: Any) -> None:
    old = cst_case.name("rename_old")
    new = cst_case.name("rename_new")
    _brick(cst_case, old, x_min=160, x_max=161)
    cst_case.require_success(
        "rename-entity",
        project_arguments(
            cst_case,
            old_name=f"{COMPONENT}:{old}",
            new_name=f"{COMPONENT}:{new}",
        ),
    )
    assert not cst_case.shared.entity_exists(COMPONENT, old)
    cst_case.shared.forget_entity(COMPONENT, old)
    cst_case.shared.register_entity(COMPONENT, new)
    assert cst_case.shared.entity_exists(COMPONENT, new)
    cst_case.shared.delete_entity(COMPONENT, new)


def test_set_color_and_change_material(cst_case: Any) -> None:
    material = "Copper (pure)"
    listed = cst_case.require_success("list-materials", {})
    assert material in listed.get("material_names", []), listed
    # 材料必须先经 define-material-from-mtd 落进工程，Solid.ChangeMaterial 才能解析。
    cst_case.require_success(
        "define-material-from-mtd",
        project_arguments(cst_case, material_name=material),
    )
    name = cst_case.name("colored")
    _brick(cst_case, name, x_min=170, x_max=171)
    cst_case.require_success(
        "set-entity-color",
        project_arguments(
            cst_case,
            shape_name=f"{COMPONENT}:{name}",
            r=255,
            g=0,
            b=0,
        ),
    )
    cst_case.require_success(
        "change-material",
        project_arguments(
            cst_case,
            shape_name=f"{COMPONENT}:{name}",
            material=material,
        ),
    )
    assert cst_case.shared.entity_exists(COMPONENT, name)
    cst_case.shared.delete_entity(COMPONENT, name)


def test_define_analytical_curve_success(cst_case: Any) -> None:
    """解析曲线无实体树读回通道，只验证提交成功（残留曲线靠会话回滚）。"""
    result = cst_case.require_success(
        "define-analytical-curve",
        project_arguments(
            cst_case,
            name=cst_case.name("acurve"),
            curve="curve1",
            law_x="t",
            law_y="0",
            law_z="0",
            param_start="0",
            param_end="10",
        ),
    )
    assert result["compatibility"]["profile"] == "cst2022", result


def test_create_loft_sweep_creates_solid(cst_case: Any) -> None:
    name = cst_case.name("loft")
    before = entity_keys(cst_case.shared.list_entities())
    result = cst_case.call(
        "create-loft-sweep",
        project_arguments(
            cst_case,
            name=name,
            component=COMPONENT,
            material="PEC",
            x_min1=-1,
            x_max1=1,
            y_min1=-1,
            y_max1=1,
            z1=150,
            x_min2=-2,
            x_max2=2,
            y_min2=-2,
            y_max2=2,
            z2=154,
        ),
    )
    assert result.get("status") == "success", result
    created = sorted(entity_keys(cst_case.shared.list_entities()) - before)
    assert created, result
    for component, item in created:
        cst_case.shared.register_entity(component, item)
    for component, item in reversed(created):
        cst_case.shared.delete_entity(component, item)


def test_create_hollow_sweep_creates_solid(cst_case: Any) -> None:
    name = cst_case.name("hollow")
    before = entity_keys(cst_case.shared.list_entities())
    result = cst_case.call(
        "create-hollow-sweep",
        project_arguments(
            cst_case,
            name=name,
            component=COMPONENT,
            material="PEC",
            x_min1=-2,
            x_max1=2,
            y_min1=-2,
            y_max1=2,
            z1=160,
            x_min2=-3,
            x_max2=3,
            y_min2=-3,
            y_max2=3,
            z2=164,
            wall_thickness=0.2,
        ),
    )
    assert result.get("status") == "success", result
    created = sorted(entity_keys(cst_case.shared.list_entities()) - before)
    assert created, result
    for component, item in created:
        cst_case.shared.register_entity(component, item)
    for component, item in reversed(created):
        cst_case.shared.delete_entity(component, item)


def test_create_horn_segment_creates_solid(cst_case: Any) -> None:
    """实体名由大整数 segment_id 决定，内部布尔减消耗内锥。"""
    segment_id = 70001
    before = entity_keys(cst_case.shared.list_entities())
    result = cst_case.call(
        "create-horn-segment",
        project_arguments(
            cst_case,
            segment_id=segment_id,
            bottom_radius=1,
            top_radius=2,
            z_min=170,
            z_max=173,
        ),
    )
    assert result.get("status") == "success", result
    assert cst_case.shared.entity_exists(COMPONENT, str(segment_id)), result
    created = sorted(entity_keys(cst_case.shared.list_entities()) - before)
    for component, item in created:
        cst_case.shared.register_entity(component, item)
    for component, item in reversed(created):
        cst_case.shared.delete_entity(component, item)
