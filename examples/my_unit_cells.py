"""自定义阵列单元 builder 示例。"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from cst_runtime.lib.geometry import brick
from cst_runtime.workflows.array import (
    ArrayElement,
    BuildResult,
    UnitBuilderRegistry,
    UnitSpec,
    build_array,
)


def build_cross(
    project_path: str,
    code: str,
    parameters: Mapping[str, Any],
) -> BuildResult:
    """创建一个简化的十字单元参考体。"""
    component = str(parameters.get("component", "metasurface"))
    length = float(parameters.get("length", 5.0))
    width = float(parameters.get("width", 1.0))
    name = f"cross_{code}"
    brick(
        project_path,
        component=component,
        name=name,
        material=str(parameters.get("material", "PEC")),
        x_range=(-length, length),
        y_range=(-width, width),
        z_range=(0.0, 0.5),
    )
    return BuildResult(component=component, reference_names=[name])


def build_demo(project_path: str):
    """使用自定义 registry 构建两单元阵列。"""
    registry = UnitBuilderRegistry(load_entry_points=False)
    registry.register("cross-v1", build_cross)
    return build_array(
        project_path,
        units={
            "a": UnitSpec(
                builder_id="cross-v1",
                parameters={"length": 5.0, "width": 1.0},
            )
        },
        elements=[
            ArrayElement(code="a", x=0.0, y=0.0, z=0.0),
            ArrayElement(code="a", x=15.0, y=0.0, z=0.0),
        ],
        registry=registry,
    )
