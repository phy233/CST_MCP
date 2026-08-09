"""远场结果的新版计算器与 CST 2022 FarfieldPlot 适配。"""
from __future__ import annotations

from typing import Any, Iterable

from .base import get_model3d, profile_for, unsupported_feature
from .execution import execute_text_query, vba_string


def supports_farfield_calculator(project: Any) -> bool:
    model3d = getattr(project, "model3d", None)
    return getattr(model3d, "FarfieldCalculator", None) is not None


def get_farfield_calculator(project: Any) -> Any:
    if not supports_farfield_calculator(project):
        raise unsupported_feature(
            "farfield.calculator",
            project=project,
            required_capability="farfield_calculator",
            next_action="CST 2022 请改用 FarfieldPlot 列表求值兼容路径。",
        )
    return get_model3d(project).FarfieldCalculator


def legacy_farfield_query_vba(
    *,
    tree_path: str,
    plot_mode: str,
    frequency_ghz: float,
    theta_values: Iterable[float],
    phi_values: Iterable[float],
) -> list[str]:
    """构造 CST 2022 列表求值查询体，输出 theta、phi、标量三列。"""
    normalized_mode = plot_mode.strip().lower()
    if normalized_mode not in {"gain", "directivity", "realized gain"}:
        raise ValueError("CST 2022 远场网格仅支持 gain、directivity、realized gain")
    lines = [
        f'SelectTreeItem "{vba_string(tree_path)}"',
        "FarfieldPlot.Reset",
        'FarfieldPlot.SetScaleLinear "False"',
        'FarfieldPlot.DBUnit "0"',
        f'FarfieldPlot.SetPlotMode "{normalized_mode}"',
    ]
    for phi in phi_values:
        for theta in theta_values:
            lines.append(
                f'FarfieldPlot.AddListEvaluationPoint "{theta}", "{phi}", "0", "spherical", "frequency", "{frequency_ghz}"'
            )
    lines.extend(
        [
            'FarfieldPlot.CalculateList ""',
            "Dim cstRtValues As Variant",
            "Dim cstRtTheta As Variant",
            "Dim cstRtPhi As Variant",
            "Dim cstRtIndex As Long",
            'cstRtValues = FarfieldPlot.GetList("spherical abs")',
            'cstRtTheta = FarfieldPlot.GetList("Point_T")',
            'cstRtPhi = FarfieldPlot.GetList("Point_P")',
            "For cstRtIndex = LBound(cstRtValues) To UBound(cstRtValues)",
            "Print #cstRtQueryFile, CStr(cstRtTheta(cstRtIndex)) & vbTab & CStr(cstRtPhi(cstRtIndex)) & vbTab & CStr(cstRtValues(cstRtIndex))",
            "Next cstRtIndex",
        ]
    )
    return lines


def read_legacy_farfield_list(
    project: Any,
    *,
    tree_path: str,
    plot_mode: str,
    frequency_ghz: float,
    theta_values: list[float],
    phi_values: list[float],
) -> tuple[list[float], list[float], list[float]]:
    """执行 CST 2022 FarfieldPlot 查询并解析标量、theta、phi 列表。"""
    lines = execute_text_query(
        project,
        legacy_farfield_query_vba(
            tree_path=tree_path,
            plot_mode=plot_mode,
            frequency_ghz=frequency_ghz,
            theta_values=theta_values,
            phi_values=phi_values,
        ),
        timeout=30.0,
    )
    scalar_values: list[float] = []
    point_theta: list[float] = []
    point_phi: list[float] = []
    for line in lines:
        fields = line.split("\t")
        if len(fields) != 3:
            continue
        point_theta.append(float(fields[0].strip()))
        point_phi.append(float(fields[1].strip()))
        scalar_values.append(float(fields[2].strip()))
    return scalar_values, point_theta, point_phi


def read_farfield_scalar_list(
    project: Any,
    *,
    tree_path: str,
    result_type: str,
    frequency_ghz: float,
    theta_values: list[float],
    phi_values: list[float],
) -> tuple[list[float], list[float], list[float], str, dict[str, Any]]:
    """使用两版都可验证的 FarfieldPlot 列表接口读取角度网格。"""
    profile = profile_for(project)
    scalar_values, point_theta, point_phi = read_legacy_farfield_list(
        project,
        tree_path=tree_path,
        plot_mode=result_type,
        frequency_ghz=frequency_ghz,
        theta_values=theta_values,
        phi_values=phi_values,
    )
    return (
        scalar_values,
        point_theta,
        point_phi,
        "FarfieldPlot",
        profile.metadata(path=profile.label),
    )


__all__ = [
    "get_farfield_calculator",
    "legacy_farfield_query_vba",
    "read_farfield_scalar_list",
    "read_legacy_farfield_list",
    "supports_farfield_calculator",
]
