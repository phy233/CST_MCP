"""CST 2022 超表面电磁设置的版本化 VBA 构造器。"""
from __future__ import annotations

import math
import re
from typing import Any, Sequence

from ..errors import ValidationError
from .base import CompatibilityProfile, unsupported_feature
from .execution import vba_string
from .modeling import CompatibleVBA


FLOQUET_SORT_CODES = (
    "+beta/pw",
    "+beta",
    "-beta",
    "+alpha",
    "-alpha",
    "+te",
    "-te",
    "+tm",
    "-tm",
    "+orderx",
    "-orderx",
    "+ordery",
    "-ordery",
)


def _require_cst2022(profile: CompatibilityProfile, feature: str) -> None:
    if profile.is_2022:
        return
    raise unsupported_feature(
        feature,
        required_capability="cst2022_em_setup",
        next_action="当前实现仅依据本机 CST 2022 对象手册；请先核对目标版本手册。",
    )


def _number(value: int | float) -> str:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("数值必须是有限值")
    return format(number, ".15g")


def unit_cell_boundary_vba(
    *,
    faces: tuple[str, str, str, str, str, str],
    theta: float,
    phi: float,
    direction: str,
    profile: CompatibilityProfile,
) -> CompatibleVBA:
    """生成 CST 2022 Boundary 的逐面和扫描角设置。"""
    _require_cst2022(profile, "unit_cell_boundary")
    normalized_direction = str(direction).strip().casefold()
    if normalized_direction not in {"outward", "inward"}:
        raise ValueError("direction 必须是 outward 或 inward")
    lines = ["With Boundary"]
    for name, value in zip(("Xmin", "Xmax", "Ymin", "Ymax", "Zmin", "Zmax"), faces):
        lines.append(f'    .{name} "{vba_string(value)}"')
    lines.extend(
        [
            '    .ApplyInAllDirections "False"',
            '    .PeriodicUseConstantAngles "True"',
            f'    .SetPeriodicBoundaryAngles "{_number(theta)}", "{_number(phi)}"',
            f'    .SetPeriodicBoundaryAnglesDirection "{normalized_direction}"',
            "End With",
        ]
    )
    return CompatibleVBA(tuple(lines), "cst2022")


def floquet_port_setup_vba(
    *,
    ports: Sequence[dict[str, Any]],
    polarization_basis: str,
    sort_code: str,
    sort_frequency: float | None,
    sort_theta: float,
    sort_phi: float,
    max_order_x: int | None,
    max_order_yprime: int | None,
    profile: CompatibilityProfile,
) -> CompatibleVBA:
    """生成 CST 2022 FloquetPort 的显式或自动模式设置。"""
    _require_cst2022(profile, "floquet_port")
    basis = str(polarization_basis).strip().casefold()
    if basis not in {"linear", "circular"}:
        raise ValueError("polarization_basis 必须是 linear 或 circular")
    normalized_sort = str(sort_code).strip().casefold()
    if normalized_sort not in FLOQUET_SORT_CODES:
        raise ValueError("sort_code 不是 CST 2022 手册允许的排序方式")

    def _optional_number(value: float | int | None) -> str:
        return "" if value is None else _number(value)

    circular_flag = "True" if basis == "circular" else "False"
    lines = ["With FloquetPort", "    .Reset"]
    for index, port in enumerate(ports):
        position = str(port["position"])
        strategy = str(port["mode_strategy"])
        customized_flag = "True" if strategy == "explicit" else "False"
        # 手册要求先用 Port 选定后续调用所针对的端口。
        lines.append(f'    .Port "{position}"')
        if index == 0:
            lines.extend(
                [
                    f'    .SetUseCircularPolarization "{circular_flag}"',
                    f'    .SetDialogFrequency "{_optional_number(sort_frequency)}"',
                    f'    .SetDialogTheta "{_number(sort_theta)}"',
                    f'    .SetDialogPhi "{_number(sort_phi)}"',
                    f'    .SetDialogMaxOrderX "{_optional_number(max_order_x)}"',
                    f'    .SetDialogMaxOrderYPrime "{_optional_number(max_order_yprime)}"',
                    f'    .SetSortCode "{normalized_sort}"',
                ]
            )
        lines.append(f'    .SetCustomizedListFlag "{customized_flag}"')
        if strategy == "explicit":
            for mode in port["modes"]:
                lines.append(
                    '    .AddMode '
                    f'"{mode["type"]}", "{mode["order_x"]}", "{mode["order_yprime"]}"'
                )
        lines.extend(
            [
                f'    .SetNumberOfModesConsidered "{port["modes_considered"]}"',
                f'    .SetDistanceToReferencePlane "{_number(port["reference_distance"])}"',
            ]
        )
    lines.append("End With")
    return CompatibleVBA(tuple(lines), "cst2022")


