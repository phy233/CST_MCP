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
