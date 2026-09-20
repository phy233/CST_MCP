"""阵列构建工作流。

该模块只编排 ``cst_runtime.lib`` 提供的原子能力，不直接访问 core。
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from importlib import metadata
import math
from typing import Any, Mapping, Protocol, Sequence

from ..lib import batch
from ..lib.geometry import brick, delete_entity, translate
from .array_templates import BUILTIN_TEMPLATES


class _ArrayOperationError(RuntimeError):
    """携带原子操作的结构化错误，避免工作流丢失失败阶段。"""

    def __init__(self, result: Mapping[str, Any]) -> None:
        super().__init__(result.get("message", "阵列原子操作失败"))
        self.result = dict(result)


def _raise_if_failed(result: Any) -> None:
    """兼容旧自定义 builder/mock 的 None 成功约定。"""
    if result is None:
        return
    if isinstance(result, dict) and (result.get("status") == "error" or result.get("ok") is False):
        raise _ArrayOperationError(result)


@dataclass(frozen=True)
class ArrayElement:
    """阵列中的一个实例；x/y/z 是参考模板的相对平移量。"""

    code: str
    x: float | str
    y: float | str
    z: float | str


@dataclass(frozen=True)
class UnitSpec:
    """某种阵列单元的 builder 与参数。"""

    builder_id: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BuildResult:
    """单元 builder 创建参考实体后的结果。"""

    component: str
    reference_names: list[str]
    status: str = "success"
    message: str = ""
    owns_reference: bool = True


@dataclass
class ArrayBuildResult:
    """阵列工作流的结构化结果。"""

    status: str
    project_path: str
    groups_built: int = 0
    instances_created: int = 0
    reference_objects: dict[str, list[str]] = field(default_factory=dict)
    message: str = ""
    instances_reused: int = 0
    groups_planned: int = 0
    instances_planned: int = 0
    failure: dict[str, Any] = field(default_factory=dict)
    submission: str = "accepted"
    execution: str = "reported_ok"

    def to_dict(self) -> dict[str, Any]:
        """转换为 JSON 可序列化字典。"""
        payload = asdict(self)
        if self.status != "success":
            payload.update(submission="not_submitted", execution="not_run")
            # 保留终止信号、错误类型与执行阶段，避免调用方误重试。
            for key in ("error_type", "error", "context", "submission", "execution",
                        "batch_retained", "retry_safe", "terminal", "await_user_decision"):
                if key in self.failure:
                    payload[key] = self.failure[key]
        return payload


class UnitBuilder(Protocol):
    """阵列单元 builder 协议。"""

    def __call__(
        self,
        project_path: str,
        code: str,
        parameters: Mapping[str, Any],
    ) -> BuildResult:
        """创建或复用参考单元，并声明是否拥有临时参考实体。"""


class UnitBuilderRegistry:
    """受控的阵列单元 builder 注册表。"""

    def __init__(self, *, load_entry_points: bool = True) -> None:
        self._builders: dict[str, UnitBuilder] = {}
        self.register("create-brick-template", _create_brick_template)
        self.register("copy-template", _prepare_existing_template)
        if load_entry_points:
            self._load_entry_points()

    def register(
        self,
        builder_id: str,
        builder: UnitBuilder,
        *,
        replace: bool = False,
    ) -> None:
        """注册一个 builder。"""
        normalized = builder_id.strip()
        if not normalized:
            raise ValueError("builder_id 不能为空")
        if normalized in self._builders and not replace:
            raise ValueError(f"builder 已存在: {normalized}")
        self._builders[normalized] = builder

    def resolve(self, builder_id: str) -> UnitBuilder:
        """解析 builder，不允许动态导入任意模块。"""
        try:
            return self._builders[builder_id]
        except KeyError as exc:
            available = ", ".join(sorted(self._builders))
            raise KeyError(
                f"未知 builder_id: {builder_id}；可用 builder: {available}"
            ) from exc

    def available(self) -> list[str]:
        """返回已注册 builder ID。"""
        return sorted(self._builders)

    def describe(self) -> list[dict[str, Any]]:
        """列出当前 Worker 可调用的模板及内置参数契约。"""
        return [{"builder_id": name, **BUILTIN_TEMPLATES.get(name, {
            "description": "扩展模板；参数契约由安装的扩展提供。",
            "parameters_schema": None,
        })} for name in self.available()]

    def _load_entry_points(self) -> None:
        try:
            discovered = metadata.entry_points()
            if hasattr(discovered, "select"):
                entries = discovered.select(group="cst_runtime.unit_builders")
            else:
                entries = discovered.get("cst_runtime.unit_builders", [])
            for entry in entries:
                self.register(entry.name, entry.load())
        except Exception:
            # 第三方 entry point 不应阻止内置 builder 使用。
            return


def _coordinate(value: Any) -> float | str:
    """保留 CST 参数表达式；纯数值继续执行有限数检查。"""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("坐标或尺寸必须是数值或 CST 参数表达式")
    if isinstance(value, str):
        value = value.strip()
        if not value or not value.isascii() or any(ord(char) < 32 or char == '"' for char in value):
            raise ValueError("参数表达式须为非空 ASCII，且不能包含引号或控制字符")
        try:
            number = float(value)
        except ValueError:
            return value
    else:
        number = float(value)
    if not math.isfinite(number):
        raise ValueError("坐标或尺寸必须为有限数")
    return number


def _text(value: Any, label: str, *, entity: bool = False) -> str:
    """检查调用方提供的文本，不查询 CST 状态。"""
    if (not isinstance(value, str) or not value.strip() or not value.isascii()
            or any(ord(char) < 32 or ord(char) == 127 or char == '"' for char in value)
            or (entity and ":" in value)):
        raise ValueError(f"{label} 须为非空 ASCII，不含引号、控制字符或实体分隔符")
    return value


def _validate_parameters(builder_id: str, code: str, parameters: Mapping[str, Any]) -> None:
    """在批次开始前检查内置模板输入，避免拼错参数后静默使用默认值。"""
    template = BUILTIN_TEMPLATES.get(builder_id)
    if template is None:
        return
    schema = template["parameters_schema"]
    unknown = set(parameters) - set(schema["properties"])
    missing = set(schema.get("required", [])) - set(parameters)
    if unknown or missing:
        raise ValueError(f"{builder_id} 参数错误：未知字段 {sorted(unknown)}，缺少字段 {sorted(missing)}")
    _text(parameters.get("component", "array"), "component", entity=True)
    if builder_id == "copy-template":
        names = parameters["reference_names"]
        if not isinstance(names, (list, tuple)) or not names:
            raise ValueError("reference_names 必须是非空实体名称列表")
        for name in names:
            _text(name, "reference_names", entity=True)
        if len(set(names)) != len(names):
            raise ValueError("reference_names 不得重复")
        return
    _text(parameters.get("name", f"brick_{code}"), "name", entity=True)
    _text(parameters.get("material", "PEC"), "material")
    for field_name, default in (("size", [1, 1, 1]), ("origin", [0, 0, 0])):
        values = parameters.get(field_name, default)
        if not isinstance(values, (list, tuple)) or len(values) != 3:
            raise ValueError(f"create-brick-template 的 {field_name} 必须包含三个数值或表达式")
        values = [_coordinate(value) for value in values]
        if field_name == "size" and any(isinstance(value, float) and value <= 0 for value in values):
            raise ValueError("create-brick-template 的 size 必须全部大于 0")


def _prepare_existing_template(project_path: str, code: str, parameters: Mapping[str, Any]) -> BuildResult:
    """借用既有实体；本工作流不获得删除源模板的所有权。"""
    return BuildResult(component=parameters["component"],
                       reference_names=list(parameters["reference_names"]), owns_reference=False)


def _upper_bound(origin: float | str, size: float | str) -> float | str:
    """表达式相加保留括号，不提前求值并冻结参数。"""
    if isinstance(origin, float) and isinstance(size, float):
        return origin + size
    return f"({origin})+({size})"


def _create_brick_template(
    project_path: str,
    code: str,
    parameters: Mapping[str, Any],
) -> BuildResult:
    """内置方块 builder；origin 是最小角点，size 沿三个正方向延伸。"""
    _validate_parameters("create-brick-template", code, parameters)
    component = str(parameters.get("component", "array"))
    name = str(parameters.get("name", f"brick_{code}"))
    material = str(parameters.get("material", "PEC"))
    size = parameters.get("size", [1.0, 1.0, 1.0])
    origin = parameters.get("origin", [0.0, 0.0, 0.0])
    sx, sy, sz = (_coordinate(value) for value in size)
    ox, oy, oz = (_coordinate(value) for value in origin)
    created = brick(
        project_path,
        component=component,
        name=name,
        material=material,
        x_range=(ox, _upper_bound(ox, sx)),
        y_range=(oy, _upper_bound(oy, sy)),
        z_range=(oz, _upper_bound(oz, sz)),
    )
    _raise_if_failed(created)
    return BuildResult(component=component, reference_names=[name])


DEFAULT_REGISTRY = UnitBuilderRegistry()


def _coerce_elements(elements: Sequence[ArrayElement | Mapping[str, Any]]) -> list[ArrayElement]:
    normalized: list[ArrayElement] = []
    for raw in elements:
        if isinstance(raw, ArrayElement):
            raw = asdict(raw)
        if set(raw) != {"code", "x", "y", "z"}:
            raise ValueError("每个 element 必须且只能包含 code、x、y、z")
        normalized.append(
            ArrayElement(
                code=str(raw["code"]),
                x=_coordinate(raw["x"]),
                y=_coordinate(raw["y"]),
                z=_coordinate(raw["z"]),
            )
        )
    return normalized


def _coerce_units(units: Mapping[str, UnitSpec | Mapping[str, Any]]) -> dict[str, UnitSpec]:
    normalized: dict[str, UnitSpec] = {}
    for code, raw in units.items():
        key = str(code)
        if isinstance(raw, UnitSpec):
            raw = asdict(raw)
        if set(raw) - {"builder_id", "parameters"} or "builder_id" not in raw:
            raise ValueError(f"units[{key}] 必须包含 builder_id，且只允许 parameters 附加字段")
        if not isinstance(raw.get("parameters", {}), Mapping):
            raise ValueError(f"units[{key}].parameters 必须为对象")
        normalized[key] = UnitSpec(builder_id=str(raw["builder_id"]),
                                   parameters=dict(raw.get("parameters", {})))
    return normalized


def build_array(
    project_path: str,
    units: Mapping[str, UnitSpec | Mapping[str, Any]],
    elements: Sequence[ArrayElement | Mapping[str, Any]],
    summary: str = "Build Array",
    *,
    registry: UnitBuilderRegistry | None = None,
) -> ArrayBuildResult:
    """按 code 分组构建并复制阵列单元。

    ``code`` 是不透明的 builder 查询键，字符串 ``"0"`` 没有空单元含义。
    ``elements`` 中的坐标是相对平移量，不是实体中心或绝对角点。
    """
    active_registry = registry or DEFAULT_REGISTRY
    try:
        _text(summary, "summary")
        normalized_elements = _coerce_elements(elements)
        normalized_units = _coerce_units(units)
        seen = set()
        declared_references: dict[tuple[str, str], str] = {}
        for element in normalized_elements:
            position = (element.code, element.x, element.y, element.z)
            if position in seen:
                raise ValueError(f"code {element.code} 存在重复位移；每个位置只声明一次")
            seen.add(position)
        for code in dict.fromkeys(element.code for element in normalized_elements):
            if code not in normalized_units:
                raise ValueError(f"code {code} 缺少 UnitSpec")
            spec = normalized_units[code]
            active_registry.resolve(spec.builder_id)
            _validate_parameters(spec.builder_id, code, spec.parameters)
            if spec.builder_id in BUILTIN_TEMPLATES:
                component = spec.parameters.get("component", "array")
                names = (spec.parameters.get("reference_names", []) if spec.builder_id == "copy-template"
                         else [spec.parameters.get("name", f"brick_{code}")])
                for name in names:
                    key = (component, name)
                    if key in declared_references:
                        raise ValueError(f"模板实体 {component}:{name} 被多个 code 引用或创建")
                    declared_references[key] = code
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return ArrayBuildResult(status="error", project_path=project_path, message=str(exc),
                                failure={"error_type": "invalid_arguments"})
    if not normalized_elements:
        return ArrayBuildResult(
            status="error",
            project_path=project_path,
            message="elements 不能为空",
        )

    groups: dict[str, list[ArrayElement]] = defaultdict(list)
    for element in normalized_elements:
        if element.code not in normalized_units:
            return ArrayBuildResult(
                status="error",
                project_path=project_path,
                message=f"code {element.code} 缺少 UnitSpec",
            )
        groups[element.code].append(element)

    begin_result = batch.begin(project_path, summary=summary)
    if begin_result.get("status") == "error":
        return ArrayBuildResult(
            status="error",
            project_path=project_path,
            message=begin_result.get("message", "无法开始批处理"),
            failure=dict(begin_result),
        )

    references: dict[str, list[str]] = {}
    instances_created = 0
    instances_reused = 0
    flush_started = False
    try:
        for code, group in groups.items():
            spec = normalized_units[code]
            builder = active_registry.resolve(spec.builder_id)
            built = builder(project_path, code, spec.parameters)
            if built.status != "success":
                raise RuntimeError(built.message or f"builder {spec.builder_id} 执行失败")
            if not built.component or not built.reference_names:
                raise ValueError("builder 必须返回 component 和 reference_names")
            references[code] = list(built.reference_names)

            keep_reference = False
            for element in group:
                if (
                    all(isinstance(value, (float, int)) and value == 0
                        for value in (element.x, element.y, element.z))
                ):
                    keep_reference = True
                    if built.owns_reference:
                        instances_created += 1
                    else:
                        instances_reused += 1
                    continue
                for name in built.reference_names:
                    translated = translate(
                        project_path,
                        name=f"{built.component}:{name}",
                        vector=(element.x, element.y, element.z),
                        multiple_objects=True,
                        repetitions=1,
                    )
                    _raise_if_failed(translated)
                instances_created += 1

            if built.owns_reference and not keep_reference:
                for name in built.reference_names:
                    deleted = delete_entity(
                        project_path, name=name, component=built.component
                    )
                    _raise_if_failed(deleted)

        flush_started = True
        flush_result = batch.flush(project_path)
        if flush_result.get("status") == "error":
            return ArrayBuildResult(
                status="error",
                project_path=project_path,
                groups_planned=len(groups),
                instances_planned=len(normalized_elements),
                reference_objects=references,
                failure={"submission": "not_submitted" if flush_result.get("retry_safe") else "unknown",
                         "execution": "not_run" if flush_result.get("retry_safe") else "unknown",
                         **dict(flush_result)},
                message=(
                    f"{flush_result.get('message', '批处理提交失败')}；"
                    "批次仅保留用于诊断，执行状态可能包含部分副作用，"
                    "请勿直接重试 flush；人工确认后显式 discard"
                ),
            )
        return ArrayBuildResult(
            status="success",
            project_path=project_path,
            groups_built=len(groups),
            instances_created=instances_created,
            instances_reused=instances_reused,
            reference_objects=references,
            groups_planned=len(groups),
            instances_planned=len(normalized_elements),
            submission=flush_result.get("submission", "accepted"),
            execution=flush_result.get("execution", "reported_ok"),
        )
    except Exception as exc:
        if not flush_started:
            batch.discard(project_path)
        return ArrayBuildResult(
            status="error",
            project_path=project_path,
            groups_planned=len(groups),
            instances_planned=len(normalized_elements),
            reference_objects=references,
            message=str(exc) + ("；提交状态不明，禁止直接重试" if flush_started else ""),
            failure={"execution": "unknown" if flush_started else "not_run",
                     "submission": "unknown" if flush_started else "not_submitted",
                     "batch_retained": flush_started, "retry_safe": not flush_started,
                     **getattr(exc, "result", {})},
        )