def plane_wave_vba(
    *,
    normal: tuple[float, float, float],
    e_vector: tuple[float, float, float],
    polarization: str,
    reference_frequency: float | None,
    handedness: str | None,
    phase_difference: float | None,
    axial_ratio: float | None,
    profile: CompatibilityProfile,
) -> CompatibleVBA:
    """生成真正创建 PlaneWave 源的 CST 2022 VBA。"""
    _require_cst2022(profile, "plane_wave")
    if polarization in {"Circular", "Elliptical"} and reference_frequency is None:
        raise ValidationError("Circular/Elliptical 极化必须提供 reference_frequency")
    if polarization == "Elliptical" and phase_difference is None:
        raise ValidationError("Elliptical 极化必须提供 phase_difference")
    if polarization == "Elliptical" and axial_ratio is None:
        raise ValidationError("Elliptical 极化必须提供 axial_ratio")
    lines = [
        "With PlaneWave",
        "    .Reset",
        f'    .Normal "{_number(normal[0])}", "{_number(normal[1])}", "{_number(normal[2])}"',
        f'    .EVector "{_number(e_vector[0])}", "{_number(e_vector[1])}", "{_number(e_vector[2])}"',
        f'    .Polarization "{polarization}"',
    ]
    if polarization in {"Circular", "Elliptical"}:
        lines.append(f'    .ReferenceFrequency "{_number(reference_frequency)}"')
    if polarization in {"Circular", "Elliptical"} and handedness is not None:
        lines.append(f'    .CircularDirection "{handedness}"')
    if polarization == "Elliptical":
        lines.extend(
            [
                f'    .PhaseDifference "{_number(phase_difference)}"',
                f'    .AxialRatio "{_number(axial_ratio)}"',
            ]
        )
    lines.extend(["    .Store", "End With"])
    return CompatibleVBA(tuple(lines), "cst2022")


def frequency_domain_solver_vba(
    *,
    mesh_method: str,
    excitation: dict[str, Any],
    profile: CompatibilityProfile,
) -> CompatibleVBA:
    """仅设置频域网格方法和激励，不执行 FDSolver.Reset。"""
    _require_cst2022(profile, "frequency_domain_solver")
    lines = [
        'ChangeSolverType "HF Frequency Domain"',
        f'FDSolver.SetMethod "{mesh_method}", ""',
    ]
    strategy = excitation["strategy"]
    if strategy == "all":
        lines.append('FDSolver.Stimulation "All", "All"')
    elif strategy == "all_with_floquet":
        lines.append('FDSolver.Stimulation "All+Floquet", "All+Floquet"')
    elif strategy == "plane_wave":
        lines.append('FDSolver.Stimulation "Plane Wave", 1')
    elif strategy == "single":
        lines.append(
            f'FDSolver.Stimulation {excitation["port"]}, {excitation["mode"]}'
        )
    elif strategy == "list":
        lines.append("FDSolver.ResetExcitationList")
        for item in excitation["items"]:
            lines.append(
                'FDSolver.AddToExcitationList '
                f'"{vba_string(item["port"])}", "{vba_string(item["mode"])}"'
            )
        lines.append('FDSolver.Stimulation "List", "List"')
    else:
        raise ValueError("未知的 excitation.strategy")
    if any(re.search(r"(?i)FDSolver\.Reset(?:\s|$)", line) for line in lines):
        raise AssertionError("configure-frequency-domain-solver 禁止生成 FDSolver.Reset")
    return CompatibleVBA(tuple(lines), "cst2022")


__all__ = [
    "FLOQUET_SORT_CODES",
    "frequency_domain_solver_vba",
    "floquet_port_setup_vba",
    "plane_wave_vba",
    "unit_cell_boundary_vba",
]
