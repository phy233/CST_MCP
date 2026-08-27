from __future__ import annotations

import ast
import inspect
import types
import typing

from jsonschema import validate

from cst_runtime.api.atomic import atomic_handler_map
from cst_runtime.tools import all_defs, build_args_templates, build_direct_arg_specs


def _direct_forward_target(handler):
    """解析形如 ``return module.function(**args)`` 的直接转发处理器。"""
    tree = ast.parse(inspect.getsource(handler))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        forwards_args = any(
            keyword.arg is None
            and isinstance(keyword.value, ast.Name)
            and keyword.value.id == "args"
            for keyword in node.keywords
        )
        if not forwards_args:
            continue
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            owner = handler.__globals__.get(node.func.value.id)
            if owner is not None:
                return getattr(owner, node.func.attr, None)
    return None


def _json_scalar_types(annotation) -> set[str]:
    """把 Python 标量类型注解映射为等价 JSON Schema 类型。"""
    origin = typing.get_origin(annotation)
    if origin in (typing.Union, types.UnionType):
        result: set[str] = set()
        for item in typing.get_args(annotation):
            if item is not type(None):
                result.update(_json_scalar_types(item))
        return result
    if annotation is str:
        return {"string"}
    if annotation is bool:
        return {"boolean"}
    if annotation is int:
        return {"integer"}
    if annotation is float:
        return {"number"}
    return set()


def test_direct_forward_schemas_match_python_scalar_annotations() -> None:
    handlers = atomic_handler_map()
    mismatches: list[str] = []

    for tool_name, definition in all_defs().items():
        handler = handlers[definition["handler"]]
        target = _direct_forward_target(handler)
        if target is None:
            continue
        hints = typing.get_type_hints(target)
        properties = definition.get("json_schema", {}).get("properties", {})
        for field_name, property_schema in properties.items():
            expected = _json_scalar_types(hints.get(field_name))
            if not expected:
                continue
            declared = property_schema.get("type")
            declared_types = set(declared if isinstance(declared, list) else [declared])
            if declared_types != expected:
                mismatches.append(
                    f"{tool_name}.{field_name}: {sorted(declared_types)} != {sorted(expected)}"
                )

    assert mismatches == []


def test_define_brick_schema_accepts_decimal_substrate_thickness() -> None:
    schema = all_defs()["define-brick"]["json_schema"]

    validate(
        {
            "project_path": "D:/work/working.cst",
            "name": "substrate",
            "component": "antenna",
            "material": "FR-4 (loss free)",
            "x_min": -40,
            "x_max": 40,
            "y_min": -30,
            "y_max": 30,
            "z_min": 0,
            "z_max": 1.6,
        },
        schema,
    )


def test_define_units_schema_exposes_cst_temperature_names() -> None:
    schema = all_defs()["define-units"]["json_schema"]
    temperature = schema["properties"]["temperature"]

    assert temperature["default"] == "Celsius"
    assert temperature["enum"] == ["Celsius", "Kelvin", "Fahrenheit"]
    validate(
        {
            "project_path": "D:/work/working.cst",
            "length": "mm",
            "frequency": "GHz",
            "temperature": "Celsius",
        },
        schema,
    )


def test_change_solver_type_schema_uses_2022_manual_values() -> None:
    solver_type = all_defs()["change-solver-type"]["json_schema"]["properties"]["solver_type"]

    assert solver_type["enum"] == [
        "HF Time Domain",
        "HF Eigenmode",
        "HF Frequency Domain",
        "HF IntegralEq",
        "HF Multilayer",
        "HF Asymptotic",
        "LF EStatic",
        "LF MStatic",
        "LF Stationary Current",
        "LF Frequency Domain",
        "LF Time Domain (MQS)",
        "PT Tracking",
        "PT Wakefields",
        "PT PIC",
        "Thermal Steady State",
        "Thermal Transient",
        "Mechanics",
    ]


def test_union_scalar_schema_remains_available_to_cli_helpers() -> None:
    assert build_args_templates()["define-brick"]["x_min"] == -10
    assert "x_min" in build_direct_arg_specs()["define-brick"]


def test_all_schema_examples_and_defaults_validate() -> None:
    failures: list[str] = []

    for tool_name, definition in all_defs().items():
        properties = definition.get("json_schema", {}).get("properties", {})
        for field_name, property_schema in properties.items():
            samples = list(property_schema.get("examples", []))
            if "default" in property_schema:
                samples.append(property_schema["default"])
            for sample in samples:
                try:
                    validate(sample, property_schema)
                except Exception as exc:
                    failures.append(f"{tool_name}.{field_name}: {exc}")

    assert failures == []


