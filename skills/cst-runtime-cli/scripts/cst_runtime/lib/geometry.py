"""CST 几何建模操作。

用法：
    from cst_runtime.lib.geometry import brick, cylinder, boolean_subtract

    # 创建一个长方体
    brick("C:\\path\\to\\model.cst",
          component="component1",
          name="patch",
          material="PEC",
          x_range=(-5, 5), y_range=(-5, 5), z_range=(0, 0.1))

    # 创建一个圆柱体
    cylinder("C:\\path\\to\\model.cst",
             component="component1",
             name="via",
             material="Copper",
             axis="z",
             center=(0, 0),
             radius=0.5,
             z_range=(0, 1))

    # 布尔减运算
    boolean_subtract("C:\\path\\to\\model.cst",
                     target="component1:outer",
                     tool="component1:inner")
"""
from __future__ import annotations

from typing import Any, Sequence

from ..core.modeling import define_brick as _define_brick
from ..core.modeling import define_cylinder as _define_cylinder
from ..core.modeling import define_cone as _define_cone
from ..core.modeling import define_rectangle as _define_rectangle
from ..core.modeling import boolean_subtract as _boolean_subtract
from ..core.modeling import boolean_add as _boolean_add
from ..core.modeling import boolean_intersect as _boolean_intersect
from ..core.modeling import boolean_insert as _boolean_insert
from ..core.modeling import delete_entity as _delete_entity
from ..core.modeling import create_component as _create_component
from ..core.modeling import change_material as _change_material
from ..core.modeling import transform_shape as _transform_shape
from ..core.modeling import add_to_history as _add_to_history


