"""现有原子操作的 handler 与元数据发现。

该模块位于 API 层，CLI 与 worker 共用这里的单一清单。工具模块中的可选依赖
均在实际调用时加载，因此发现清单不会要求安装全部可选依赖。
"""
from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Any, Callable


_TOOL_MODULES = (
    "simulation",
    "modeling",
    "project",
    "results",
    "farfield",
    "session",
    "audit",
    "workspace",
    "optimization",
    "doe",
    "em_setup",
    "metasurface",
    "history",
    "interaction",
)


def _output_schema(name: str) -> dict[str, Any]:
    """返回以 OperationResult 为基础、并按新结果接口细化的输出 Schema。"""
    properties: dict[str, Any] = {
        "status": {"type": "string", "enum": ["success", "error"]},
        "ok": {"type": "boolean"},
        "error_type": {"type": "string"},
        "message": {"type": "string"},
        "error": {"type": "object"},
        "context": {"type": "object"},
    }
    if name in {"list-sparameter-results", "list-field-results"}:
        properties.update({
            "project_path": {"type": "string"},
            "count": {"type": "integer", "minimum": 0},
            "results": {"type": "array", "items": {"type": "object"}},
        })
    elif name == "export-sparameter":
        properties.update({
            "project_path": {"type": "string"},
            "result_path": {"type": "string"},
            "run_id": {"type": "integer", "minimum": 0},
            "output_path": {"type": "string"},
            "point_count": {"type": "integer", "minimum": 0},
            "result_metric": {"type": "object"},
            "s11_metric": {"type": ["object", "null"]},
        })
    elif name == "run-experiment":
        properties.update({
            "project_path": {"type": "string"},
            "run_id": {"type": "integer", "minimum": 0},
            "completion_result_paths": {
                "type": "array", "items": {"type": "string"},
            },
            "result_metrics": {"type": "array", "items": {"type": "object"}},
            "s11_metric": {"type": ["object", "null"]},
            "solver_completed": {"type": "boolean"},
        })
    elif name == "analyze-metasurface-sparameters":
        properties.update({
            "output_path": {"type": "string"},
            "file_size": {"type": "integer", "minimum": 1},
            "run_id": {"type": "integer", "minimum": 0},
            "frequency_range_ghz": {
                "type": "array", "minItems": 2, "maxItems": 2,
                "items": {"type": "number"},
            },
            "frequency_count": {"type": "integer", "minimum": 1},
            "channel_count": {"type": "integer", "minimum": 1},
            "summary": {"type": "object"},
            "warning_count": {"type": "integer", "minimum": 0},
            "warnings": {"type": "array", "items": {"type": "object"}},
        })
    elif name in {"inspect-boundary", "inspect-floquet-ports", "inspect-plane-wave", "list-monitors"}:
        properties.update({
            "project_path": {"type": "string"},
            "faces": {"type": "object"},
            "unit_cell_scan": {"type": "object"},
            "ports": {"type": "array", "items": {"type": "object"}},
            "plane_wave": {"type": "object"},
            "monitors": {"type": "array", "items": {"type": "object"}},
            "count": {"type": "integer", "minimum": 0},
        })
    elif name in {"define-unit-cell-boundary", "define-floquet-port", "define-plane-wave"}:
        properties.update({
            "project_path": {"type": "string"},
            "submission": {"type": "string"},
            "execution": {"type": "string"},
            "requested": {"type": "object"},
            "actual": {"type": "object"},
            "unverified_fields": {"type": "array", "items": {"type": "string"}},
        })
    elif name == "configure-frequency-domain-solver":
        properties.update({
            "project_path": {"type": "string"},
            "submission": {"type": "string"},
            "execution": {"type": "string"},
            "solver_type": {"type": "string"},
            "mesh_method": {"type": "string"},
            "excitation": {"type": "object"},
            "untouched_settings": {"type": "string"},
        })
    elif name.startswith("export-"):
        properties.update({
            "project_path": {"type": "string"},
            "output_path": {"type": "string"},
            "output_file": {"type": "string"},
            "file_size": {"type": "integer", "minimum": 0},
        })
    return {
        "type": "object",
        "properties": properties,
        "required": ["status"],
        # OperationResult 允许各领域附加经过测试的业务字段。
        "additionalProperties": True,
    }


@lru_cache(maxsize=1)
def atomic_handler_map() -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    """发现受控 tools 包中的全部 ``tool_*`` handler。"""
    handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
    for module_name in _TOOL_MODULES:
        module = importlib.import_module(f"cst_runtime.tools.{module_name}")
        for attribute_name in dir(module):
            if not attribute_name.startswith("tool_"):
                continue
            value = getattr(module, attribute_name)
            if callable(value):
                handlers[attribute_name] = value
    return handlers


def atomic_definitions() -> list[dict[str, Any]]:
    """返回带 handler 的原子操作定义。"""
    from .exposure import exposure_for, validate_exposure
    from ..tools import all_defs

    handlers = atomic_handler_map()
    definitions: list[dict[str, Any]] = []
    for name, definition in all_defs().items():
        handler_name = str(definition["handler"])
        try:
            handler = handlers[handler_name]
        except KeyError as exc:
            raise KeyError(
                f"操作 {name} 缺少 handler: {handler_name}"
            ) from exc
        definitions.append(
            {
                "name": name,
                "description": str(definition.get("description", name)),
                "risk": str(definition.get("risk", "read")),
                "exposure": validate_exposure(
                    str(definition.get("exposure", exposure_for(name)))
                ),
                "input_schema": definition["json_schema"],
                "output_schema": definition.get("output_schema") or _output_schema(name),
                "handler": handler,
            }
        )
    return definitions
