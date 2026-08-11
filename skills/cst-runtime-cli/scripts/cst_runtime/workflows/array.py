"""阵列构建工作流。

该模块只编排 ``cst_runtime.lib`` 提供的原子能力，不直接访问 core。
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from importlib import metadata
from typing import Any, Callable, Mapping, Protocol, Sequence

from ..lib import batch
from ..lib.geometry import brick, delete_entity, translate


def _raise_if_failed(result: Any) -> None:
    """兼容旧自定义 builder/mock 的 None 成功约定。"""
    if result is None:
        return
    if isinstance(result, dict) and result.get("status") == "error":
        raise RuntimeError(result.get("message", "阵列原子操作失败"))


@dataclass(frozen=True)
class ArrayElement:
    """阵列中的一个实例；x/y/z 是参考模板的相对平移量。"""

    code: str
    x: float
    y: float
    z: float


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


@dataclass
class ArrayBuildResult:
    """阵列工作流的结构化结果。"""

    status: str
    project_path: str
    groups_built: int = 0
    instances_created: int = 0
    reference_objects: dict[str, list[str]] = field(default_factory=dict)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为 JSON 可序列化字典。"""
        return asdict(self)


class UnitBuilder(Protocol):
    """阵列单元 builder 协议。"""

    def __call__(
        self,
        project_path: str,
        code: str,
        parameters: Mapping[str, Any],
    ) -> BuildResult:
        """在原点创建一个参考单元。"""


class UnitBuilderRegistry:
    """受控的阵列单元 builder 注册表。"""

    def __init__(self, *, load_entry_points: bool = True) -> None:
        self._builders: dict[str, UnitBuilder] = {}
        self.register("brick-v1", _build_brick)
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


def _build_brick(
    project_path: str,
    code: str,
    parameters: Mapping[str, Any],
) -> BuildResult:
    """内置方块 builder；origin 是最小角点，size 沿三个正方向延伸。"""
    component = str(parameters.get("component", "array"))
    name = str(parameters.get("name", f"brick_{code}"))
    material = str(parameters.get("material", "PEC"))
    size = parameters.get("size", [1.0, 1.0, 1.0])
    origin = parameters.get("origin", [0.0, 0.0, 0.0])
    if not isinstance(size, (list, tuple)) or len(size) != 3:
        raise ValueError("brick-v1 的 size 必须包含三个数值")
    if not isinstance(origin, (list, tuple)) or len(origin) != 3:
        raise ValueError("brick-v1 的 origin 必须包含三个数值")
    sx, sy, sz = (float(value) for value in size)
    ox, oy, oz = (float(value) for value in origin)
    if sx <= 0 or sy <= 0 or sz <= 0:
        raise ValueError("brick-v1 的 size 必须全部大于 0")
    created = brick(
        project_path,
        component=component,
        name=name,
        material=material,
        x_range=(ox, ox + sx),
        y_range=(oy, oy + sy),
        z_range=(oz, oz + sz),
    )
    if isinstance(created, dict) and created.get("status") == "error":
        return BuildResult(
            component=component,
            reference_names=[],
            status="error",
            message=created.get("message", "创建参考单元失败"),
        )
    return BuildResult(component=component, reference_names=[name])


DEFAULT_REGISTRY = UnitBuilderRegistry()


def _coerce_elements(elements: Sequence[ArrayElement | Mapping[str, Any]]) -> list[ArrayElement]:
    normalized: list[ArrayElement] = []
    for raw in elements:
        if isinstance(raw, ArrayElement):
            normalized.append(raw)
            continue
        normalized.append(
            ArrayElement(
                code=str(raw["code"]),
                x=float(raw["x"]),
                y=float(raw["y"]),
                z=float(raw["z"]),
            )
        )
    return normalized


def _coerce_units(units: Mapping[str, UnitSpec | Mapping[str, Any]]) -> dict[str, UnitSpec]:
    normalized: dict[str, UnitSpec] = {}
    for code, raw in units.items():
        key = str(code)
        if isinstance(raw, UnitSpec):
            normalized[key] = raw
        else:
            normalized[key] = UnitSpec(
                builder_id=str(raw["builder_id"]),
                parameters=dict(raw.get("parameters", {})),
            )
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
    normalized_elements = _coerce_elements(elements)
    normalized_units = _coerce_units(units)
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

    active_registry = registry or DEFAULT_REGISTRY
    begin_result = batch.begin(project_path, summary=summary)
    if begin_result.get("status") == "error":
        return ArrayBuildResult(
            status="error",
            project_path=project_path,
            message=begin_result.get("message", "无法开始批处理"),
        )

    references: dict[str, list[str]] = {}
    instances_created = 0
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
                    abs(element.x) < 1e-9
                    and abs(element.y) < 1e-9
                    and abs(element.z) < 1e-9
                ):
                    keep_reference = True
                    instances_created += 1
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

            if not keep_reference:
                for name in built.reference_names:
                    deleted = delete_entity(
                        project_path, name=name, component=built.component
                    )
                    _raise_if_failed(deleted)

        flush_result = batch.flush(project_path)
        if flush_result.get("status") == "error":
            return ArrayBuildResult(
                status="error",
                project_path=project_path,
                groups_built=len(references),
                instances_created=instances_created,
                reference_objects=references,
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
            reference_objects=references,
        )
    except Exception as exc:
        batch.discard(project_path)
        return ArrayBuildResult(
            status="error",
            project_path=project_path,
            groups_built=len(references),
            instances_created=instances_created,
            reference_objects=references,
            message=str(exc),
        )