def test_coordinate_metadata_is_concise_and_actionable() -> None:
    """坐标说明应覆盖调用前计算要点，同时保持简短。"""
    definitions = all_defs()
    coordinate_fields = {
        "create-hollow-sweep": (
            "x_min1", "x_max1", "y_min1", "y_max1", "z1",
            "x_min2", "x_max2", "y_min2", "y_max2", "z2",
        ),
        "create-loft-sweep": (
            "x_min1", "x_max1", "y_min1", "y_max1", "z1",
            "x_min2", "x_max2", "y_min2", "y_max2", "z2",
        ),
        "define-analytical-curve": ("law_x", "law_y", "law_z"),
        "define-brick": ("x_min", "x_max", "y_min", "y_max", "z_min", "z_max"),
        "define-cone": ("axis", "axis_min", "axis_max", "x_center", "y_center"),
        "define-cylinder": ("axis", "axis_min", "axis_max", "x_center", "y_center"),
        "define-extrude-curve": ("curve", "thickness"),
        "define-polygon-3d": ("points",),
        "define-rectangle": ("x_min", "x_max", "y_min", "y_max"),
        "set-background-with-space": (
            "x_min_space", "x_max_space", "y_min_space", "y_max_space",
            "z_min_space", "z_max_space",
        ),
        "set-probe": ("x_pos", "y_pos", "z_pos"),
        "transform-curve": (
            "center_x", "center_y", "center_z",
            "plane_normal_x", "plane_normal_y", "plane_normal_z",
        ),
        "transform-shape": (
            "center_x", "center_y", "center_z",
            "plane_normal_x", "plane_normal_y", "plane_normal_z",
            "angle_x", "angle_y", "angle_z",
        ),
        "define-port": ("x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "orientation"),
    }

    for tool_name, field_names in coordinate_fields.items():
        definition = definitions[tool_name]
        assert len(definition["description"]) <= 240
        assert "example" not in definition["description"].lower()
        properties = definition["json_schema"]["properties"]
        for field_name in field_names:
            field_description = properties[field_name].get("description", "")
            assert field_description
            assert len(field_description) <= 140
            assert "example" not in field_description.lower()

    polygon = definitions["define-polygon-3d"]
    assert "active X/Y/Z or local U/V/W" in polygon["description"]
    assert "verify coplanarity" in polygon["description"]
    assert "n dot (Pi-P1)=0" in polygon["json_schema"]["properties"]["points"]["description"]

    extrude = definitions["define-extrude-curve"]
    assert "closed planar curve" in extrude["description"]
    assert "Positive thickness follows its ordered normal" in extrude["description"]
    assert "Compute the normal and sign first" in extrude["description"]
    assert "negative along -n" in extrude["json_schema"]["properties"]["thickness"]["description"]
    assert "consumes it on success" in extrude["json_schema"]["properties"]["curve"]["description"]

    assert "differentiable" in definitions["define-analytical-curve"]["description"]
    assert "active X/Y/Z or local U/V/W" in definitions["define-brick"]["description"]
    for tool_name in ("define-cone", "define-cylinder"):
        properties = definitions[tool_name]["json_schema"]["properties"]
        required = definitions[tool_name]["json_schema"]["required"]
        assert "axis_min/axis_max set the axial" in definitions[tool_name]["description"]
        assert "mapped to axis-specific VBA setters" in definitions[tool_name]["description"]
        assert "axis_min" in properties and "axis_max" in properties
        assert "z_min" not in properties and "z_max" not in properties
        assert "axis_min" in required and "axis_max" in required
    assert "bottom_radius is at the lower bound" in definitions["define-cone"]["description"]

    assert "global X/Y/Z position" in definitions["set-probe"]["description"]
    assert "global X/Y/Z bounds" in definitions["set-background-with-space"]["description"]
    assert "*min radiates +axis" in definitions["define-port"]["description"]

    transform_shape = definitions["transform-shape"]
    assert "Mirror uses PlaneNormal; rotate uses Angle" in transform_shape["description"]
    assert "do not define a rotate axis" in transform_shape["description"]
    assert "no separate plane-normal argument" in definitions["define-loft"]["description"]
