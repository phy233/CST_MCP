"""协议无关的 cst_runtime 操作注册表。

本模块只使用普通 Python 类型和 JSON Schema，不依赖 MCP SDK。
"""
from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass
from typing import Any, Callable

from ..contracts import error_response, normalize_response, success_response
from .exposure import exposure_for


OperationHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class OperationSpec:
    """一个可被 Python、CLI 或远程适配器调用的操作。"""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: OperationHandler
    exposure: str
    tool_name: str | None = None
    risk: str = "read"
    output_schema: dict[str, Any] | None = None

    @property
    def public_name(self) -> str:
        """返回 CLI 和 MCP 使用的公开工具名。"""
        return self.tool_name or self.name

    def describe(self, *, public: bool = False) -> dict[str, Any]:
        """返回不包含 Python handler 的可序列化描述。"""
        result = {
            "name": self.public_name if public else self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "risk": self.risk,
            "exposure": self.exposure,
        }
        if public and self.public_name != self.name:
            result["operation"] = self.name
        if self.output_schema is not None:
            result["output_schema"] = self.output_schema
        return result


_OPERATIONS: dict[str, OperationSpec] | None = None


def _object_schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _array_build(args: dict[str, Any]) -> dict[str, Any]:
    from ..workflows.array import build_array

    return build_array(
        project_path=args["project_path"],
        units=args["units"],
        elements=args["elements"],
        summary=args.get("summary", "Build Array"),
    ).to_dict()


def _sweep_run(args: dict[str, Any]) -> dict[str, Any]:
    """quick-sweep：本工具自行管理会话（open → sweep → close）。"""
    from ..lib.session import close_project, open_project
    from ..workflows.sweep import quick_sweep

    project_path = args["project_path"]
    opened = open_project(project_path)
    if opened.get("status") == "error":
        return dict(opened)
    try:
        return quick_sweep(
            project_path=project_path,
            parameters=args["parameters"],
            target_freq_ghz=float(args["target_freq_ghz"]),
            result_path=args.get(
                "result_path",
                "1D Results\\S-Parameters\\S1,1",
            ),
            output_dir=args.get("output_dir"),
            continue_on_error=bool(args.get("continue_on_error", True)),
            restore_parameters=bool(args.get("restore_parameters", True)),
        ).to_dict()
    finally:
        close_project(project_path, save=False)


def _cross_process_run(args: dict[str, Any]) -> dict[str, Any]:
    """cross-process-sweep：本工具自行管理会话（open → sweep → close）。"""
    from ..lib.session import close_project, open_project
    from ..workflows.cross_process import quick_cross_sweep

    project_path = args["project_path"]
    opened = open_project(project_path)
    if opened.get("status") == "error":
        return dict(opened)
    try:
        result = quick_cross_sweep(
            project_path=project_path,
            lx_range=args["lx_range"],
            ly1_range=args["ly1_range"],
            target_freq_ghz=float(args["target_freq_ghz"]),
            output_dir=args.get("output_dir"),
            continue_on_error=bool(args.get("continue_on_error", True)),
            restore_parameters=bool(args.get("restore_parameters", True)),
        )
        return result.to_dict()
    finally:
        close_project(project_path, save=False)


def _workflow_operations() -> dict[str, OperationSpec]:
    number_array = {"type": "array", "items": {"type": "number"}, "minItems": 1}
    array_output = _object_schema(
        {
            "status": {"type": "string"},
            "project_path": {"type": "string"},
            "groups_built": {"type": "integer"},
            "instances_created": {"type": "integer"},
            "reference_objects": {"type": "object"},
            "message": {"type": "string"},
        },
        ["status", "project_path", "groups_built", "instances_created"],
    )
    sweep_output = _object_schema(
        {
            "status": {"type": "string"},
            "output_dir": {"type": "string"},
            "sweep_time": {"type": "number"},
            "total_steps": {"type": "integer"},
            "successful_steps": {"type": "integer"},
            "failed_steps": {"type": "integer"},
            "records": {"type": "array", "items": {"type": "object"}},
            "exported_files": {"type": "array", "items": {"type": "string"}},
            "errors": {"type": "array", "items": {"type": "object"}},
        },
        [
            "status",
            "output_dir",
            "total_steps",
            "successful_steps",
            "failed_steps",
            "records",
            "exported_files",
            "errors",
        ],
    )
    return {
        "array.build": OperationSpec(
            name="array.build",
            tool_name="build-array",
            description=(
                "按普通 code 和受控 builder 批量构建 CST 阵列；"
                "元素坐标是参考模板的相对平移量。brick-v1 的 origin 是最小角点，"
                "如使用中心坐标应由调用方预先换算。"
            ),
            risk="write",
            exposure=exposure_for("build-array"),
            input_schema=_object_schema(
                {
                    "project_path": {"type": "string", "minLength": 1},
                    "units": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "builder_id": {"type": "string", "minLength": 1},
                                "parameters": {
                                    "type": "object",
                                    "description": (
                                        "builder 参数；brick-v1 的 origin 为最小角点，"
                                        "size 沿 X/Y/Z 正方向延伸。"
                                    ),
                                },
                            },
                            "required": ["builder_id"],
                            "additionalProperties": False,
                        },
                    },
                    "elements": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "普通 builder 查询键；字符串 0 不表示空单元。",
                                },
                                "x": {"type": "number", "description": "X 方向相对平移量。"},
                                "y": {"type": "number", "description": "Y 方向相对平移量。"},
                                "z": {"type": "number", "description": "Z 方向相对平移量。"},
                            },
                            "required": ["code", "x", "y", "z"],
                            "additionalProperties": False,
                        },
                    },
                    "summary": {"type": "string", "default": "Build Array"},
                },
                ["project_path", "units", "elements"],
            ),
            output_schema=array_output,
            handler=_array_build,
        ),
        "sweep.run": OperationSpec(
            name="sweep.run",
            tool_name="quick-sweep",
            description="运行参数扫描并导出 JSON、CSV 和 NPZ 结果。",
            risk="long-running",
            exposure=exposure_for("quick-sweep"),
            input_schema=_object_schema(
                {
                    "project_path": {"type": "string", "minLength": 1},
                    "parameters": {
                        "type": "object",
                        "additionalProperties": number_array,
                    },
                    "target_freq_ghz": {"type": "number"},
                    "result_path": {
                        "type": "string",
                        "default": "1D Results\\S-Parameters\\S1,1",
                    },
                    "output_dir": {"type": ["string", "null"], "default": None},
                    "continue_on_error": {"type": "boolean", "default": True},
                    "restore_parameters": {"type": "boolean", "default": True},
                },
                ["project_path", "parameters", "target_freq_ghz"],
            ),
            output_schema=sweep_output,
            handler=_sweep_run,
        ),
        "cross_process.run": OperationSpec(
            name="cross_process.run",
            tool_name="cross-process-sweep",
            description="运行十字形单元的双极化参数扫描。",
            risk="long-running",
            exposure=exposure_for("cross-process-sweep"),
            input_schema=_object_schema(
                {
                    "project_path": {"type": "string", "minLength": 1},
                    "lx_range": number_array,
                    "ly1_range": number_array,
                    "target_freq_ghz": {"type": "number"},
                    "output_dir": {"type": ["string", "null"], "default": None},
                    "continue_on_error": {"type": "boolean", "default": True},
                    "restore_parameters": {"type": "boolean", "default": True},
                },
                ["project_path", "lx_range", "ly1_range", "target_freq_ghz"],
            ),
            output_schema=sweep_output,
            handler=_cross_process_run,
        ),
    }


