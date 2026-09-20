"""批量建模模板的公开契约；同时用于发现工具和参数模板生成。"""
from __future__ import annotations

from typing import Any


COORDINATE = {"type": ["number", "string"], "minLength": 1}
VECTOR = {"type": "array", "items": COORDINATE, "minItems": 3, "maxItems": 3}
NAME = {"type": "string", "minLength": 1, "pattern": r'^[\x20-\x21\x23-\x39\x3B-\x7E]+$'}

BUILTIN_TEMPLATES: dict[str, dict[str, Any]] = {
    "create-brick-template": {
        "description": "每个 code 创建一次方块样板，再按相对位移复制；origin 是最小角点。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "component": {**NAME, "default": "array"},
                "name": {**NAME, "description": "省略时使用 brick_<code>；不同 code 应使用不同名称。"},
                "material": {"type": "string", "minLength": 1, "default": "PEC"},
                "size": {**VECTOR, "default": [1, 1, 1]},
                "origin": {**VECTOR, "default": [0, 0, 0]},
            },
            "additionalProperties": False,
        },
        "example_parameters": {"component": "array", "name": "cell_A", "material": "PEC",
                               "size": [2, 2, 0.1], "origin": [-1, -1, 0]},
        "preserves_source": False,
    },
    "copy-template": {
        "description": "复制同一工程、同一 component 下已建好的样板实体并平移；始终保留源样板。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "component": NAME,
                "reference_names": {"type": "array", "items": NAME, "minItems": 1,
                                    "uniqueItems": True},
            },
            "required": ["component", "reference_names"],
            "additionalProperties": False,
        },
        "example_parameters": {"component": "cell_template", "reference_names": ["patch", "substrate"]},
        "preserves_source": True,
    },
}

EXAMPLE_UNITS = {"A": {"builder_id": "create-brick-template",
                        "parameters": BUILTIN_TEMPLATES["create-brick-template"]["example_parameters"]}}
EXAMPLE_ELEMENTS = [{"code": "A", "x": 0, "y": 0, "z": 0},
                    {"code": "A", "x": 5, "y": 0, "z": 0}]
