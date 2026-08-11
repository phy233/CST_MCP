"""lib 语义操作所需的版本化 VBA 模板。"""
from __future__ import annotations

import math
import re
from typing import Sequence

from .base import CompatibilityProfile
from .modeling import (
    CompatibleVBA,
    _bool,
    _curve_container_guard_vba,
    _curve_item_verification_vba,
    _profile,
    transform_vba,
)


def boundary_per_face_vba(
    *,
    faces: tuple[str, str, str, str, str, str],
    periodic_angle: float,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    # 待完善：该方法只是逐面边界的历史实现，不能视为完整 Unit Cell/Floquet
    # 配置。高级周期角和开放边界需求应由用户在 CST 图形界面中手动完成。
    resolved = _profile(profile)
    lines = ["With Boundary"]
    for name, value in zip(("Xmin", "Xmax", "Ymin", "Ymax", "Zmin", "Zmax"), faces):
        lines.append(f'    .{name} "{value}"')
    lines.append('    .ApplyInAllDirections "False"')
    if resolved.is_2022:
        lines.extend(
            [
                '    .PeriodicUseConstantAngles "True"',
                f'    .SetPeriodicBoundaryAngles "{periodic_angle}", "0"',
            ]
        )
    else:
        lines.extend(
            [
                '    .PeriodicUsePrimitive "False"',
                f'    .SetPeriodicShiftAngle "True", "{periodic_angle}"',
            ]
        )
    lines.append("End With")
    return CompatibleVBA(tuple(lines), resolved.label)


def translate_vba(
    *,
    name: str,
    vector: tuple[float, float, float],
    multiple_objects: bool,
    repetitions: int,
    destination: str,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    return transform_vba(
        target_kind="Shape",
        name=name,
        transform_type="Translate",
        center=("0", "0", "0"),
        plane_normal=("0", "0", "1"),
        vector=vector,
        multiple_objects=multiple_objects,
        repetitions=repetitions,
        destination=destination,
        profile=profile,
    )


def activate_wcs_vba(
    *,
    name: str,
    origin: tuple[float, float, float],
    normal: tuple[float, float, float],
    uvector: tuple[float, float, float],
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    lines = [
        "With WCS",
        '    .ActivateWCS "local"',
        f"    .SetOrigin {origin[0]}, {origin[1]}, {origin[2]}",
        f"    .SetNormal {normal[0]}, {normal[1]}, {normal[2]}",
        f"    .SetUVector {uvector[0]}, {uvector[1]}, {uvector[2]}",
    ]
    if resolved.is_2022:
        lines.append(f'    .Store "{name}"')
    else:
        lines.append(f'    .SetName "{name}"')
    lines.append("End With")
    return CompatibleVBA(tuple(lines), resolved.label)


def deactivate_wcs_vba(*, profile: CompatibilityProfile | None = None) -> CompatibleVBA:
    resolved = _profile(profile)
    return CompatibleVBA(('WCS.ActivateWCS "global"',), resolved.label)


def arc_vba(
    *,
    name: str,
    curve: str,
    center: tuple[float, float, float],
    radius: float,
    start_angle: float,
    end_angle: float,
    segments: int,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    if not resolved.is_2022:
        return CompatibleVBA(
            (
                *_curve_container_guard_vba(curve),
                "With Arc",
                "    .Reset",
                f'    .Name "{name}"',
                f'    .Curve "{curve}"',
                f"    .Center {center[0]}, {center[1]}, {center[2]}",
                f"    .Radius {radius}",
                f"    .StartAngle {start_angle}",
                f"    .EndAngle {end_angle}",
                f"    .Segments {segments}",
                "    .Create",
                "End With",
                *_curve_item_verification_vba(curve, name, source="Arc.Create"),
            ),
            "cst2026",
        )
    start_radians = math.radians(start_angle)
    end_radians = math.radians(end_angle)
    x1 = center[0] + radius * math.cos(start_radians)
    y1 = center[1] + radius * math.sin(start_radians)
    x2 = center[0] + radius * math.cos(end_radians)
    y2 = center[1] + radius * math.sin(end_radians)
    angle = end_angle - start_angle
    orientation = "CounterClockwise" if angle >= 0 else "Clockwise"
    token = re.sub(r"[^A-Za-z0-9_]", "_", name)[:32] or "Arc"
    stored_wcs = f"__CSTRuntime_{token}_WCS"
    lines = [
        *_curve_container_guard_vba(curve),
        f'WCS.Store "{stored_wcs}"',
        'WCS.ActivateWCS "local"',
        f"WCS.SetOrigin 0, 0, {center[2]}",
        "WCS.SetNormal 0, 0, 1",
        "WCS.SetUVector 1, 0, 0",
        "With Arc",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Curve "{curve}"',
        f'    .Orientation "{orientation}"',
        f'    .Xcenter "{center[0]}"',
        f'    .Ycenter "{center[1]}"',
        f'    .X1 "{x1}"',
        f'    .Y1 "{y1}"',
        f'    .X2 "{x2}"',
        f'    .Y2 "{y2}"',
        f'    .Angle "{abs(angle)}"',
        '    .UseAngle "True"',
        f'    .Segments "{segments}"',
        "    .Create",
        "End With",
        f'WCS.Restore "{stored_wcs}"',
        *_curve_item_verification_vba(curve, name, source="Arc.Create"),
    ]
    return CompatibleVBA(
        tuple(lines),
        "cst2022",
        not_applied={"wcs_cleanup": stored_wcs},
    )


def polygon_solid_vba(
    *,
    name: str,
    component: str,
    material: str,
    vertices: Sequence[tuple[float, float]],
    z_range: tuple[float, float],
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    if len(vertices) < 3:
        raise ValueError("Polygon requires at least 3 vertices")
    token = re.sub(r"[^A-Za-z0-9_]", "_", name)[:28] or "Polygon"
    curve = f"__cst_runtime_{token}"
    profile_name = "profile"
    lines = [
        *_curve_container_guard_vba(curve),
        "With Polygon",
        "    .Reset",
        f'    .Name "{profile_name}"',
        f'    .Curve "{curve}"',
        f'    .Point "{vertices[0][0]}", "{vertices[0][1]}"',
    ]
    for x, y in vertices[1:]:
        lines.append(f'    .LineTo "{x}", "{y}"')
    lines.extend(
        [
            f'    .LineTo "{vertices[0][0]}", "{vertices[0][1]}"',
            "    .Create",
            "End With",
            *_curve_item_verification_vba(
                curve,
                profile_name,
                source="Polygon.Create",
            ),
            "With ExtrudeCurve",
            "    .Reset",
            f'    .Name "{name}"',
            f'    .Component "{component}"',
            f'    .Material "{material}"',
            f'    .Thickness "{z_range[1] - z_range[0]}"',
            '    .Twistangle "0"',
            '    .Taperangle "0"',
        ]
    )
    if not resolved.is_2022:
        lines.append('    .DeleteProfile "True"')
    lines.extend(
        [
            f'    .Curve "{curve}:{profile_name}"',
            "    .Create",
            "End With",
        ]
    )
    if z_range[0] != 0:
        lines.extend(
            transform_vba(
                target_kind="Shape",
                name=f"{component}:{name}",
                transform_type="Translate",
                center=("0", "0", "0"),
                plane_normal=("0", "0", "1"),
                vector=(0, 0, z_range[0]),
                multiple_objects=False,
                repetitions=1,
                profile=resolved,
            ).lines
        )
    return CompatibleVBA(tuple(lines), resolved.label)


def waveguide_port_vba(
    *,
    port_number: int,
    face: str,
    width: float | None,
    height: float | None,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    if not resolved.is_2022:
        lines = [
            "With Port",
            "    .Reset",
            f'    .PortNumber "{port_number}"',
            '    .SetNumberOfStimulatedModes "1"',
            '    .SetPortType "Waveguide"',
            f'    .Face "{face}"',
        ]
        if width is not None:
            lines.append(f'    .SetWaveguideWidth "{width}"')
        if height is not None:
            lines.append(f'    .SetWaveguideHeight "{height}"')
        lines.extend(['    .SetWaveguidePort "True"', '    .Create', "End With"])
        return CompatibleVBA(tuple(lines), "cst2026")

    normalized_face = face.strip().lower()
    if normalized_face not in {"xmin", "xmax", "ymin", "ymax", "zmin", "zmax"}:
        raise ValueError("face 必须是 xmin/xmax/ymin/ymax/zmin/zmax 之一")
    lines = [
        "Dim cstRtXmin As Double, cstRtXmax As Double",
        "Dim cstRtYmin As Double, cstRtYmax As Double",
        "Dim cstRtZmin As Double, cstRtZmax As Double",
        "Boundary.GetStructureBox cstRtXmin, cstRtXmax, cstRtYmin, cstRtYmax, cstRtZmin, cstRtZmax",
    ]
    if normalized_face.startswith("z"):
        if width is not None:
            lines.extend(["Dim cstRtXcenter As Double", "cstRtXcenter = (cstRtXmin + cstRtXmax) / 2", f"cstRtXmin = cstRtXcenter - {width} / 2", f"cstRtXmax = cstRtXcenter + {width} / 2"])
        if height is not None:
            lines.extend(["Dim cstRtYcenter As Double", "cstRtYcenter = (cstRtYmin + cstRtYmax) / 2", f"cstRtYmin = cstRtYcenter - {height} / 2", f"cstRtYmax = cstRtYcenter + {height} / 2"])
    elif normalized_face.startswith("x"):
        if width is not None:
            lines.extend(["Dim cstRtYcenter As Double", "cstRtYcenter = (cstRtYmin + cstRtYmax) / 2", f"cstRtYmin = cstRtYcenter - {width} / 2", f"cstRtYmax = cstRtYcenter + {width} / 2"])
        if height is not None:
            lines.extend(["Dim cstRtZcenter As Double", "cstRtZcenter = (cstRtZmin + cstRtZmax) / 2", f"cstRtZmin = cstRtZcenter - {height} / 2", f"cstRtZmax = cstRtZcenter + {height} / 2"])
    else:
        if width is not None:
            lines.extend(["Dim cstRtXcenter As Double", "cstRtXcenter = (cstRtXmin + cstRtXmax) / 2", f"cstRtXmin = cstRtXcenter - {width} / 2", f"cstRtXmax = cstRtXcenter + {width} / 2"])
        if height is not None:
            lines.extend(["Dim cstRtZcenter As Double", "cstRtZcenter = (cstRtZmin + cstRtZmax) / 2", f"cstRtZmin = cstRtZcenter - {height} / 2", f"cstRtZmax = cstRtZcenter + {height} / 2"])
    axis = normalized_face[0]
    bound = f"cstRt{normalized_face.capitalize()}"
    lines.extend(
        [
            "With Port",
            "    .Reset",
            f'    .PortNumber "{port_number}"',
            '    .NumberOfModes "1"',
            '    .Coordinates "Free"',
            f'    .Orientation "{normalized_face}"',
            '    .PortOnBound "True"',
            "    .Xrange cstRtXmin, cstRtXmax",
            "    .Yrange cstRtYmin, cstRtYmax",
            "    .Zrange cstRtZmin, cstRtZmax",
            "    .Create",
            "End With",
        ]
    )
    # 端口所在轴的两个范围端点必须落在同一结构边界平面。
    range_line = {"x": "Xrange", "y": "Yrange", "z": "Zrange"}[axis]
    lines[lines.index(f"    .{range_line} cstRt{axis.upper()}min, cstRt{axis.upper()}max")] = f"    .{range_line} {bound}, {bound}"
    return CompatibleVBA(tuple(lines), "cst2022")


def _floquet_modes(count: int, circular: bool) -> list[tuple[str, int, int]]:
    if count < 1:
        raise ValueError("Floquet 模式数必须大于零")
    types = ("LCP", "RCP") if circular else ("TE", "TM")
    orders = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
    modes: list[tuple[str, int, int]] = []
    for order_x, order_y in orders:
        for mode_type in types:
            modes.append((mode_type, order_x, order_y))
            if len(modes) == count:
                return modes
    raise ValueError("当前兼容模板最多显式定义 10 个 Floquet 模式")


def floquet_port_vba(
    *,
    zmin_modes: int,
    zmax_modes: int,
    zmin_reference_distance: float,
    zmax_reference_distance: float,
    polarization_type: str,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    # 待完善：该历史模板并未覆盖 FloquetPort 的全部高级组合。后续扩展前必须
    # 重新核对目标 CST 版本本地手册和实际工程；本轮仅保留现有行为。
    resolved = _profile(profile)
    if not resolved.is_2022:
        return CompatibleVBA(
            (
                "With Port",
                "    .Reset",
                "    .Floquet",
                f'    .SetDialogParameter "ZminModes", "{zmin_modes}"',
                f'    .SetDialogParameter "ZmaxModes", "{zmax_modes}"',
                f'    .SetDialogParameter "ZminReferenceDistance", "{zmin_reference_distance}"',
                f'    .SetDialogParameter "ZmaxReferenceDistance", "{zmax_reference_distance}"',
                f'    .SetDialogParameter "PolarizationType", "{polarization_type}"',
                "    .CreateFloquetPort",
                "End With",
            ),
            "cst2026",
        )
    circular = polarization_type.strip().lower() == "circular"
    if polarization_type.strip().lower() not in {"linear", "circular"}:
        raise ValueError("polarization_type 必须为 linear 或 circular")
    lines = ["With FloquetPort", "    .Reset", f'    .SetUseCircularPolarization "{_bool(circular)}"']
    for position, count, distance in (
        ("Zmin", zmin_modes, zmin_reference_distance),
        ("Zmax", zmax_modes, zmax_reference_distance),
    ):
        lines.extend([f'    .Port "{position}"', '    .SetCustomizedListFlag "True"'])
        for mode_type, order_x, order_y in _floquet_modes(count, circular):
            lines.append(f'    .AddMode "{mode_type}", "{order_x}", "{order_y}"')
        lines.extend(
            [
                f'    .SetNumberOfModesConsidered "{count}"',
                f'    .SetDistanceToReferencePlane "{distance}"',
            ]
        )
    lines.append("End With")
    return CompatibleVBA(tuple(lines), "cst2022")


__all__ = [
    "activate_wcs_vba",
    "arc_vba",
    "boundary_per_face_vba",
    "deactivate_wcs_vba",
    "floquet_port_vba",
    "polygon_solid_vba",
    "translate_vba",
    "waveguide_port_vba",
]
