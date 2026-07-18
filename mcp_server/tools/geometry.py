"""MCP Tool definitions: CST Geometry operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def brick(project_path: str, component: str, name: str, material: str, x_range: tuple[float, float], y_range: tuple[float, float], z_range: tuple[float, float]) -> dict[str, Any]:
    """
    创建一个长方体。

    Args:
        project_path: .cst 文件的绝对路径
        component: 文件夹（Component）名称
        name: 长方体实体的名称
        material: 材料名称
        x_range: (最小值, 最大值) X 轴坐标范围
        y_range: (最小值, 最大值) Y 轴坐标范围
        z_range: (最小值, 最大值) Z 轴坐标范围

    Raises:
        RuntimeError: 如果无法创建长方体时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "brick", project_path=project_path, component=component, name=name, material=material, x_range=x_range, y_range=y_range, z_range=z_range)

def cylinder(project_path: str, component: str, name: str, material: str, axis: str, center: tuple[float, float], radius: float, z_range: tuple[float, float], inner_radius: float = 0.0) -> dict[str, Any]:
    """
    创建一个圆柱体（或圆管）。

    Args:
        project_path: .cst 文件的绝对路径
        component: 文件夹（Component）名称
        name: 实体名称
        material: 材料名称
        axis: 轴向 ("x", "y", 或 "z")
        center: (x, y) 截面圆心坐标
        radius: 外圆半径
        z_range: (最小值, 最大值) 沿着轴向的范围
        inner_radius: 内圆半径（默认为0，即实心圆柱）

    Raises:
        RuntimeError: 如果无法创建圆柱体时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "cylinder", project_path=project_path, component=component, name=name, material=material, axis=axis, center=center, radius=radius, z_range=z_range, inner_radius=inner_radius)

def cone(project_path: str, component: str, name: str, material: str, axis: str, center: tuple[float, float], bottom_radius: float, top_radius: float, z_range: tuple[float, float]) -> dict[str, Any]:
    """
    创建一个圆锥体。

    Args:
        project_path: .cst 文件的绝对路径
        component: 文件夹（Component）名称
        name: 实体名称
        material: 材料名称
        axis: 轴向 ("x", "y", 或 "z")
        center: (x, y) 截面圆心坐标
        bottom_radius: 底部半径
        top_radius: 顶部半径
        z_range: (最小值, 最大值) 沿着轴向的范围

    Raises:
        RuntimeError: 如果无法创建圆锥体时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "cone", project_path=project_path, component=component, name=name, material=material, axis=axis, center=center, bottom_radius=bottom_radius, top_radius=top_radius, z_range=z_range)

def rectangle(project_path: str, curve: str, name: str, x_range: tuple[float, float], y_range: tuple[float, float]) -> dict[str, Any]:
    """
    创建一个矩形曲线（2D）。

    Args:
        project_path: .cst 文件的绝对路径
        curve: 曲线文件夹名称
        name: 矩形曲线名称
        x_range: (最小值, 最大值) X 轴坐标范围
        y_range: (最小值, 最大值) Y 轴坐标范围

    Raises:
        RuntimeError: 如果无法创建矩形曲线时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "rectangle", project_path=project_path, curve=curve, name=name, x_range=x_range, y_range=y_range)

def boolean_add(project_path: str, shape1: str, shape2: str) -> dict[str, Any]:
    """
    对两个实体进行布尔加运算（合并）。

    Args:
        project_path: .cst 文件的绝对路径
        shape1: 第一个形状名称 (格式: component:name)
        shape2: 第二个形状名称 (格式: component:name)

    Raises:
        RuntimeError: 如果布尔运算失败时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "boolean_add", project_path=project_path, shape1=shape1, shape2=shape2)

def boolean_subtract(project_path: str, target: str, tool: str) -> dict[str, Any]:
    """
    进行布尔减运算。

    Args:
        project_path: .cst 文件的绝对路径
        target: 目标被减形状 (格式: component:name)
        tool: 用来减去的工具形状 (格式: component:name)

    Raises:
        RuntimeError: 如果布尔运算失败时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "boolean_subtract", project_path=project_path, target=target, tool=tool)

def boolean_intersect(project_path: str, shape1: str, shape2: str) -> dict[str, Any]:
    """
    对两个实体进行布尔交运算。

    Args:
        project_path: .cst 文件的绝对路径
        shape1: 第一个形状名称 (格式: component:name)
        shape2: 第二个形状名称 (格式: component:name)

    Raises:
        RuntimeError: 如果布尔运算失败时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "boolean_intersect", project_path=project_path, shape1=shape1, shape2=shape2)

def delete_entity(project_path: str, name: str, component: str = '') -> dict[str, Any]:
    """
    删除一个实体。

    Args:
        project_path: .cst 文件的绝对路径
        name: 实体名称
        component: (可选) 文件夹名称，如果你直接在name里写成了"component:name"可以留空

    Raises:
        RuntimeError: 如果无法删除实体时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "delete_entity", project_path=project_path, name=name, component=component)

def delete_component(project_path: str, component: str) -> dict[str, Any]:
    """
    删除整个 Component 文件夹及其内部的所有实体。

    Args:
        project_path: .cst 文件的绝对路径
        component: 文件夹名称

    Raises:
        RuntimeError: 如果无法删除文件夹时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "delete_component", project_path=project_path, component=component)

