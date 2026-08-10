"""建模、网格、求解器和监视器的版本化 VBA 生成器。"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..errors import ValidationError
from .base import CompatibilityProfile, detect_compatibility_profile, unsupported_feature
from .execution import vba_string


CST_2022_SOLVER_TYPES = (
    "HF Time Domain",
    "HF Eigenmode",
    "HF Frequency Domain",
    "HF IntegralEq",
    "HF Multilayer",
    "HF Asymptotic",
    "LF EStatic",
    "LF MStatic",
    "LF Stationary Current",
    "LF Frequency Domain",
    "LF Time Domain (MQS)",
    "PT Tracking",
    "PT Wakefields",
    "PT PIC",
    "Thermal Steady State",
    "Thermal Transient",
    "Mechanics",
)


@dataclass(frozen=True)
class CompatibleVBA:
    lines: tuple[str, ...]
    path: str
    not_applied: dict[str, Any] = field(default_factory=dict)

    def metadata(self, profile: CompatibilityProfile) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "profile": self.path,
            "detected_version": profile.version,
            "detection_source": profile.source,
        }
        if self.not_applied:
            payload["not_applied"] = self.not_applied
        return payload


def _profile(profile: CompatibilityProfile | None) -> CompatibilityProfile:
    resolved = profile or detect_compatibility_profile()
    if resolved.is_2022 or resolved.is_2026_or_later:
        return resolved
    raise unsupported_feature(
        "vba.versioned_template",
        required_capability="known_cst_version",
        next_action="请绑定 CST 2022/2026 Python 库，或设置 CST_RUNTIME_CST_VERSION 后重试。",
    )


def _bool(value: bool) -> str:
    return "True" if value else "False"


def _curve_container_guard_vba(curve: str) -> tuple[str, ...]:
    """确保曲线容器存在，避免曲线项被静默丢弃。"""
    escaped_curve = vba_string(curve)
    tree_path = vba_string(f"Curves\\{curve}")
    return (
        f'If Not SelectTreeItem("{tree_path}") Then',
        f'    Curve.NewCurve "{escaped_curve}"',
        "End If",
    )


def _curve_item_verification_vba(
    curve: str,
    name: str,
    *,
    source: str = "Polygon3D.Create",
) -> tuple[str, ...]:
    """验证曲线项，并通过现有 History 状态文件网关报告失败。"""
    tree_path = vba_string(f"Curves\\{curve}\\{name}")
    full_name = vba_string(f"{curve}:{name}")
    escaped_source = vba_string(source)
    return (
        f'If Not SelectTreeItem("{tree_path}") Then',
        f'    ReportError "{escaped_source}: Curve item was not created: {full_name}"',
        "End If",
    )


def _normalize_temperature_unit(value: str) -> str:
    """把常见温度单位写法转换为 CST 接受的完整名称。"""
    aliases = {
        "celsius": "celsius",
        "degc": "celsius",
        "°c": "celsius",
        "kelvin": "kelvin",
        "k": "kelvin",
        "fahrenheit": "fahrenheit",
        "degf": "fahrenheit",
        "°f": "fahrenheit",
    }
    normalized = aliases.get(str(value).strip().casefold())
    if normalized is None:
        raise ValidationError(
            'temperature 必须是 "Celsius"、"Kelvin" 或 "Fahrenheit"'
        )
    return normalized


def _reject_nondefault(
    profile: CompatibilityProfile,
    feature: str,
    values: dict[str, tuple[Any, Any]],
    capability: str,
) -> None:
    unsupported = [name for name, (value, default) in values.items() if value != default]
    if unsupported:
        raise unsupported_feature(
            feature,
            required_capability=capability,
            unsupported_arguments=unsupported,
            message=f"CST {profile.major} 无法等价表达参数：{', '.join(unsupported)}",
        )


def units_vba(
    *,
    length: str,
    frequency: str,
    voltage: str,
    resistance: str,
    inductance: str,
    temperature: str,
    time: str,
    current: str,
    conductance: str,
    capacitance: str,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    temperature = _normalize_temperature_unit(temperature)
    values = {
        "Length": length,
        "Frequency": frequency,
        "Voltage": voltage,
        "Resistance": resistance,
        "Inductance": inductance,
        "Temperature": temperature,
        "Time": time,
        "Current": current,
        "Conductance": conductance,
        "Capacitance": capacitance,
    }
    if resolved.is_2026_or_later:
        values["Temperature"] = {
            "celsius": "degC",
            "kelvin": "K",
            "fahrenheit": "degF",
        }[temperature]
        return CompatibleVBA(
            tuple(["With Units", *[f'    .SetUnit "{name}", "{value}"' for name, value in values.items()], "End With"]),
            "cst2026",
        )
    unsupported_defaults = {
        "voltage": (voltage, "V"),
        "resistance": (resistance, "Ohm"),
        "inductance": (inductance, "nH"),
        "current": (current, "A"),
        "conductance": (conductance, "S"),
        "capacitance": (capacitance, "pF"),
    }
    _reject_nondefault(resolved, "units.electrical", unsupported_defaults, "units.set_electrical_unit")
    return CompatibleVBA(
        (
            "With Units",
            f'    .Geometry "{length}"',
            f'    .Frequency "{frequency}"',
            f'    .Time "{time}"',
            f'    .TemperatureUnit "{temperature}"',
            "End With",
        ),
        "cst2022",
        not_applied={name: value for name, (value, _default) in unsupported_defaults.items()},
    )


def _axis_ranges_and_centers(
    axis: str,
    range_min: float | str,
    range_max: float | str,
    center1: float | str,
    center2: float | str,
) -> tuple[str, tuple[str, float | str], tuple[str, float | str]]:
    axis_lower = str(axis).strip().lower()
    if axis_lower == "x":
        return "Xrange", ("Ycenter", center1), ("Zcenter", center2)
    if axis_lower == "y":
        return "Yrange", ("Xcenter", center1), ("Zcenter", center2)
    if axis_lower == "z":
        return "Zrange", ("Xcenter", center1), ("Ycenter", center2)
    raise ValidationError('axis 必须是 "x"、"y" 或 "z"')


def _is_literal_zero(value: float | str) -> bool:
    try:
        return float(str(value).strip()) == 0.0
    except ValueError:
        return False


def cylinder_vba(
    *,
    name: str,
    component: str,
    material: str,
    outer_radius: float | str,
    inner_radius: float | str,
    axis: str,
    range_min: float | str,
    range_max: float | str,
    center1: float | str,
    center2: float | str,
    segments: int,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    """按 CST 版本生成圆柱；2026 的中空圆柱用两个实体相减实现。"""
    resolved = _profile(profile)
    range_name, first_center, second_center = _axis_ranges_and_centers(
        axis,
        range_min,
        range_max,
        center1,
        center2,
    )

    def solid_lines(solid_name: str, radius: float | str) -> list[str]:
        lines = [
            "With Cylinder",
            "    .Reset",
            f'    .Name "{solid_name}"',
            f'    .Component "{component}"',
            f'    .Material "{material}"',
        ]
        if resolved.is_2022:
            lines.extend(
                [
                    f'    .Outerradius "{radius}"',
                    f'    .Innerradius "{inner_radius}"',
                ]
            )
        else:
            lines.extend(
                [
                    f'    .Xradius "{radius}"',
                    f'    .Yradius "{radius}"',
                ]
            )
        lines.extend(
            [
                f'    .Axis "{axis}"',
                f'    .{range_name} "{range_min}", "{range_max}"',
                f'    .{first_center[0]} "{first_center[1]}"',
                f'    .{second_center[0]} "{second_center[1]}"',
                f'    .Segments "{segments}"',
                "    .Create",
                "End With",
            ]
        )
        return lines

    lines = solid_lines(name, outer_radius)
    if resolved.is_2026_or_later and not _is_literal_zero(inner_radius):
        inner_name = f"__cst_runtime_inner_{name}"
        lines.extend(solid_lines(inner_name, inner_radius))
        lines.append(
            f'Solid.Subtract "{component}:{name}", "{component}:{inner_name}"'
        )
    return CompatibleVBA(tuple(lines), resolved.label)


def cone_vba(
    *,
    name: str,
    component: str,
    material: str,
    bottom_radius: float | str,
    top_radius: float | str,
    axis: str,
    range_min: float | str,
    range_max: float | str,
    center1: float | str,
    center2: float | str,
    segments: int,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    """按 CST 版本生成圆锥或圆台 VBA。"""
    resolved = _profile(profile)
    range_name, first_center, second_center = _axis_ranges_and_centers(
        axis,
        range_min,
        range_max,
        center1,
        center2,
    )
    lines = [
        "With Cone",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Component "{component}"',
        f'    .Material "{material}"',
    ]
    if resolved.is_2022:
        lines.extend(
            [
                f'    .Bottomradius "{bottom_radius}"',
                f'    .Topradius "{top_radius}"',
            ]
        )
    else:
        lines.extend(
            [
                f'    .Xradius "{bottom_radius}"',
                f'    .Yradius "{bottom_radius}"',
                f'    .XradiusTop "{top_radius}"',
                f'    .YradiusTop "{top_radius}"',
            ]
        )
    lines.extend(
        [
            f'    .Axis "{axis}"',
            f'    .{range_name} "{range_min}", "{range_max}"',
            f'    .{first_center[0]} "{first_center[1]}"',
            f'    .{second_center[0]} "{second_center[1]}"',
            f'    .Segments "{segments}"',
            "    .Create",
            "End With",
        ]
    )
    return CompatibleVBA(tuple(lines), resolved.label)


def background_vba(
    *,
    background_type: str | None = None,
    spaces: tuple[float, float, float, float, float, float] | None = None,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    reset = ".Reset" if resolved.is_2022 else ".ResetBackground"
    lines = ["With Background", f"    {reset}"]
    if background_type is not None:
        lines.append(f'    .Type "{background_type}"')
    if spaces is not None:
        for name, value in zip(("Xmin", "Xmax", "Ymin", "Ymax", "Zmin", "Zmax"), spaces):
            lines.append(f'    .{name}Space "{value}"')
        lines.append('    .ApplyInAllDirections "False"')
    lines.append("End With")
    return CompatibleVBA(tuple(lines), resolved.label)


def mesh_vba(
    *,
    steps_per_wave_near: int,
    steps_per_wave_far: int,
    steps_per_box_near: int,
    steps_per_box_far: int,
    edge_refinement_ratio: int,
    edge_refinement_buffer_lines: int,
    ratio_limit_geometry: int,
    equilibrate_value: float,
    use_gpu: bool,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    if resolved.is_2022:
        _reject_nondefault(
            resolved,
            "mesh.modern_refinement",
            {
                "steps_per_wave_far": (steps_per_wave_far, 5),
                "steps_per_box_far": (steps_per_box_far, 1),
                "edge_refinement_ratio": (edge_refinement_ratio, 2),
                "edge_refinement_buffer_lines": (edge_refinement_buffer_lines, 3),
                "use_gpu": (use_gpu, True),
            },
            "mesh.modern_refinement",
        )
        return CompatibleVBA(
            (
                "With Mesh",
                '    .MeshType "PBA"',
                f'    .LinesPerWavelength "{steps_per_wave_near}"',
                f'    .MinimumStepNumber "{steps_per_box_near}"',
                '    .UseRatioLimit "True"',
                f'    .RatioLimit "{ratio_limit_geometry}"',
                '    .EquilibrateMesh "True"',
                f'    .EquilibrateMeshRatio "{equilibrate_value}"',
                '    .UsePecEdgeModel "True"',
                '    .PointAccEnhancement "0"',
                '    .AutomeshRefineAtPecLines "True", "2"',
                "End With",
            ),
            "cst2022",
            not_applied={
                "steps_per_wave_far": steps_per_wave_far,
                "steps_per_box_far": steps_per_box_far,
                "edge_refinement_ratio": edge_refinement_ratio,
                "edge_refinement_buffer_lines": edge_refinement_buffer_lines,
                "use_gpu": use_gpu,
            },
        )
    return CompatibleVBA(
        (
            'With Mesh',
            '    .MeshType "PBA"',
            '    .SetCreator "High Frequency"',
            "End With",
            "With MeshSettings",
            '    .SetMeshType "Hex"',
            f'    .Set "StepsPerWaveNear", "{steps_per_wave_near}"',
            f'    .Set "StepsPerWaveFar", "{steps_per_wave_far}"',
            f'    .Set "StepsPerBoxNear", "{steps_per_box_near}"',
            f'    .Set "StepsPerBoxFar", "{steps_per_box_far}"',
            f'    .Set "RatioLimitGeometry", "{ratio_limit_geometry}"',
            f'    .Set "EdgeRefinementRatio", "{edge_refinement_ratio}"',
            f'    .Set "EdgeRefinementBufferLines", "{edge_refinement_buffer_lines}"',
            f'    .Set "Equilibrate", "{equilibrate_value}"',
            "End With",
            "With Mesh",
            '    .ConnectivityCheck "True"',
            '    .UsePecEdgeModel "True"',
            '    .PBAVersion "2023042623"',
            '    .SetCADProcessingMethod "MultiThread22", "-1"',
            f'    .SetGPUForMatrixCalculationDisabled "{"0" if use_gpu else "1"}"',
            "End With",
        ),
        "cst2026",
    )


def solver_vba(
    *,
    stimulation_port: str,
    stimulation_mode: str,
    steady_state_limit: float,
    mesh_adaption: bool,
    auto_norm_impedance: bool,
    norming_impedance: float,
    calculate_modes_only: bool,
    s_para_symmetry: bool,
    store_td_results: bool,
    run_discretizer_only: bool,
    full_deembedding: bool,
    superimpose_plw: bool,
    use_sensitivity: bool,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    if resolved.is_2022:
        _reject_nondefault(
            resolved,
            "solver.modern_options",
            {
                "run_discretizer_only": (run_discretizer_only, False),
                "use_sensitivity": (use_sensitivity, False),
            },
            "solver.modern_options",
        )
    lines = ["With Solver"]
    if resolved.is_2026_or_later:
        lines.insert(0, 'Mesh.SetCreator "High Frequency"')
        lines.extend(['    .Method "Hexahedral"', '    .CalculationType "TD-S"'])
    lines.extend(
        [
            f'    .StimulationPort "{stimulation_port}"',
            f'    .StimulationMode "{stimulation_mode}"',
            f'    .SteadyStateLimit "{steady_state_limit}"',
            f'    .MeshAdaption "{_bool(mesh_adaption)}"',
            f'    .AutoNormImpedance "{_bool(auto_norm_impedance)}"',
            f'    .NormingImpedance "{norming_impedance}"',
            f'    .CalculateModesOnly "{_bool(calculate_modes_only)}"',
            f'    .SParaSymmetry "{_bool(s_para_symmetry)}"',
            f'    .StoreTDResultsInCache "{_bool(store_td_results)}"',
            f'    .FullDeembedding "{_bool(full_deembedding)}"',
            f'    .SuperimposePLWExcitation "{_bool(superimpose_plw)}"',
        ]
    )
    if resolved.is_2026_or_later:
        lines.extend(
            [
                f'    .RunDiscretizerOnly "{_bool(run_discretizer_only)}"',
                f'    .UseSensitivityAnalysis "{_bool(use_sensitivity)}"',
            ]
        )
    lines.append("End With")
    return CompatibleVBA(tuple(lines), resolved.label)


def solver_acceleration_vba(
    *,
    use_parallelization: bool,
    max_threads: int,
    max_cpu_devices: int,
    remote_calc: bool,
    use_distributed: bool,
    max_distributed_ports: int,
    distribute_matrix: bool,
    mpi_parallel: bool,
    auto_mpi: bool,
    hardware_accel: bool,
    max_gpus: int,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    if resolved.is_2022:
        _reject_nondefault(
            resolved,
            "solver.acceleration.modern_options",
            {
                "max_cpu_devices": (max_cpu_devices, 2),
                "remote_calc": (remote_calc, False),
                "max_distributed_ports": (max_distributed_ports, 64),
                "auto_mpi": (auto_mpi, False),
                "max_gpus": (max_gpus, 4),
            },
            "solver.acceleration.modern_options",
        )
    lines = ["With Solver"]
    if resolved.is_2026_or_later:
        lines.extend(
            [
                f'    .UseParallelization "{_bool(use_parallelization)}"',
                f'    .MaximumNumberOfCPUDevices "{max_cpu_devices}"',
                f'    .RemoteCalculation "{_bool(remote_calc)}"',
            ]
        )
    lines.extend(
        [
            f'    .MaximumNumberOfThreads "{max_threads}"',
            f'    .UseDistributedComputing "{_bool(use_distributed)}"',
            f'    .DistributeMatrixCalculation "{_bool(distribute_matrix)}"',
            f'    .MPIParallelization "{_bool(mpi_parallel)}"',
            f'    .HardwareAcceleration "{_bool(hardware_accel)}"',
        ]
    )
    if resolved.is_2026_or_later:
        lines.extend(
            [
                f'    .MaxNumberOfDistributedComputingPorts "{max_distributed_ports}"',
                f'    .AutomaticMPI "{_bool(auto_mpi)}"',
                f'    .MaximumNumberOfGPUs "{max_gpus}"',
            ]
        )
    lines.append("End With")
    not_applied = {"use_parallelization": use_parallelization} if resolved.is_2022 else {}
    return CompatibleVBA(tuple(lines), resolved.label, not_applied=not_applied)


def port_vba(
    *,
    port_number: str,
    ranges: tuple[float, float, float, float, float, float],
    orientation: str,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    x_min, x_max, y_min, y_max, z_min, z_max = ranges
    lines = [
        "With Port",
        "    .Reset",
        f'    .PortNumber "{port_number}"',
        '    .Label ""',
    ]
    if resolved.is_2026_or_later:
        lines.append('    .Folder ""')
    lines.extend(
        [
            '    .NumberOfModes "1"',
            '    .AdjustPolarization "False"',
            '    .PolarizationAngle "0.0"',
            '    .ReferencePlaneDistance "0"',
            '    .Coordinates "Free"',
            f'    .Orientation "{orientation}"',
            '    .PortOnBound "False"',
            f"    .Xrange {x_min}, {x_max}",
            f"    .Yrange {y_min}, {y_max}",
            f"    .Zrange {z_min}, {z_max}",
            '    .SingleEnded "False"',
        ]
    )
    if resolved.is_2026_or_later:
        lines.append('    .WaveguideMonitor "False"')
    lines.extend(["    .Create", "End With"])
    return CompatibleVBA(tuple(lines), resolved.label)


def _sample_count(start: float, end: float, step: float) -> int:
    if step <= 0 or end < start:
        raise ValidationError("监视器频率范围要求 step > 0 且 end_freq >= start_freq")
    intervals = (end - start) / step
    rounded = round(intervals)
    if not math.isclose(intervals, rounded, rel_tol=1e-9, abs_tol=1e-9):
        raise ValidationError("CST 2022 监视器频率范围必须能被步长整除")
    return int(rounded) + 1


def monitor_vba(
    *,
    field_type: str,
    start: float,
    end: float,
    step: float | None = None,
    samples: int | None = None,
    name: str,
    dimension: str = "Volume",
    subvolume: tuple[float, float, float, float, float, float] | None = None,
    use_subvolume: bool = False,
    enable_nearfield: bool | None = None,
    modern_setter_style: bool = False,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    normalized_name = name.strip()
    if not normalized_name:
        raise ValidationError("监视器名称不能为空")
    escaped_name = vba_string(normalized_name)
    field_key = str(field_type).strip().casefold()
    is_single_frequency_field = field_key in {"efield", "hfield"}
    is_broadband_farfield = False
    if resolved.is_2022 and field_key == "farfield":
        try:
            is_broadband_farfield = not math.isclose(
                float(start),
                float(end),
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        except (TypeError, ValueError) as exc:
            raise ValidationError("CST 2022 Farfield 监视器频率必须是数值") from exc
    if resolved.is_2022 and is_single_frequency_field:
        try:
            same_frequency = math.isclose(float(start), float(end), rel_tol=1e-12, abs_tol=1e-12)
        except (TypeError, ValueError) as exc:
            raise ValidationError("CST 2022 Efield/Hfield 监视器频率必须是数值") from exc
        if not same_frequency:
            raise unsupported_feature(
                "monitor.frequency_range",
                required_capability="single_frequency_efield_hfield",
                unsupported_arguments=["end"],
                message="CST 2022 的 Efield/Hfield 频域监视器只支持单频，start 与 end 必须相同",
            )
        if samples is not None and int(samples) != 1:
            raise unsupported_feature(
                "monitor.frequency_samples",
                required_capability="single_frequency_efield_hfield",
                unsupported_arguments=["samples"],
                message="CST 2022 的 Efield/Hfield 频域监视器不支持 FrequencySamples",
            )
        count = 1
    elif resolved.is_2022:
        count = int(samples) if samples is not None else _sample_count(start, end, float(step))
        if count < 1:
            raise ValidationError("监视器样本数必须大于零")
    else:
        count = int(samples) if samples is not None else 1
    lines = ["With Monitor", "    .Reset"]
    if resolved.is_2022:
        lines.append(f'    .Name "{escaped_name}"')
        lines.extend(
            [
                '    .Domain "Frequency"',
                f'    .FieldType "{field_type}"',
                f'    .Dimension "{dimension}"',
            ]
        )
        if is_single_frequency_field:
            lines.append(f'    .Frequency "{start}"')
        else:
            lines.extend(
                [
                    f'    .FrequencyRange "{start}", "{end}"',
                    f'    .FrequencySamples "{count}"',
                ]
            )
        if not is_broadband_farfield:
            lines.append(f'    .UseSubvolume "{_bool(use_subvolume)}"')
            if use_subvolume and subvolume is not None:
                lines.append('    .SetSubvolume ' + ", ".join(f'"{value}"' for value in subvolume))
        if enable_nearfield is not None:
            lines.append(f'    .EnableNearfieldCalculation "{_bool(enable_nearfield)}"')
        if field_type.lower() == "farfield":
            lines.append('    .ExportFarfieldSource "False"')
        lines.extend(["    .Create", "End With"])
        not_applied = {"step": step} if is_single_frequency_field and step is not None else {}
        if is_broadband_farfield and use_subvolume:
            not_applied["use_subvolume"] = True
            if subvolume is not None:
                not_applied["subvolume"] = subvolume
        return CompatibleVBA(tuple(lines), "cst2022", not_applied=not_applied)
    if modern_setter_style:
        lines = [
            "With Monitor",
            "    .Reset",
            f'    .SetName "{escaped_name}"',
            '    .SetDimensionType "Farfield"',
            '    .SetDomain "Frequency"',
            f"    .SetDomainRange {start}, {end}",
            f"    .SetStep {step}",
            "    .SetSubVolumeEnabledFlag 1",
        ]
        if subvolume is not None:
            lines.append("    .SetSubVolume " + ", ".join(str(value) for value in subvolume))
        lines.extend(["    .SetNearfieldSamplingFlag 1", "    .SetCreateFieldsFlag 1", "    .Create", "End With"])
        return CompatibleVBA(tuple(lines), "cst2026")
    lines.extend(
        [
            '    .Domain "Frequency"',
            f'    .FieldType "{field_type}"',
            f'    .Dimension "{dimension}"',
            f'    .UseSubvolume "{_bool(use_subvolume)}"',
        ]
    )
    if use_subvolume and subvolume is not None:
        lines.append('    .SetSubvolume ' + ", ".join(f'"{value}"' for value in subvolume))
    if enable_nearfield is not None:
        lines.append(f'    .EnableNearfieldCalculation "{_bool(enable_nearfield)}"')
    if step is not None:
        lines.append(f'    .CreateUsingLinearStep "{start}", "{end}", "{step}"')
    else:
        lines.append(f'    .CreateUsingLinearSamples "{start}", "{end}", "{count}"')
    lines.append("End With")
    return CompatibleVBA(tuple(lines), "cst2026")


def plot_export_vba(
    *,
    preset_name: str,
    output_path: str,
    width: int = 1920,
    height: int = 1080,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    """通过 VBA 全局 Plot 对象导出当前三维视图。"""
    resolved = _profile(profile)
    view_names = {
        "Front": "Front",
        "Back": "Back",
        "Top": "Top",
        "Bottom": "Bottom",
        "Left": "Left",
        "Right": "Right",
        "Isometric": "Perspective",
    }
    if preset_name not in view_names:
        raise ValidationError(f"不支持的三维视图预设: {preset_name}")
    if width <= 0 or height <= 0:
        raise ValidationError("图像宽度和高度必须大于零")

    escaped_view = vba_string(view_names[preset_name])
    escaped_path = vba_string(output_path)
    return CompatibleVBA(
        (
            f'Plot.RestoreView "{escaped_view}"',
            "Plot.ZoomToStructure",
            f'Plot.ExportImage "{escaped_path}", {width}, {height}',
        ),
        resolved.label,
    )


def rectangle_vba(
    *,
    name: str,
    curve: str,
    x_min: float | str,
    x_max: float | str,
    y_min: float | str,
    y_max: float | str,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    """创建矩形曲线项，并满足 CST 2022 的曲线容器前置条件。"""
    resolved = _profile(profile)
    lines = [
        *_curve_container_guard_vba(curve),
        "With Rectangle",
        "    .Reset",
        f'    .Name "{vba_string(name)}"',
        f'    .Curve "{vba_string(curve)}"',
        f'    .Xrange "{vba_string(str(x_min))}", "{vba_string(str(x_max))}"',
        f'    .Yrange "{vba_string(str(y_min))}", "{vba_string(str(y_max))}"',
        "    .Create",
        "End With",
        *_curve_item_verification_vba(curve, name, source="Rectangle.Create"),
    ]
    return CompatibleVBA(tuple(lines), resolved.label)


def polygon3d_vba(
    name: str,
    curve: str,
    points: Iterable[Iterable[Any]],
    *,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    normalized_points = [list(point) for point in points]
    normalized_points = [point for point in normalized_points if len(point) >= 3]
    if len(normalized_points) < 3:
        raise ValidationError("三维多边形至少需要三个有效点")

    escaped_name = vba_string(name)
    escaped_curve = vba_string(curve)
    lines = [
        *_curve_container_guard_vba(curve),
        "With Polygon3D",
        "    .Reset",
        f'    .Name "{escaped_name}"',
        f'    .Curve "{escaped_curve}"',
    ]
    if resolved.is_2022:
        for values in normalized_points:
            lines.append(
                f'    .Point "{vba_string(str(values[0]))}", '
                f'"{vba_string(str(values[1]))}", '
                f'"{vba_string(str(values[2]))}"'
            )
    else:
        encoded_points = ", ".join(
            f'"{vba_string(str(values[0]))}:'
            f'{vba_string(str(values[1]))}:'
            f'{vba_string(str(values[2]))}"'
            for values in normalized_points
        )
        lines.append(f"    .Point {encoded_points}")
        lines.append('    .Closed "False"')
    lines.extend(
        [
            "    .Create",
            "End With",
            *_curve_item_verification_vba(curve, name),
        ]
    )
    return CompatibleVBA(tuple(lines), resolved.label)


def analytical_curve_vba(
    *,
    name: str,
    curve: str,
    law_x: str,
    law_y: str,
    law_z: str,
    param_start: str,
    param_end: str,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    """生成解析曲线；2026 官方接口只能等价表达当前工作平面内的曲线。"""
    resolved = _profile(profile)
    lines = [
        *_curve_container_guard_vba(curve),
        "With AnalyticalCurve",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Curve "{curve}"',
    ]
    if resolved.is_2022:
        lines.extend(
            [
                f'    .LawX "{law_x}"',
                f'    .LawY "{law_y}"',
                f'    .LawZ "{law_z}"',
                f'    .ParameterRange "{param_start}", "{param_end}"',
            ]
        )
    else:
        if not _is_literal_zero(law_z):
            raise unsupported_feature(
                "analytical_curve.3d",
                required_capability="analytical_curve.curve_expression_3d",
                unsupported_arguments=["law_z"],
                message=(
                    "CST 2026 AnalyticalCurve.CurveExpression 只能等价表达当前工作平面内的二维曲线；"
                    "非零 law_z 不能安全转换。"
                ),
            )
        lines.extend(
            [
                f'    .CurveExpression "{law_x}", "{law_y}"',
                '    .ParameterName "t"',
                f'    .Minvalue "{param_start}"',
                f'    .Maxvalue "{param_end}"',
            ]
        )
    lines.extend(
        [
            "    .Create",
            "End With",
            *_curve_item_verification_vba(
                curve,
                name,
                source="AnalyticalCurve.Create",
            ),
        ]
    )
    return CompatibleVBA(tuple(lines), resolved.label)


def loft_vba(
    *,
    name: str,
    component: str,
    material: str,
    tangency: float,
    minimize_twist: bool,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    """生成 Loft；CST 2022 官方对象没有 Minimizetwist。"""
    resolved = _profile(profile)
    lines = [
        "With Loft",
        "    .Reset",
        f'    .Name "{vba_string(name)}"',
        f'    .Component "{vba_string(component)}"',
        f'    .Material "{vba_string(material)}"',
        f'    .Tangency "{tangency}"',
    ]
    if resolved.is_2026_or_later:
        lines.append(f'    .Minimizetwist "{_bool(minimize_twist)}"')
    lines.extend(["    .CreateNew", "End With"])
    not_applied = {"minimize_twist": minimize_twist} if resolved.is_2022 else {}
    return CompatibleVBA(tuple(lines), resolved.label, not_applied=not_applied)


def change_solver_type_vba(
    *,
    solver_type: str,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    """使用 VBA Sub 的无括号语法切换求解器。"""
    resolved = _profile(profile)
    normalized_solver_type = str(solver_type).strip()
    if normalized_solver_type not in CST_2022_SOLVER_TYPES:
        raise ValidationError(
            "solver_type 必须是 CST 2022 ChangeSolverType 文档列出的合法值",
            context={"solver_type": solver_type, "allowed_values": list(CST_2022_SOLVER_TYPES)},
        )
    return CompatibleVBA(
        (f'ChangeSolverType "{vba_string(normalized_solver_type)}"',),
        resolved.label,
    )


def postprocess_activation_vba(
    *,
    operation: str,
    enable: bool,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    """拒绝官方方法表中没有一对一对应项的后处理开关。"""
    resolved = _profile(profile)
    next_action = (
        (
            "CST 2022 需要 ApplyTo(target)、AddOperation(operation) 后再 Run；"
            "当前工具未提供 target，不能安全转换。"
        )
        if resolved.is_2022
        else (
            "CST 2026 官方 PostProcess1D 方法表仅记录 Reset、Calc、GetArray 和 SetCombine；"
            "未记录 ActivateOperation，不能安全下发。"
        )
    )
    raise unsupported_feature(
        "postprocess1d.activate_operation",
        required_capability="postprocess1d.activate_operation",
        unsupported_arguments=["operation", "enable"],
        next_action=next_action,
    )


def mesh_fpbavoid_nonreg_unite_vba(
    *,
    enable: bool,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    """生成仅 CST 2026 支持的 FPBA 非规则合并设置。"""
    resolved = _profile(profile)
    if resolved.is_2022:
        raise unsupported_feature(
            "mesh.fpbavoid_nonreg_unite",
            required_capability="mesh.fpbavoid_nonreg_unite",
            unsupported_arguments=["enable"],
            next_action="CST 2022 无等价设置；请移除此调用或升级 CST。",
        )
    return CompatibleVBA(
        (f'Mesh.FPBAAvoidNonRegUnite {_bool(enable)}',),
        resolved.label,
    )


def extrude_curve_vba(
    *,
    name: str,
    component: str,
    material: str,
    curve: str,
    thickness: float | str,
    twist_angle: float,
    taper_angle: float,
    delete_profile: bool,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    if resolved.is_2022 and ":" not in curve:
        raise ValidationError(
            'CST 2022 ExtrudeCurve.curve 必须是完整曲线项名 "container:item"'
        )
    lines = [
        "With ExtrudeCurve",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Component "{component}"',
        f'    .Material "{material}"',
        f'    .Thickness "{thickness}"',
        f'    .Twistangle "{twist_angle}"',
        f'    .Taperangle "{taper_angle}"',
    ]
    if resolved.is_2026_or_later:
        lines.append(f'    .DeleteProfile "{_bool(delete_profile)}"')
    lines.extend([f'    .Curve "{curve}"', "    .Create", "End With"])
    not_applied = {"delete_profile": False} if resolved.is_2022 and not delete_profile else {}
    return CompatibleVBA(tuple(lines), resolved.label, not_applied=not_applied)


def transform_vba(
    *,
    target_kind: str,
    name: str,
    transform_type: str,
    center: tuple[str, str, str],
    plane_normal: tuple[str, str, str],
    angle: tuple[str, str, str] = ("0", "0", "0"),
    multiple_objects: bool = True,
    group_objects: bool = False,
    repetitions: int = 1,
    destination: str = "",
    vector: tuple[Any, Any, Any] | None = None,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    if resolved.is_2022 and destination:
        raise unsupported_feature(
            "transform.destination",
            required_capability="transform.destination",
            unsupported_arguments=["destination"],
            message="CST 2022 Transform 无法等价表达非空目标组件。",
        )
    lines = ["With Transform", "    .Reset", f'    .Name "{name}"', '    .Origin "Free"']
    if vector is not None:
        lines.append(f'    .Vector "{vector[0]}", "{vector[1]}", "{vector[2]}"')
    else:
        lines.extend(
            [
                f'    .Center "{center[0]}", "{center[1]}", "{center[2]}"',
                f'    .PlaneNormal "{plane_normal[0]}", "{plane_normal[1]}", "{plane_normal[2]}"',
            ]
        )
        if transform_type.lower() != "mirror":
            lines.append(f'    .Angle "{angle[0]}", "{angle[1]}", "{angle[2]}"')
    lines.extend(
        [
            f'    .MultipleObjects "{_bool(multiple_objects)}"',
            f'    .GroupObjects "{_bool(group_objects)}"',
            f'    .Repetitions "{repetitions}"',
            '    .MultipleSelection "False"',
        ]
    )
    if resolved.is_2026_or_later:
        lines.extend([f'    .Destination "{destination}"', '    .AutoDestination "True"'])
    lines.extend(['    .Material ""', f'    .Transform "{target_kind}", "{transform_type}"', "End With"])
    return CompatibleVBA(tuple(lines), resolved.label)


__all__ = [
    "CST_2022_SOLVER_TYPES",
    "CompatibleVBA",
    "background_vba",
    "extrude_curve_vba",
    "change_solver_type_vba",
    "loft_vba",
    "mesh_vba",
    "monitor_vba",
    "plot_export_vba",
    "polygon3d_vba",
    "rectangle_vba",
    "port_vba",
    "solver_acceleration_vba",
    "solver_vba",
    "transform_vba",
    "units_vba",
]
