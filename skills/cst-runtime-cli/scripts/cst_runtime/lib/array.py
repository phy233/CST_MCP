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

from ..core.modeling import begin_batch as _begin_batch
from ..core.modeling import flush_batch as _flush_batch
from ..core.modeling import discard_batch as _discard_batch
from .geometry import translate as _translate
from .geometry import delete_entity as _delete_entity


# 定义 ModelBuilder 的类型提示。
# 它接收 project_path，并返回一个包含 "status", "component", 和 "solids" 的字典。
ModelBuilder = Callable[[str], dict[str, Any]]


def build_array(
    project_path: str,
    unit_builder: ModelBuilder,
    coordinates: Sequence[tuple[float, float, float]],
    summary: str = "Build Array",
) -> dict[str, Any]:
    """通过回调函数构建阵列。
    
    该函数会自动开启并管理 Command Buffer 的生命周期。它首先调用 `unit_builder`
    构建一个参考单元，然后根据 `coordinates` 列表将参考单元复制并平移到指定位置，
    最后删除原点处的参考单元。

    Args:
        project_path: .cst 文件的绝对路径。
        unit_builder: 负责构建单个单元的回调函数。
        coordinates: (x, y, z) 坐标元组的列表。
        summary: 批处理任务的摘要名称，将在 CST History Tree 中显示。

    Returns:
        包含 "status" 和其他执行信息的字典。如果失败，"status" 为 "error"。
    """
    if not coordinates:
        return {"status": "error", "message": "coordinates 列表不能为空"}

    # 1. 开启 Batch
    res = _begin_batch(project_path, summary=summary)
    if res.get("status") == "error":
        return res

    try:
        # 2. 调用 ModelBuilder 构建参考单元
        builder_res = unit_builder(project_path)
        if builder_res.get("status") == "error":
            # 构建失败，提前抛弃缓冲区
            _discard_batch(project_path)
            return builder_res
        
        component = builder_res.get("component")
        solids = builder_res.get("solids", [])
        if not component or not solids:
            _discard_batch(project_path)
            return {"status": "error", "message": "unit_builder 必须返回 'component' 和 'solids'"}

        # 3. 遍历坐标，执行复制和平移
        keep_reference = False
        for idx, (x, y, z) in enumerate(coordinates):
            if abs(x) < 1e-9 and abs(y) < 1e-9 and abs(z) < 1e-9:
                # CST 的 Transform.Translate 向量如果为 (0,0,0) 会抛出运行时异常，
                # 导致整个 Batch 被 CST 回滚。因此，直接保留参考单元代替复制。
                keep_reference = True
                continue

            for solid in solids:
                solid_full_name = f"{component}:{solid}"
                # 将实体复制并平移到目标位置
                # multiple_objects=True 表示在平移时保留原物体并创建副本
                _translate(
                    project_path,
                    name=solid_full_name,
                    vector=(x, y, z),
                    multiple_objects=True,
                    repetitions=1,
                    destination=component,
                )
        
        # 4. 循环结束后，按需删除原点处的参考模型
        if not keep_reference:
            for solid in solids:
                _delete_entity(project_path, name=solid, component=component)
            
        # 5. 提交 Batch
        return _flush_batch(project_path)

    except Exception as e:
        # 如果中间出现任何 Python 异常（例如类型错误），安全地清理缓冲区并返回错误
        _discard_batch(project_path)
        return {"status": "error", "message": f"Array building failed: {str(e)}"}