def brick(
    project_path: str,
    component: str,
    name: str,
    material: str,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    z_range: tuple[float, float],
) -> None:
    """创建一个长方体。

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
    """
    result = _define_brick(
        project_path, name, component, material,
        x_range[0], x_range[1], y_range[0], y_range[1], z_range[0], z_range[1]
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create brick"))


def cylinder(
    project_path: str,
    component: str,
    name: str,
    material: str,
    axis: str,
    center: tuple[float, float],
    radius: float,
    z_range: tuple[float, float],
    inner_radius: float = 0.0,
) -> None:
    """创建一个圆柱体（或圆管）。

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
    """
    result = _define_cylinder(
        project_path, name, component, material,
        radius, inner_radius, axis,
        z_range[0], z_range[1], center[0], center[1]
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create cylinder"))


def cone(
    project_path: str,
    component: str,
    name: str,
    material: str,
    axis: str,
    center: tuple[float, float],
    bottom_radius: float,
    top_radius: float,
    z_range: tuple[float, float],
) -> None:
    """创建一个圆锥体。

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
    """
    result = _define_cone(
        project_path, name, component, material,
        bottom_radius, top_radius, axis,
        z_range[0], z_range[1], center[0], center[1]
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create cone"))


def rectangle(
    project_path: str,
    curve: str,
    name: str,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
) -> None:
    """创建一个矩形曲线（2D）。

    Args:
        project_path: .cst 文件的绝对路径
        curve: 曲线文件夹名称
        name: 矩形曲线名称
        x_range: (最小值, 最大值) X 轴坐标范围
        y_range: (最小值, 最大值) Y 轴坐标范围

    Raises:
        RuntimeError: 如果无法创建矩形曲线时抛出
    """
    result = _define_rectangle(
        project_path, name, curve,
        x_range[0], x_range[1], y_range[0], y_range[1]
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create rectangle"))


def boolean_add(project_path: str, shape1: str, shape2: str) -> None:
    """对两个实体进行布尔加运算（合并）。

    Args:
        project_path: .cst 文件的绝对路径
        shape1: 第一个形状名称 (格式: component:name)
        shape2: 第二个形状名称 (格式: component:name)

    Raises:
        RuntimeError: 如果布尔运算失败时抛出
    """
    result = _boolean_add(project_path, shape1, shape2)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to boolean add"))


def boolean_subtract(project_path: str, target: str, tool: str) -> None:
    """进行布尔减运算。

    Args:
        project_path: .cst 文件的绝对路径
        target: 目标被减形状 (格式: component:name)
        tool: 用来减去的工具形状 (格式: component:name)

    Raises:
        RuntimeError: 如果布尔运算失败时抛出
    """
    result = _boolean_subtract(project_path, target, tool)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to boolean subtract"))


def boolean_intersect(project_path: str, shape1: str, shape2: str) -> None:
    """对两个实体进行布尔交运算。

    Args:
        project_path: .cst 文件的绝对路径
        shape1: 第一个形状名称 (格式: component:name)
        shape2: 第二个形状名称 (格式: component:name)

    Raises:
        RuntimeError: 如果布尔运算失败时抛出
    """
    result = _boolean_intersect(project_path, shape1, shape2)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to boolean intersect"))


def delete_entity(project_path: str, name: str, component: str = "") -> None:
    """删除一个实体。

    Args:
        project_path: .cst 文件的绝对路径
        name: 实体名称
        component: (可选) 文件夹名称，如果你直接在name里写成了"component:name"可以留空

    Raises:
        RuntimeError: 如果无法删除实体时抛出
    """
    if component:
        full_name = f"{component}:{name}"
    else:
        full_name = name
    result = _delete_entity(project_path, component or "", name)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to delete entity"))


def delete_component(project_path: str, component: str) -> None:
    """删除整个 Component 文件夹及其内部的所有实体。

    Args:
        project_path: .cst 文件的绝对路径
        component: 文件夹名称

    Raises:
        RuntimeError: 如果无法删除文件夹时抛出
    """
    vba = f'Component.Delete "{component}"'
    result = _add_to_history(project_path, vba, f"Delete component: {component}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to delete component"))


def rotate(
    project_path: str,
    name: str,
    center: tuple[float, float, float] = (0, 0, 0),
    angle: tuple[float, float, float] = (0, 0, 0),
    multiple_objects: bool = True,
    repetitions: int = 1,
) -> None:
    """旋转实体。

    Args:
        project_path: .cst 文件的绝对路径
        name: 实体名称
        center: (x, y, z) 旋转中心点
        angle: (x, y, z) 绕各轴的旋转角度（度）
        multiple_objects: 是否复制对象（保留原对象）
        repetitions: 复制的数量

    Raises:
        RuntimeError: 如果旋转失败时抛出
    """
    result = _transform_shape(
        project_path, name, "rotate",
        center_x=str(center[0]), center_y=str(center[1]), center_z=str(center[2]),
        angle_x=str(angle[0]), angle_y=str(angle[1]), angle_z=str(angle[2]),
        multiple_objects=multiple_objects, repetitions=repetitions
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to rotate"))


def translate(
    project_path: str,
    name: str,
    vector: tuple[float, float, float],
    multiple_objects: bool = True,
    repetitions: int = 1,
    destination: str = "",
) -> None:
    """平移（移动）实体。

    Args:
        project_path: .cst 文件的绝对路径
        name: 实体名称
        vector: (x, y, z) 平移向量
        multiple_objects: 是否复制对象（保留原对象）
        repetitions: 复制的数量
        destination: 复制目标的新文件夹名称

    Raises:
        RuntimeError: 如果平移失败时抛出
    """
    # NOTE: CST 2026 feature - transform_shape needs to be extended to support "translate"
    # Currently this is a placeholder that constructs VBA directly
    vba = [
        "With Transform",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Vector "{vector[0]}", "{vector[1]}", "{vector[2]}"',
        f'    .MultipleObjects "{"True" if multiple_objects else "False"}"',
        f'    .Repetitions "{repetitions}"',
        f'    .Destination "{destination}"',
        '    .Transform "Shape", "Translate"',
        "End With",
    ]
    result = _add_to_history(project_path, "\n".join(vba), f"Translate: {name}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to translate"))


def mirror(
    project_path: str,
    name: str,
    plane_normal: tuple[float, float, float] = (0, 1, 0),
    center: tuple[float, float, float] = (0, 0, 0),
) -> None:
    """镜像实体。

    Args:
        project_path: .cst 文件的绝对路径
        name: 实体名称
        plane_normal: (x, y, z) 镜像面的法向量
        center: (x, y, z) 镜像中心点

    Raises:
        RuntimeError: 如果镜像失败时抛出
    """
    result = _transform_shape(
        project_path, name, "mirror",
        center_x=str(center[0]), center_y=str(center[1]), center_z=str(center[2]),
        plane_normal_x=str(plane_normal[0]), plane_normal_y=str(plane_normal[1]),
        plane_normal_z=str(plane_normal[2])
    )
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to mirror"))


def activate_wcs(
    project_path: str,
    name: str,
    origin: tuple[float, float, float],
    normal: tuple[float, float, float] = (0, 0, 1),
    uvector: tuple[float, float, float] = (1, 0, 0),
) -> None:
    """激活局部工作坐标系 (WCS)。

    Args:
        project_path: .cst 文件的绝对路径
        name: WCS 的名称
        origin: (x, y, z) WCS 原点坐标
        normal: (x, y, z) WCS 法线方向 (默认Z轴)
        uvector: (x, y, z) WCS U轴方向 (默认X轴)

    Raises:
        RuntimeError: 如果无法激活 WCS 时抛出
    """
    vba = f"""With WCS
    .ActivateWCS "local"
    .SetOrigin {origin[0]}, {origin[1]}, {origin[2]}
    .SetNormal {normal[0]}, {normal[1]}, {normal[2]}
    .SetUVector {uvector[0]}, {uvector[1]}, {uvector[2]}
    .SetName "{name}"
End With"""
    result = _add_to_history(project_path, vba, f"Activate WCS: {name}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to activate WCS"))


def deactivate_wcs(project_path: str) -> None:
    """切回全局坐标系 (Global WCS)。

    Args:
        project_path: .cst 文件的绝对路径

    Raises:
        RuntimeError: 如果无法停用 WCS 时抛出
    """
    vba = 'WCS.ActivateWCS "global"'
    result = _add_to_history(project_path, vba, "Deactivate WCS")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to deactivate WCS"))


def arc(
    project_path: str,
    name: str,
    center: tuple[float, float, float],
    radius: float,
    start_angle: float,
    end_angle: float,
    segments: int = 0,
    component: str = "component1",
) -> None:
    """创建一个圆弧曲线。

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
    """
    vba = f"""With Arc
    .Reset
    .Name "{name}"
    .Curve "{component}"
    .Center {center[0]}, {center[1]}, {center[2]}
    .Radius {radius}
    .StartAngle {start_angle}
    .EndAngle {end_angle}
    .Segments {segments}
    .Create
End With"""
    result = _add_to_history(project_path, vba, f"Define Arc: {name}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create arc"))


def polygon(
    project_path: str,
    name: str,
    component: str,
    material: str,
    vertices: Sequence[tuple[float, float]],
    z_range: tuple[float, float],
) -> None:
    """根据顶点坐标创建一个多边形拉伸实体。

    Args:
        project_path: .cst 文件的绝对路径
        name: 实体名称
        component: 文件夹（Component）名称
        material: 材料名称
        vertices: [(x1, y1), (x2, y2), ...] 顶点坐标的列表
        z_range: (最小值, 最大值) 拉伸的 Z 轴范围

    Raises:
        RuntimeError: 如果无法创建多边形时抛出
    """
    if len(vertices) < 3:
        raise ValueError("Polygon requires at least 3 vertices")

    vba_lines = [
        "With Polygon3D",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Component "{component}"',
        f'    .Material "{material}"',
    ]
    for i, (x, y) in enumerate(vertices):
        vba_lines.append(f'    .Point {x}, {y}, {z_range[0]}')
    for i, (x, y) in enumerate(reversed(vertices)):
        vba_lines.append(f'    .Point {x}, {y}, {z_range[1]}')
    vba_lines.extend([
        "    .Create",
        "End With",
    ])
    result = _add_to_history(project_path, "\n".join(vba_lines), f"Define Polygon: {name}")
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Failed to create polygon"))