def rotate(project_path: str, name: str, center: tuple[float, float, float] = (0, 0, 0), angle: tuple[float, float, float] = (0, 0, 0), multiple_objects: bool = True, repetitions: int = 1) -> dict[str, Any]:
    """
    旋转实体。

    Args:
        project_path: .cst 文件的绝对路径
        name: 实体名称
        center: (x, y, z) 旋转中心点
        angle: (x, y, z) 绕各轴的旋转角度（度）
        multiple_objects: 是否复制对象（保留原对象）
        repetitions: 复制的数量

    Raises:
        RuntimeError: 如果旋转失败时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "rotate", project_path=project_path, name=name, center=center, angle=angle, multiple_objects=multiple_objects, repetitions=repetitions)

def mirror(project_path: str, name: str, plane_normal: tuple[float, float, float] = (0, 1, 0), center: tuple[float, float, float] = (0, 0, 0)) -> dict[str, Any]:
    """
    镜像实体。

    Args:
        project_path: .cst 文件的绝对路径
        name: 实体名称
        plane_normal: (x, y, z) 镜像面的法向量
        center: (x, y, z) 镜像中心点

    Raises:
        RuntimeError: 如果镜像失败时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "mirror", project_path=project_path, name=name, plane_normal=plane_normal, center=center)

def translate(project_path: str, name: str, vector: tuple[float, float, float], multiple_objects: bool = True, repetitions: int = 1, destination: str = '') -> dict[str, Any]:
    """
    平移（移动）实体。

    Args:
        project_path: .cst 文件的绝对路径
        name: 实体名称
        vector: (x, y, z) 平移向量
        multiple_objects: 是否复制对象（保留原对象）
        repetitions: 复制的数量
        destination: 复制目标的新文件夹名称

    Raises:
        RuntimeError: 如果平移失败时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "translate", project_path=project_path, name=name, vector=vector, multiple_objects=multiple_objects, repetitions=repetitions, destination=destination)

def activate_wcs(project_path: str, name: str, origin: tuple[float, float, float], normal: tuple[float, float, float] = (0, 0, 1), uvector: tuple[float, float, float] = (1, 0, 0)) -> dict[str, Any]:
    """
    激活局部工作坐标系 (WCS)。

    Args:
        project_path: .cst 文件的绝对路径
        name: WCS 的名称
        origin: (x, y, z) WCS 原点坐标
        normal: (x, y, z) WCS 法线方向 (默认Z轴)
        uvector: (x, y, z) WCS U轴方向 (默认X轴)

    Raises:
        RuntimeError: 如果无法激活 WCS 时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "activate_wcs", project_path=project_path, name=name, origin=origin, normal=normal, uvector=uvector)

def deactivate_wcs(project_path: str) -> dict[str, Any]:
    """
    切回全局坐标系 (Global WCS)。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法停用 WCS 时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "deactivate_wcs", project_path=project_path)

def arc(project_path: str, name: str, center: tuple[float, float, float], radius: float, start_angle: float, end_angle: float, segments: int = 0, component: str = 'component1') -> dict[str, Any]:
    """
    创建一个圆弧曲线。

    Args:
        project_path: .cst 文件的绝对路径
        name: 曲线名称
        center: (x, y, z) 圆弧中心点坐标
        radius: 圆弧半径
        start_angle: 起始角度（度）
        end_angle: 结束角度（度）
        segments: 分段数 (0表示自动)
        component: 曲线所在的文件夹名称

    Raises:
        RuntimeError: 如果无法创建圆弧时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "arc", project_path=project_path, name=name, center=center, radius=radius, start_angle=start_angle, end_angle=end_angle, segments=segments, component=component)

def polygon(project_path: str, name: str, component: str, material: str, vertices: list[tuple[float, float]], z_range: tuple[float, float]) -> dict[str, Any]:
    """
    根据顶点坐标创建一个多边形拉伸实体。

    Args:
        project_path: .cst 文件的绝对路径
        name: 实体名称
        component: 文件夹（Component）名称
        material: 材料名称
        vertices: [(x1, y1), (x2, y2), ...] 顶点坐标的列表
        z_range: (最小值, 最大值) 拉伸的 Z 轴范围

    Raises:
        RuntimeError: 如果无法创建多边形时抛出

    Returns:
        dict[str, Any]: The execution result from CST.
    """
    return call_cst("lib.geometry", "polygon", project_path=project_path, name=name, component=component, material=material, vertices=vertices, z_range=z_range)

GEOMETRY_TOOLS = [
    {"name": "brick", "handler": brick},
    {"name": "cylinder", "handler": cylinder},
    {"name": "cone", "handler": cone},
    {"name": "rectangle", "handler": rectangle},
    {"name": "boolean-add", "handler": boolean_add},
    {"name": "boolean-subtract", "handler": boolean_subtract},
    {"name": "boolean-intersect", "handler": boolean_intersect},
    {"name": "delete-entity", "handler": delete_entity},
    {"name": "delete-component", "handler": delete_component},
    {"name": "rotate", "handler": rotate},
    {"name": "mirror", "handler": mirror},
    {"name": "translate", "handler": translate},
    {"name": "activate-wcs", "handler": activate_wcs},
    {"name": "deactivate-wcs", "handler": deactivate_wcs},
    {"name": "arc", "handler": arc},
    {"name": "polygon", "handler": polygon},
]
