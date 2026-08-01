"""建模、网格、求解器和监视器的版本化 VBA 生成器。"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..errors import ValidationError
from .base import CompatibilityProfile, detect_compatibility_profile, unsupported_feature


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
                f'    .MinimumLineNumber "{steps_per_box_near}"',
                f'    .MinimumStepNumber "{steps_per_box_far}"',
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
    name: str = "",
    dimension: str = "Volume",
    subvolume: tuple[float, float, float, float, float, float] | None = None,
    use_subvolume: bool = False,
    enable_nearfield: bool | None = None,
    modern_setter_style: bool = False,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    if resolved.is_2022:
        count = int(samples) if samples is not None else _sample_count(start, end, float(step))
        if count < 1:
            raise ValidationError("监视器样本数必须大于零")
    else:
        count = int(samples) if samples is not None else 1
    lines = ["With Monitor", "    .Reset"]
    if resolved.is_2022:
        if name:
            lines.append(f'    .Name "{name}"')
        lines.extend(
            [
                '    .Domain "Frequency"',
                f'    .FieldType "{field_type}"',
                f'    .Dimension "{dimension}"',
                f'    .FrequencyRange "{start}", "{end}"',
                f'    .FrequencySamples "{count}"',
                f'    .UseSubvolume "{_bool(use_subvolume)}"',
            ]
        )
        if subvolume is not None:
            lines.append('    .SetSubvolume ' + ", ".join(f'"{value}"' for value in subvolume))
        if enable_nearfield is not None:
            lines.append(f'    .EnableNearfieldCalculation "{_bool(enable_nearfield)}"')
        if field_type.lower() == "farfield":
            lines.append('    .ExportFarfieldSource "False"')
        lines.extend(["    .Create", "End With"])
        return CompatibleVBA(tuple(lines), "cst2022")
    if modern_setter_style:
        lines = [
            "With Monitor",
            "    .Reset",
            f'    .SetName "{name}"',
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
    if subvolume is not None:
        lines.append('    .SetSubvolume ' + ", ".join(f'"{value}"' for value in subvolume))
    if enable_nearfield is not None:
        lines.append(f'    .EnableNearfieldCalculation "{_bool(enable_nearfield)}"')
    if step is not None:
        lines.append(f'    .CreateUsingLinearStep "{start}", "{end}", "{step}"')
    else:
        lines.append(f'    .CreateUsingLinearSamples "{start}", "{end}", "{count}"')
    lines.append("End With")
    return CompatibleVBA(tuple(lines), "cst2026")


def polygon3d_vba(
    name: str,
    curve: str,
    points: Iterable[Iterable[Any]],
    *,
    profile: CompatibilityProfile | None = None,
) -> CompatibleVBA:
    resolved = _profile(profile)
    lines = ["With Polygon3D", "    .Reset"]
    if resolved.is_2026_or_later:
        lines.append("    .Version 10")
    lines.extend([f'    .Name "{name}"', f'    .Curve "{curve}"'])
    for point in points:
        values = list(point)
        if len(values) >= 3:
            lines.append(f'    .Point "{values[0]}", "{values[1]}", "{values[2]}"')
    lines.extend(["    .Create", "End With"])
    return CompatibleVBA(tuple(lines), resolved.label)


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
    if resolved.is_2022 and delete_profile:
        lines.append(f'Curve.DeleteCurve "{curve}"')
    return CompatibleVBA(tuple(lines), resolved.label)


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
    "CompatibleVBA",
    "background_vba",
    "extrude_curve_vba",
    "mesh_vba",
    "monitor_vba",
    "polygon3d_vba",
    "port_vba",
    "solver_acceleration_vba",
    "solver_vba",
    "transform_vba",
    "units_vba",
]
