"""CST 阵列建模工作流。

该模块提供了高级的阵列建模工作流。它不负责具体的几何建模，而是通过控制反转 (IoC)
将具体的单元建模委托给用户提供的 ModelBuilder 回调函数。本模块只负责批处理生命周期、
循环复制、平移和错误恢复。

用法：
    from cst_runtime.lib.array import build_array, ModelBuilder
    
    def my_unit_builder(project_path: str) -> dict:
        # ... 构建几何 ...
        return {"status": "success", "component": "array_comp", "solids": ["brick1"]}
        
    build_array("project.cst", my_unit_builder, [(0,0,0), (10,0,0)])
"""
from __future__ import annotations

from typing import Any, Callable, Sequence
from dataclasses import dataclass, field
from collections import defaultdict

from ..core.modeling import begin_batch as _begin_batch
from ..core.modeling import flush_batch as _flush_batch
from ..core.modeling import discard_batch as _discard_batch
from .geometry import translate as _translate
from .geometry import delete_entity as _delete_entity


@dataclass
class ArrayElement:
    """定义阵列中的一个独立单元元素。"""
    x: float
    y: float
    z: float
    code: Any = None
    # 预留给未来的扩展属性，例如 rotation, material 等
    # 只要它们在字典/类里，用户和 builder 之间可以相互传递


@dataclass
class BuildResult:
    """定义 ModelBuilder 回调函数的返回结果。"""
    component: str
    reference_names: list[str]
    status: str = "success"
    message: str = ""


# ModelBuilder 接收项目路径和一个参考 ArrayElement，返回构建结果。
ModelBuilder = Callable[[str, ArrayElement], BuildResult]


def build_array(
    project_path: str,
    unit_builder: ModelBuilder,
    elements: Sequence[ArrayElement],
    summary: str = "Build Array",
) -> dict[str, Any]:
    """通过回调函数构建复杂阵列。
    
    该函数会自动开启并管理 Command Buffer 的生命周期。它将根据 `elements` 中
    不同的 `code` 进行分组，按组调用 `unit_builder` 构建参考单元，然后将参考单元
    复制并平移到相应的坐标，最后删除该组的参考单元。

    Args:
        project_path: .cst 文件的绝对路径。
        unit_builder: 负责构建单种形态样板的回调函数。
        elements: ArrayElement 数据类的列表。
        summary: 批处理任务的摘要名称，将在 CST History Tree 中显示。

    Returns:
        包含 "status" 和其他执行信息的字典。如果失败，"status" 为 "error"。
    """
    if not elements:
        return {"status": "error", "message": "elements 列表不能为空"}

    # 按 code 分组 (具有相同 code 的元素共用同一个参考样板)
    code_groups: dict[Any, list[ArrayElement]] = defaultdict(list)
    for el in elements:
        code_groups[el.code].append(el)

    # 1. 开启 Batch
    res = _begin_batch(project_path, summary=summary)
    if res.get("status") == "error":
        return res

    try:
        # 对每一种 code 独立构建并复制
        for code, group_elements in code_groups.items():
            # 2. 调用 ModelBuilder 构建当前 code 的参考单元
            # 传递该组的第一个元素作为代表（包含可能存在的拓展属性）
            representative = group_elements[0]
            builder_res = unit_builder(project_path, representative)
            
            if builder_res.status != "success":
                _discard_batch(project_path)
                return {"status": "error", "message": builder_res.message}
            
            component = builder_res.component
            solids = builder_res.reference_names
            
            if not component or not solids:
                _discard_batch(project_path)
                return {"status": "error", "message": "unit_builder 返回的 component 或 reference_names 为空"}

            # 3. 遍历属于该 code 的所有元素坐标，执行复制和平移
            keep_reference = False
            for el in group_elements:
                x, y, z = el.x, el.y, el.z
                if abs(x) < 1e-9 and abs(y) < 1e-9 and abs(z) < 1e-9:
                    keep_reference = True
                    continue

                for solid in solids:
                    solid_full_name = f"{component}:{solid}"
                    _translate(
                        project_path,
                        name=solid_full_name,
                        vector=(x, y, z),
                        multiple_objects=True,
                        repetitions=1,
                        destination=component,
                    )
            
            # 4. 当前组循环结束后，按需删除原点处的参考模型
            if not keep_reference:
                for solid in solids:
                    _delete_entity(project_path, name=solid, component=component)
                
        # 5. 所有组都处理完毕，提交 Batch
        return _flush_batch(project_path)

    except Exception as e:
        _discard_batch(project_path)
        return {"status": "error", "message": f"Array building failed: {str(e)}"}