def _atomic_operations() -> dict[str, OperationSpec]:
    """把已有 runtime 原子工具纳入统一注册表。

    这些 handler 仍属于 cst_runtime 包，MCP 层不会导入或复制它们。
    """
    from .atomic import atomic_definitions

    result: dict[str, OperationSpec] = {}
    for definition in atomic_definitions():
        name = definition["name"]
        handler = definition["handler"]

        def call(
            args: dict[str, Any],
            *,
            _handler: Callable[[dict[str, Any]], dict[str, Any]] = handler,
        ) -> dict[str, Any]:
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                value = _handler(args)
            if not isinstance(value, dict):
                value = success_response(result=value)
            else:
                # IPC 边界只暴露普通 JSON 字典，不泄漏 Python 专用结果类型。
                value = dict(value)
            output = captured.getvalue().strip()
            if output:
                value.setdefault("stdout", output)
            return value

        result[name] = OperationSpec(
            name=name,
            description=definition["description"],
            risk=definition["risk"],
            exposure=definition["exposure"],
            input_schema=definition["input_schema"],
            output_schema=definition.get("output_schema"),
            handler=call,
        )
    return result


def operations() -> dict[str, OperationSpec]:
    """返回完整操作注册表。"""
    global _OPERATIONS
    if _OPERATIONS is None:
        merged = _atomic_operations()
        merged.update(_workflow_operations())
        _OPERATIONS = merged
    return dict(_OPERATIONS)


def describe_operations() -> list[dict[str, Any]]:
    """返回按稳定操作名排序的操作描述。"""
    return [operations()[name].describe() for name in sorted(operations())]


def tools() -> dict[str, OperationSpec]:
    """返回以 CLI/MCP 公开名为键的工具视图。"""
    return {spec.public_name: spec for spec in operations().values()}


def describe_tools() -> list[dict[str, Any]]:
    """返回按公开名排序的 CLI/MCP 工具描述。"""
    public_tools = tools()
    return [
        public_tools[name].describe(public=True)
        for name in sorted(public_tools)
    ]


def invoke(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """按稳定操作名调用白名单中的一个操作。"""
    spec = operations().get(name)
    if spec is None:
        return error_response(
            "unknown_operation",
            f"未知操作: {name}",
            phase="validation",
            available_operations=sorted(operations()),
        )
    supplied = dict(arguments or {})
    if spec.input_schema.get("additionalProperties") is False:
        allowed = set(spec.input_schema.get("properties", {}))
        unknown = sorted(set(supplied) - allowed)
        if unknown:
            return error_response(
                "invalid_arguments",
                f"包含 Schema 未声明的参数: {', '.join(unknown)}",
                phase="validation",
                unknown_arguments=unknown,
            )
    try:
        result = spec.handler(supplied)
        if not isinstance(result, dict):
            return success_response(result=result)
        return normalize_response(result)
    except ValueError as exc:
        return error_response("invalid_arguments", str(exc), phase="validation")
    except Exception as exc:
        return error_response("runtime_error", str(exc), phase="runtime")


def invoke_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """按 CLI/MCP 公开名调用统一 API handler。"""
    spec = tools().get(name)
    if spec is None:
        return error_response(
            "unknown_tool",
            f"未知工具: {name}",
            phase="validation",
            available_tools=sorted(tools()),
        )
    return invoke(spec.name, arguments)
