from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from . import buffer
from .error_gateway import submit_vba_history
from .errors import CSTRuntimeError, error_response, success_response
from .compatibility import detect_compatibility_profile
from .compatibility.modeling import (
    background_vba,
    extrude_curve_vba,
    mesh_vba,
    monitor_vba,
    polygon3d_vba,
    port_vba,
    solver_vba,
    transform_vba,
    units_vba,
)
from .compatibility.lib import (
    activate_wcs_vba,
    arc_vba,
    boundary_per_face_vba,
    deactivate_wcs_vba,
    floquet_port_vba,
    polygon_solid_vba,
    translate_vba,
    waveguide_port_vba,
)
from .identity import attach_expected_project
from .utils import abs_project_path as _abs_project_path


def _add_vba_history(project_path: str, history_name: str, vba_lines: list[str], project: Any = None) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    if buffer.is_batch_mode(normalized_project):
        buffer.append_to_batch(normalized_project, vba_lines)
        return success_response(
            submission="buffered",
            execution="not_run",
            verification="not_run",
            project_path=normalized_project,
            history_label=history_name,
        )
    if project is None:
        project, status = attach_expected_project(normalized_project)
        if project is None:
            return status

    # PROFILING
    import time
    from . import utils as core_utils
    is_profile = hasattr(core_utils, "_PROFILE_DATA")
    if is_profile and core_utils._PROFILE_DATA["t_com_begin"] == 0:
        core_utils._PROFILE_DATA["t_com_begin"] = time.perf_counter()

    result = submit_vba_history(
        project,
        history_name,
        vba_lines,
        project_path=normalized_project,
    )

    # PROFILING
    if is_profile and core_utils._PROFILE_DATA["t_com_end"] == 0:
        core_utils._PROFILE_DATA["t_com_end"] = time.perf_counter()

    return result


def _single_vba(project_path: str, history_name: str, vba: str, project: Any = None) -> dict[str, Any]:
    return _add_vba_history(project_path, history_name, [vba], project=project)


def _submit_versioned_vba(
    project_path: str,
    history_name: str,
    builder: Any,
    **arguments: Any,
) -> dict[str, Any]:
    """生成已确认版本的 VBA，并把兼容路径写入成功响应。"""
    try:
        profile = detect_compatibility_profile()
        generated = builder(profile=profile, **arguments)
        result = _add_vba_history(project_path, history_name, list(generated.lines))
        if result.get("status") != "error":
            result["compatibility"] = generated.metadata(profile)
        return result
    except CSTRuntimeError as exc:
        return exc.to_response(project_path=_abs_project_path(project_path))
    except (TypeError, ValueError) as exc:
        return error_response(
            "invalid_arguments",
            str(exc),
            phase="validation",
            project_path=_abs_project_path(project_path),
        )


def begin_batch(project_path: str, summary: str = "Batch Execution") -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    try:
        buffer.begin_batch(normalized_project, summary=summary)
        return success_response(
            submission="buffered",
            execution="not_run",
            verification="not_run",
            project_path=normalized_project,
        )
    except RuntimeError as exc:
        return error_response(
            "begin_batch_failed", str(exc),
            project_path=normalized_project,
            runtime_module="cst_runtime.modeling",
        )


def flush_batch(project_path: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    try:
        name, script = buffer.peek_batch(normalized_project)
    except RuntimeError as exc:
        return error_response(
            "flush_batch_failed", str(exc),
            project_path=normalized_project,
            runtime_module="cst_runtime.modeling",
        )
    if not script.strip():
        buffer.commit_batch(normalized_project)
        return success_response(
            submission="not_required",
            execution="not_run",
            verification="not_run",
            project_path=normalized_project,
            message="empty batch, nothing to flush",
            batch_committed=True,
        )

    project, status = attach_expected_project(normalized_project)
    if project is None:
        return {**status, "batch_retained": True, "retry_safe": True}

    result = submit_vba_history(
        project,
        name,
        [script],
        project_path=normalized_project,
        feature="modeling.batch",
    )
    if result.get("ok") is True:
        buffer.commit_batch(normalized_project)
        return {**result, "batch_committed": True}
    return {**result, "batch_retained": True, "retry_safe": False}


def discard_batch(project_path: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    buffer.discard_batch(normalized_project)
    return success_response(
        submission="discarded",
        execution="not_run",
        verification="not_run",
        project_path=normalized_project,
    )


_BUILTIN_MATERIALS = frozenset({
    "PEC", "Vacuum", "Copper", "Gold", "Aluminum", "Brass", "Bronze",
    "Silver", "Steel", "Nickel", "Iron", "Tin", "Zinc", "Lead",
})


def _define_material(project_path: str, material: str) -> dict[str, Any]:
    if material in _BUILTIN_MATERIALS:
        return {"status": "success", "message": f"built-in material '{material}'"}
    return {"status": "success", "message": f"material '{material}' (will resolve at build time)"}


def define_material_from_mtd(project_path: str, material_name: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    skill_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    mtd_path = skill_root / "references" / "Materials" / f"{material_name}.mtd"
    if not mtd_path.exists():
        return error_response(
            "material_mtd_not_found",
            f"Material MTD file not found: {mtd_path}",
            project_path=normalized_project,
        )
    try:
        mtd_content = mtd_path.read_text(encoding="utf-8").strip()
        lines = mtd_content.split("\n")
        vba_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                continue
            vba_lines.append(stripped)
        res = _add_vba_history(normalized_project, f"Define Material: {material_name}", vba_lines, project=project)
        if res.get("status") == "error":
            return res
        return {"status": "success", "project_path": normalized_project, "material_name": material_name}
    except Exception as exc:
        return error_response(
            "define_material_from_mtd_failed",
            str(exc),
            project_path=normalized_project,
            material_name=material_name,
        )


def define_brick(
    project_path: str,
    name: str,
    component: str,
    material: str,
    x_min: float | str,
    x_max: float | str,
    y_min: float | str,
    y_max: float | str,
    z_min: float | str,
    z_max: float | str,
) -> dict[str, Any]:
    mat_result = _define_material(project_path, material)
    if mat_result.get("status") == "error":
        return mat_result
    vba = [
        "With Brick",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Component "{component}"',
        f'    .Material "{material}"',
        f"    .Xrange {x_min}, {x_max}",
        f"    .Yrange {y_min}, {y_max}",
        f"    .Zrange {z_min}, {z_max}",
        "    .Create",
        "End With",
    ]
    return _add_vba_history(project_path, f"Define Brick:{name}", vba)


def define_cylinder(
    project_path: str,
    name: str,
    component: str,
    material: str,
    outer_radius: float | str,
    inner_radius: float | str,
    axis: str,
    range_min: float | str | None = None,
    range_max: float | str | None = None,
    z_min: float | str | None = None,
    z_max: float | str | None = None,
    center1: float | str = 0.0,
    center2: float | str = 0.0,
    x_center: float | str | None = None,
    y_center: float | str | None = None,
    segments: int = 0,
) -> dict[str, Any]:
    if range_min is None and z_min is not None:
        range_min = z_min
    if range_max is None and z_max is not None:
        range_max = z_max
    if center1 is None and x_center is not None:
        center1 = x_center
    if center2 is None and y_center is not None:
        center2 = y_center
    if range_min is None or range_max is None:
        return error_response(
            "missing_argument",
            "range_min or z_min (and range_max or z_max) is required",
        )

    axis_lower = axis.lower()
    if axis_lower == "x":
        range_param = f"Xrange {range_min}, {range_max}"
        c1, c2 = ".Ycenter", ".Zcenter"
    elif axis_lower == "y":
        range_param = f"Yrange {range_min}, {range_max}"
        c1, c2 = ".Xcenter", ".Zcenter"
    else:
        range_param = f"Zrange {range_min}, {range_max}"
        c1, c2 = ".Xcenter", ".Ycenter"

    vba = [
        "With Cylinder",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Component "{component}"',
        f'    .Material "{material}"',
        f"    .OuterRadius {outer_radius}",
        f"    .InnerRadius {inner_radius}",
        f'    .Axis "{axis}"',
        f"    .{range_param}",
        f"    {c1} {center1}",
        f"    {c2} {center2}",
        f'    .Segments "{segments}"',
        "    .Create",
        "End With",
    ]
    return _add_vba_history(project_path, f"Define Cylinder:{name}", vba)


def define_cone(
    project_path: str,
    name: str,
    component: str,
    material: str,
    bottom_radius: float | str,
    top_radius: float | str,
    axis: str,
    range_min: float | str | None = None,
    range_max: float | str | None = None,
    z_min: float | str | None = None,
    z_max: float | str | None = None,
    center1: float | str = 0.0,
    center2: float | str = 0.0,
    x_center: float | str | None = None,
    y_center: float | str | None = None,
    segments: int = 0,
) -> dict[str, Any]:
    if range_min is None and z_min is not None:
        range_min = z_min
    if range_max is None and z_max is not None:
        range_max = z_max
    if center1 is None and x_center is not None:
        center1 = x_center
    if center2 is None and y_center is not None:
        center2 = y_center
    if range_min is None or range_max is None:
        return error_response(
            "missing_argument",
            "range_min or z_min (and range_max or z_max) is required",
        )

    axis_lower = axis.lower()
    if axis_lower == "x":
        range_param = f"Xrange {range_min}, {range_max}"
        c1, c2 = ".Ycenter", ".Zcenter"
    elif axis_lower == "y":
        range_param = f"Yrange {range_min}, {range_max}"
        c1, c2 = ".Xcenter", ".Zcenter"
    else:
        range_param = f"Zrange {range_min}, {range_max}"
        c1, c2 = ".Xcenter", ".Ycenter"

    vba = [
        "With Cone",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Component "{component}"',
        f'    .Material "{material}"',
        f"    .BottomRadius {bottom_radius}",
        f"    .TopRadius {top_radius}",
        f'    .Axis "{axis}"',
        f"    .{range_param}",
        f"    {c1} {center1}",
        f"    {c2} {center2}",
        f'    .Segments "{segments}"',
        "    .Create",
        "End With",
    ]
    return _add_vba_history(project_path, f"Define Cone:{name}", vba)


def define_rectangle(
    project_path: str,
    name: str,
    curve: str,
    x_min: float | str,
    x_max: float | str,
    y_min: float | str,
    y_max: float | str,
) -> dict[str, Any]:
    vba = [
        "With Rectangle",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Curve "{curve}"',
        f"    .Xrange {x_min}, {x_max}",
        f"    .Yrange {y_min}, {y_max}",
        "    .Create",
        "End With",
    ]
    return _add_vba_history(project_path, f"Define Rectangle:{name}", vba)


def boolean_subtract(project_path: str, target: str, tool: str) -> dict[str, Any]:
    vba = f'Solid.Subtract "{target}", "{tool}"'
    return _single_vba(project_path, f"boolean subtract: {target} - {tool}", vba)


def boolean_add(project_path: str, shape1: str, shape2: str) -> dict[str, Any]:
    vba = f'Solid.Add "{shape1}", "{shape2}"'
    return _single_vba(project_path, f"boolean add: {shape1} + {shape2}", vba)


def boolean_intersect(project_path: str, shape1: str, shape2: str) -> dict[str, Any]:
    vba = f'Solid.Intersect "{shape1}", "{shape2}"'
    return _single_vba(project_path, f"boolean intersect: {shape1} & {shape2}", vba)


def boolean_insert(project_path: str, shape1: str, shape2: str) -> dict[str, Any]:
    vba = f'Solid.Insert "{shape1}", "{shape2}"'
    return _single_vba(project_path, f"boolean insert: {shape1} <- {shape2}", vba)


def delete_entity(project_path: str, component: str, name: str) -> dict[str, Any]:
    full_name = f"{component}:{name}"
    vba = f'Solid.Delete "{full_name}"'
    return _single_vba(project_path, f"delete entity: {full_name}", vba)


def create_component(project_path: str, component_name: str) -> dict[str, Any]:
    vba = f'Component.New "{component_name}"'
    return _single_vba(project_path, f"create component: {component_name}", vba)


def change_material(project_path: str, shape_name: str, material: str) -> dict[str, Any]:
    mat_result = _define_material(project_path, material)
    if mat_result.get("status") == "error":
        return mat_result
    vba = f'Solid.ChangeMaterial "{shape_name}", "{material}"'
    return _single_vba(project_path, f"change material: {shape_name}", vba)


def define_frequency_range(project_path: str, start_freq: float, end_freq: float) -> dict[str, Any]:
    vba = f'Solver.FrequencyRange "{start_freq}", "{end_freq}"'
    return _single_vba(project_path, "define frequency range", vba)


def change_frequency_range(project_path: str, min_frequency: str, max_frequency: str) -> dict[str, Any]:
    vba = f'Solver.FrequencyRange "{min_frequency}", "{max_frequency}"'
    return _single_vba(project_path, "ChangeFrequency", vba)


def change_solver_type(project_path: str, solver_type: str) -> dict[str, Any]:
    vba = f'ChangeSolverType("{solver_type}")'
    return _single_vba(project_path, f"change solver type to {solver_type}", vba)


def define_background(project_path: str, background_type: str = "Normal") -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "define background",
        background_vba,
        background_type=background_type,
    )


def define_boundary(project_path: str, face_type: str = "expanded open", symmetry_type: str = "none") -> dict[str, Any]:
    vba = [
        "With Boundary",
        f'.Xmin "{face_type}"',
        f'.Xmax "{face_type}"',
        f'.Ymin "{face_type}"',
        f'.Ymax "{face_type}"',
        f'.Zmin "{face_type}"',
        f'.Zmax "{face_type}"',
        f'.Xsymmetry "{symmetry_type}"',
        f'.Ysymmetry "{symmetry_type}"',
        f'.Zsymmetry "{symmetry_type}"',
        "End With",
    ]
    return _add_vba_history(project_path, "define boundary", vba)


def define_mesh(
    project_path: str,
    steps_per_wave_near: int = 5,
    steps_per_wave_far: int = 5,
    steps_per_box_near: int = 5,
    steps_per_box_far: int = 1,
    edge_refinement_ratio: int = 2,
    edge_refinement_buffer_lines: int = 3,
    ratio_limit_geometry: int = 10,
    equilibrate_value: float = 1.5,
    use_gpu: bool = True,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "Define Mesh",
        mesh_vba,
        steps_per_wave_near=steps_per_wave_near,
        steps_per_wave_far=steps_per_wave_far,
        steps_per_box_near=steps_per_box_near,
        steps_per_box_far=steps_per_box_far,
        edge_refinement_ratio=edge_refinement_ratio,
        edge_refinement_buffer_lines=edge_refinement_buffer_lines,
        ratio_limit_geometry=ratio_limit_geometry,
        equilibrate_value=equilibrate_value,
        use_gpu=use_gpu,
    )


def define_solver(
    project_path: str,
    stimulation_port: str = "All",
    stimulation_mode: str = "All",
    steady_state_limit: float = -40,
    mesh_adaption: bool = False,
    auto_norm_impedance: bool = True,
    norming_impedance: float = 50,
    calculate_modes_only: bool = False,
    s_para_symmetry: bool = False,
    store_td_results: bool = False,
    run_discretizer_only: bool = False,
    full_deembedding: bool = False,
    superimpose_plw: bool = False,
    use_sensitivity: bool = False,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "Define Solver",
        solver_vba,
        stimulation_port=stimulation_port,
        stimulation_mode=stimulation_mode,
        steady_state_limit=steady_state_limit,
        mesh_adaption=mesh_adaption,
        auto_norm_impedance=auto_norm_impedance,
        norming_impedance=norming_impedance,
        calculate_modes_only=calculate_modes_only,
        s_para_symmetry=s_para_symmetry,
        store_td_results=store_td_results,
        run_discretizer_only=run_discretizer_only,
        full_deembedding=full_deembedding,
        superimpose_plw=superimpose_plw,
        use_sensitivity=use_sensitivity,
    )


def define_port(
    project_path: str,
    port_number: str,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z_min: float,
    z_max: float,
    orientation: str,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        f"Define Port:{port_number}",
        port_vba,
        port_number=port_number,
        ranges=(x_min, x_max, y_min, y_max, z_min, z_max),
        orientation=orientation,
    )


def define_monitor(project_path: str, start_freq: float, end_freq: float, step: float) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        f"Define Monitor:{start_freq}-{end_freq}",
        monitor_vba,
        field_type="Farfield",
        start=start_freq,
        end=end_freq,
        step=step,
        name=f"farfield (f={start_freq})_1",
        subvolume=(-105, 105, -105, 105, 0, 445),
        use_subvolume=True,
        enable_nearfield=True,
        modern_setter_style=True,
    )


def rename_entity(project_path: str, old_name: str, new_name: str) -> dict[str, Any]:
    vba = f'Solid.Rename "{old_name}", "{new_name}"'
    return _single_vba(project_path, f"rename: {old_name} -> {new_name}", vba)


def set_entity_color(
    project_path: str,
    shape_name: str,
    use_individual_color: bool = True,
    r: int = 192,
    g: int = 192,
    b: int = 192,
) -> dict[str, Any]:
    vba_use = "1" if use_individual_color else "0"
    vba = [
        f'Solid.SetUseIndividualColor "{shape_name}", {vba_use}',
        f'Solid.ChangeIndividualColor "{shape_name}", "{r}", "{g}", "{b}"',
    ]
    return _add_vba_history(project_path, f"set color: {shape_name}", vba)


def define_units(
    project_path: str,
    length: str = "mm",
    frequency: str = "GHz",
    voltage: str = "V",
    resistance: str = "Ohm",
    inductance: str = "nH",
    temperature: str = "degC",
    time: str = "ns",
    current: str = "A",
    conductance: str = "S",
    capacitance: str = "pF",
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "Define Units",
        units_vba,
        length=length,
        frequency=frequency,
        voltage=voltage,
        resistance=resistance,
        inductance=inductance,
        temperature=temperature,
        time=time,
        current=current,
        conductance=conductance,
        capacitance=capacitance,
    )


def set_farfield_monitor(
    project_path: str,
    start_freq: float,
    end_freq: float,
    step: float = 1,
    subvolume_x_min: float = -105,
    subvolume_x_max: float = 105,
    subvolume_y_min: float = -105,
    subvolume_y_max: float = 105,
    subvolume_z_min: float = 0,
    subvolume_z_max: float = 445,
    enable_nearfield: bool = True,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "Set Farfield Monitor",
        monitor_vba,
        field_type="Farfield",
        start=start_freq,
        end=end_freq,
        step=step,
        subvolume=(
            subvolume_x_min,
            subvolume_x_max,
            subvolume_y_min,
            subvolume_y_max,
            subvolume_z_min,
            subvolume_z_max,
        ),
        use_subvolume=False,
        enable_nearfield=enable_nearfield,
    )


def set_efield_monitor(
    project_path: str,
    start_freq: float,
    end_freq: float,
    step: float = 1,
    dimension: str = "Volume",
    subvolume_x_min: float = -105,
    subvolume_x_max: float = 105,
    subvolume_y_min: float = -105,
    subvolume_y_max: float = 105,
    subvolume_z_min: float = 0,
    subvolume_z_max: float = 443,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "Set Efield Monitor",
        monitor_vba,
        field_type="Efield",
        start=start_freq,
        end=end_freq,
        step=step,
        dimension=dimension,
        subvolume=(
            subvolume_x_min,
            subvolume_x_max,
            subvolume_y_min,
            subvolume_y_max,
            subvolume_z_min,
            subvolume_z_max,
        ),
        use_subvolume=False,
    )


def set_field_monitor(project_path: str, field_type: str, start_frequency: str, end_frequency: str, num_samples: str) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        f"Set{field_type}Monitor",
        monitor_vba,
        field_type=f"{field_type}field",
        start=start_frequency,
        end=end_frequency,
        samples=num_samples,
    )


def set_probe(project_path: str, field_type: str, x_pos: str, y_pos: str, z_pos: str) -> dict[str, Any]:
    vba = f'Probe.Reset\nProbe.AutoLabel 1\nProbe.Field "{field_type}field"\nProbe.Orientation "All"\nProbe.Xpos "{x_pos}"\nProbe.Ypos "{y_pos}"\nProbe.Zpos "{z_pos}"\nProbe.Create'
    return _single_vba(project_path, f"Set{field_type}Probe", vba)


def delete_probe_by_id(project_path: str, probe_id: str) -> dict[str, Any]:
    vba = f'Probe.DeleteById "{probe_id}"'
    return _single_vba(project_path, f"DeleteProbe{probe_id}", vba)


def delete_monitor(project_path: str, monitor_name: str) -> dict[str, Any]:
    vba = f'Monitor.Delete "{monitor_name}"'
    return _single_vba(project_path, f"delete monitor: {monitor_name}", vba)


def set_background_with_space(
    project_path: str,
    x_min_space: float = 30,
    x_max_space: float = 30,
    y_min_space: float = 30,
    y_max_space: float = 30,
    z_min_space: float = 50,
    z_max_space: float = 100,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "Set Background Space",
        background_vba,
        spaces=(x_min_space, x_max_space, y_min_space, y_max_space, z_min_space, z_max_space),
    )


def set_farfield_plot_cuts(project_path: str, lateral_cuts: list | None = None, polar_cuts: list | None = None) -> dict[str, Any]:
    if lateral_cuts is None:
        lateral_cuts = [("0", "1"), ("90", "1")]
    if polar_cuts is None:
        polar_cuts = [("90", "1")]
    vba = ["With FarfieldPlot", "    .ClearCuts"]
    for phi, active in lateral_cuts:
        vba.append(f'    .AddCut "lateral", "{phi}", "{active}"')
    for theta, active in polar_cuts:
        vba.append(f'    .AddCut "polar", "{theta}", "{active}"')
    vba.append("End With")
    return _add_vba_history(project_path, "set farfield cuts", vba)


def show_bounding_box(project_path: str) -> dict[str, Any]:
    return _single_vba(project_path, "switch bounding box", 'Plot.DrawBox "True"')


def activate_post_process_operation(project_path: str, operation: str, enable: bool = True) -> dict[str, Any]:
    flag = "true" if enable else "false"
    vba = f'PostProcess1D.ActivateOperation "{operation}", "{flag}"'
    return _single_vba(project_path, f"activate post process: {operation}", vba)


def create_mesh_group(project_path: str, group_name: str, items: list[str]) -> dict[str, Any]:
    result = _single_vba(project_path, f"create mesh group: {group_name}", f'Group.Add "{group_name}", "mesh"')
    if result.get("status") == "error":
        return result
    for item in items:
        sub = _single_vba(project_path, f"add item to group: {group_name}", f'Group.AddItem "solid${item}", "{group_name}"')
        if sub.get("status") == "error":
            return sub
    return {
        "status": "success",
        "project_path": result.get("project_path"),
        "message": f"Mesh group {group_name} created with {len(items)} items",
    }


def define_polygon_3d(project_path: str, name: str, curve: str, points: list[list]) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        f"Define Polygon3D: {name}",
        polygon3d_vba,
        name=name,
        curve=curve,
        points=points,
    )


def define_analytical_curve(project_path: str, name: str, curve: str, law_x: str, law_y: str, law_z: str, param_start: str, param_end: str) -> dict[str, Any]:
    vba = [
        "With AnalyticalCurve",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Curve "{curve}"',
        f'    .LawX "{law_x}"',
        f'    .LawY "{law_y}"',
        f'    .LawZ "{law_z}"',
        f'    .ParameterRange "{param_start}", "{param_end}"',
        "    .Create",
        "End With",
    ]
    return _add_vba_history(project_path, f"Define AnalyticalCurve: {name}", vba)


def define_extrude_curve(
    project_path: str,
    name: str,
    component: str,
    material: str,
    curve: str,
    thickness: float | str,
    twist_angle: float = 0.0,
    taper_angle: float = 0.0,
    delete_profile: bool = True,
) -> dict[str, Any]:
    try:
        profile = detect_compatibility_profile()
        generated = extrude_curve_vba(
            name=name,
            component=component,
            material=material,
            curve=curve,
            thickness=thickness,
            twist_angle=twist_angle,
            taper_angle=taper_angle,
            delete_profile=delete_profile,
            profile=profile,
        )
    except CSTRuntimeError as exc:
        return exc.to_response(project_path=_abs_project_path(project_path))
    mat_result = _define_material(project_path, material)
    if mat_result.get("status") == "error":
        return mat_result
    result = _add_vba_history(project_path, f"Define ExtrudeCurve: {name}", list(generated.lines))
    if result.get("status") != "error":
        result["compatibility"] = generated.metadata(profile)
    return result


def transform_shape(
    project_path: str,
    shape_name: str,
    transform_type: str,
    center_x: str = "0",
    center_y: str = "0",
    center_z: str = "0",
    plane_normal_x: str = "0",
    plane_normal_y: str = "1",
    plane_normal_z: str = "0",
    angle_x: str = "0",
    angle_y: str = "0",
    angle_z: str = "0",
    multiple_objects: bool = True,
    group_objects: bool = False,
    repetitions: int = 1,
    destination: str = "",
) -> dict[str, Any]:
    ttype = {"mirror": "Mirror", "rotate": "Rotate"}.get(transform_type.lower(), transform_type)
    return _submit_versioned_vba(
        project_path,
        f"transform shape: {shape_name}",
        transform_vba,
        target_kind="Shape",
        name=shape_name,
        transform_type=ttype,
        center=(center_x, center_y, center_z),
        plane_normal=(plane_normal_x, plane_normal_y, plane_normal_z),
        angle=(angle_x, angle_y, angle_z),
        multiple_objects=multiple_objects,
        group_objects=group_objects,
        repetitions=repetitions,
        destination=destination,
    )


def transform_curve(
    project_path: str,
    curve_name: str,
    center_x: str = "0",
    center_y: str = "0",
    center_z: str = "0",
    plane_normal_x: str = "0",
    plane_normal_y: str = "1",
    plane_normal_z: str = "0",
    multiple_objects: bool = True,
    group_objects: bool = False,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        f"transform curve: {curve_name}",
        transform_vba,
        target_kind="Curve",
        name=curve_name,
        transform_type="Mirror",
        center=(center_x, center_y, center_z),
        plane_normal=(plane_normal_x, plane_normal_y, plane_normal_z),
        multiple_objects=multiple_objects,
        group_objects=group_objects,
    )


def create_horn_segment(project_path: str, segment_id: int, bottom_radius: float, top_radius: float, z_min: float, z_max: float) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    d = 5
    outer = define_cone(project_path, name=str(segment_id), component="component1", material="PEC",
                        bottom_radius=bottom_radius + d, top_radius=top_radius + d, axis="z",
                        z_min=z_min, z_max=z_max, x_center=0, y_center=0)
    if outer.get("status") == "error":
        return outer
    inner = define_cone(project_path, name=f"solid{segment_id}", component="component1", material="PEC",
                        bottom_radius=bottom_radius, top_radius=top_radius, axis="z",
                        z_min=z_min, z_max=z_max, x_center=0, y_center=0)
    if inner.get("status") == "error":
        return inner
    remove = boolean_subtract(project_path, target=f"component1:{segment_id}", tool=f"component1:solid{segment_id}")
    if remove.get("status") == "error":
        return remove
    return {"status": "success", "project_path": normalized_project, "message": f"Horn segment {segment_id} created"}


def _profile_brick(project_path, project, component, name, material, xmin, xmax, ymin, ymax, z):
    vba = f'With Brick\n    .Name "{name}"\n    .Component "{component}"\n    .Material "{material}"\n    .Xrange "{xmin}", "{xmax}"\n    .Yrange "{ymin}", "{ymax}"\n    .Zrange "{z}", "{z}"\n    .Create\nEnd With'
    return _single_vba(project_path, f"Create:{name}", vba, project=project)


def _pick_face(project_path, project, component, name):
    return _single_vba(project_path, f"Pick:{name}", f'Pick.PickFaceFromId "{component}:{name}", "1"', project=project)


def _do_loft(project_path, project, name, component, material, tangency, minimize_twist):
    twist = "true" if minimize_twist else "false"
    vba = f'With Loft\n    .Reset\n    .Name "{name}"\n    .Component "{component}"\n    .Material "{material}"\n    .Tangency "{tangency}"\n    .Minimizetwist "{twist}"\n    .CreateNew\nEnd With'
    return _single_vba(project_path, f"Loft:{name}", vba, project=project)


def _delete_temp(project_path, project, component, name):
    return _single_vba(project_path, f"Delete:{name}", f'Solid.Delete "{component}:{name}"', project=project)


def create_loft_sweep(
    project_path: str, name: str, component: str, material: str,
    x_min1: float, x_max1: float, y_min1: float, y_max1: float, z1: float,
    x_min2: float, x_max2: float, y_min2: float, y_max2: float, z2: float,
    tangency: int = 0, minimize_twist: bool = True,
) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    p1, p2 = f"_p1_{name}", f"_p2_{name}"
    
    steps = [
        lambda: _profile_brick(normalized_project, project, component, p1, material, x_min1, x_max1, y_min1, y_max1, z1),
        lambda: _profile_brick(normalized_project, project, component, p2, material, x_min2, x_max2, y_min2, y_max2, z2),
        lambda: _pick_face(normalized_project, project, component, p2),
        lambda: _pick_face(normalized_project, project, component, p1),
        lambda: _do_loft(normalized_project, project, name, component, material, tangency, minimize_twist),
        lambda: _delete_temp(normalized_project, project, component, p1),
        lambda: _delete_temp(normalized_project, project, component, p2),
    ]
    for step in steps:
        res = step()
        if res.get("status") == "error":
            return res
            
    return {"status": "success", "project_path": normalized_project, "message": f"Loft sweep {name} created"}


def create_hollow_sweep(
    project_path: str, name: str, component: str, material: str,
    x_min1: float, x_max1: float, y_min1: float, y_max1: float, z1: float,
    x_min2: float, x_max2: float, y_min2: float, y_max2: float, z2: float,
    wall_thickness: float = 2.0, tangency: int = 0, minimize_twist: bool = True,
) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    ix1, ix2 = x_min1 + wall_thickness, x_max1 - wall_thickness
    iy1, iy2 = y_min1 + wall_thickness, y_max1 - wall_thickness
    jx1, jx2 = x_min2 + wall_thickness, x_max2 - wall_thickness
    jy1, jy2 = y_min2 + wall_thickness, y_max2 - wall_thickness
    op1, op2, ip1, ip2 = f"_op1_{name}", f"_op2_{name}", f"_ip1_{name}", f"_ip2_{name}"
    ol, il = f"_ol_{name}", f"_il_{name}"
    
    steps = [
        lambda: _profile_brick(normalized_project, project, component, op1, material, x_min1, x_max1, y_min1, y_max1, z1),
        lambda: _profile_brick(normalized_project, project, component, op2, material, x_min2, x_max2, y_min2, y_max2, z2),
        lambda: _profile_brick(normalized_project, project, component, ip1, material, ix1, ix2, iy1, iy2, z1),
        lambda: _profile_brick(normalized_project, project, component, ip2, material, jx1, jx2, jy1, jy2, z2),
        lambda: _pick_face(normalized_project, project, component, op2),
        lambda: _pick_face(normalized_project, project, component, op1),
        lambda: _do_loft(normalized_project, project, ol, component, material, tangency, minimize_twist),
        lambda: _pick_face(normalized_project, project, component, ip2),
        lambda: _pick_face(normalized_project, project, component, ip1),
        lambda: _do_loft(normalized_project, project, il, component, material, tangency, minimize_twist),
        lambda: _single_vba(normalized_project, f"Bool:{name}", f'Solid.Subtract "{component}:{ol}", "{component}:{il}"', project=project)
    ]
    for t in [op1, op2, ip1, ip2]:
        steps.append(lambda t=t: _delete_temp(normalized_project, project, component, t))
        
    for step in steps:
        res = step()
        if res.get("status") == "error":
            return res
            
    return {"status": "success", "project_path": normalized_project, "message": f"Hollow sweep {name} created"}


def add_to_history(project_path: str, command: str, history_name: str = "") -> dict[str, Any]:
    name = history_name or f"VBA: {command[:40]}"
    return _single_vba(project_path, name, command)


def set_boundary_per_face(
    project_path: str,
    xmin: str,
    xmax: str,
    ymin: str,
    ymax: str,
    zmin: str,
    zmax: str,
    periodic_angle: float = 0,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "Define Boundary Per Face",
        boundary_per_face_vba,
        faces=(xmin, xmax, ymin, ymax, zmin, zmax),
        periodic_angle=periodic_angle,
    )


def translate_shape(
    project_path: str,
    name: str,
    vector: tuple[float, float, float],
    multiple_objects: bool = True,
    repetitions: int = 1,
    destination: str = "",
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        f"Translate: {name}",
        translate_vba,
        name=name,
        vector=vector,
        multiple_objects=multiple_objects,
        repetitions=repetitions,
        destination=destination,
    )


def activate_working_coordinate_system(
    project_path: str,
    name: str,
    origin: tuple[float, float, float],
    normal: tuple[float, float, float],
    uvector: tuple[float, float, float],
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        f"Activate WCS: {name}",
        activate_wcs_vba,
        name=name,
        origin=origin,
        normal=normal,
        uvector=uvector,
    )


def deactivate_working_coordinate_system(project_path: str) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "Deactivate WCS",
        deactivate_wcs_vba,
    )


def define_arc_curve(
    project_path: str,
    name: str,
    curve: str,
    center: tuple[float, float, float],
    radius: float,
    start_angle: float,
    end_angle: float,
    segments: int = 0,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        f"Define Arc: {name}",
        arc_vba,
        name=name,
        curve=curve,
        center=center,
        radius=radius,
        start_angle=start_angle,
        end_angle=end_angle,
        segments=segments,
    )


def define_polygon_solid(
    project_path: str,
    name: str,
    component: str,
    material: str,
    vertices: list[tuple[float, float]],
    z_range: tuple[float, float],
) -> dict[str, Any]:
    try:
        profile = detect_compatibility_profile()
        generated = polygon_solid_vba(
            name=name,
            component=component,
            material=material,
            vertices=vertices,
            z_range=z_range,
            profile=profile,
        )
    except (CSTRuntimeError, ValueError) as exc:
        if isinstance(exc, CSTRuntimeError):
            return exc.to_response(project_path=_abs_project_path(project_path))
        return error_response("invalid_arguments", str(exc), project_path=_abs_project_path(project_path))
    material_result = _define_material(project_path, material)
    if material_result.get("status") == "error":
        return material_result
    result = _add_vba_history(project_path, f"Define Polygon: {name}", list(generated.lines))
    if result.get("status") != "error":
        result["compatibility"] = generated.metadata(profile)
    return result


def define_waveguide_port(
    project_path: str,
    port_number: int,
    face: str,
    width: float | None = None,
    height: float | None = None,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        f"Define Waveguide Port {port_number}",
        waveguide_port_vba,
        port_number=port_number,
        face=face,
        width=width,
        height=height,
    )


def define_floquet_port(
    project_path: str,
    zmin_modes: int,
    zmax_modes: int,
    zmin_reference_distance: float,
    zmax_reference_distance: float,
    polarization_type: str,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "Define Floquet Port",
        floquet_port_vba,
        zmin_modes=zmin_modes,
        zmax_modes=zmax_modes,
        zmin_reference_distance=zmin_reference_distance,
        zmax_reference_distance=zmax_reference_distance,
        polarization_type=polarization_type,
    )


def pick_face(project_path: str, component: str, name: str, face_id: str) -> dict[str, Any]:
    full = f"{component}:{name}"
    return _single_vba(project_path, f"Pick face: {full}", f'Pick.PickFaceFromId "{full}", "{face_id}"')


def define_loft(project_path: str, name: str, component: str, material: str, tangency: int = 0, minimize_twist: bool = True) -> dict[str, Any]:
    mat_result = _define_material(project_path, material)
    if mat_result.get("status") == "error":
        return mat_result
    twist = "true" if minimize_twist else "false"
    return _add_vba_history(project_path, f"Define Loft:{name}", [
        "With Loft",
        "    .Reset",
        f'    .Name "{name}"',
        f'    .Component "{component}"',
        f'    .Material "{material}"',
        f'    .Tangency "{tangency}"',
        f'    .Minimizetwist "{twist}"',
        "    .CreateNew",
        "End With",
    ])


def _ascii_export(project_path: str, tree_path: str, file_path: str, history_name: str) -> dict[str, Any]:
    vba = f'SelectTreeItem "{tree_path}"\nASCIIExport.Reset\nASCIIExport.FileName "{file_path}"\nASCIIExport.Execute'
    return _single_vba(project_path, history_name, vba)


def export_e_field(project_path: str, frequency: str, file_path: str) -> dict[str, Any]:
    tree = f"2D/3D Results\\E-Field\\e-field (f={frequency}) [pw]"
    fpath = f"{file_path}\\E-field-{frequency}GHz.txt"
    return _ascii_export(project_path, tree, fpath, "ExportEField")


def export_surface_current(project_path: str, frequency: str, file_path: str) -> dict[str, Any]:
    tree = f"2D/3D Results\\Surface Current\\surface current (f={frequency}) [pw]"
    fpath = f"{file_path}\\Surface-Current-{frequency}GHz.txt"
    return _ascii_export(project_path, tree, fpath, "ExportSurfaceCurrent")


def export_voltage(project_path: str, voltage_index: str, file_path: str) -> dict[str, Any]:
    tree = f"1D Results\\Voltage Monitors\\voltage{voltage_index} [pw]"
    fpath = f"{file_path}\\voltage-{voltage_index}.txt"
    return _ascii_export(project_path, tree, fpath, f"ExportVoltage{voltage_index}")


def capture_3d_view(
    project_path: str = "",
    output_dir: str = "",
    filename_prefix: str = "view",
    view_type: str = "preset",
    preset_name: str = "Isometric",
    azimuth: float = 45.0,
    elevation: float = 30.0,
    zoom: float = 1.0,
    return_image_data: bool = False,
) -> dict[str, Any]:
    """Capture 3D view of CST model as PNG + JSON metadata.
    
    Args:
        project_path: Path to .cst file
        output_dir: Output directory (default: <project_dir>/exports/screenshots/)
        filename_prefix: Filename prefix (default: "view")
        view_type: "custom" or "preset"
        preset_name: Preset view name (Front/Back/Top/Bottom/Left/Right/Isometric)
        azimuth: Azimuth angle in degrees (0=+X, 90=+Y, CCW positive)
        elevation: Elevation angle in degrees (0=horizontal, 90=+Z top view)
        zoom: Zoom scale (1.0=default, 0.5=2x closer, 2.0=2x farther)
        return_image_data: If True, include base64-encoded image data in response
    
    Returns:
        dict with status, image_path, metadata_path, view_params, and optionally image_data_base64
    """
    import json
    import base64
    from datetime import datetime
    from .session import open_project, close_project, get_attached_project
    
    if not project_path:
        return error_response("project_path_required", "project_path is required")

    if zoom <= 0:
        return error_response("invalid_zoom", f"zoom must be > 0, got {zoom}")

    valid_presets = {"Front", "Back", "Top", "Bottom", "Left", "Right", "Isometric"}
    if preset_name not in valid_presets:
        return error_response("invalid_preset_name", f"preset_name must be one of {sorted(valid_presets)}")

    if view_type not in {"custom", "preset"}:
        return error_response("invalid_view_type", f"view_type must be 'custom' or 'preset'")

    p = Path(project_path)
    if not p.exists():
        return error_response("project_not_found", f"Project not found: {p}")

    # Resolve project path first
    p = p.resolve()
    
    # Setup output directory
    if output_dir:
        out_dir = Path(output_dir).resolve()
    else:
        out_dir = p.parent / "exports" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp and filenames
    ts = datetime.now()
    ts_str = ts.strftime("%Y%m%d_%H%M%S")
    png_path = out_dir / f"{filename_prefix}_{ts_str}.png"
    json_path = out_dir / f"{filename_prefix}_{ts_str}.json"
    
    # Open project and capture view
    try:
        open_project(str(p))
        prj = get_attached_project(str(p))
        
        # Set view based on type
        if view_type == "preset":
            _set_preset_view(prj, preset_name)
        else:
            _set_custom_view(prj, azimuth, elevation, zoom)
        
        # Export image
        _export_image(prj, str(png_path))
        
        # Write metadata JSON
        metadata = {
            "project_path": str(p.resolve()),
            "timestamp": ts.isoformat(timespec="seconds"),
            "view_type": view_type,
            "view_params": {
                "azimuth": azimuth if view_type == "custom" else None,
                "elevation": elevation if view_type == "custom" else None,
                "zoom": zoom,
                "preset_name": preset_name if view_type == "preset" else None
            },
            "image_path": str(png_path.resolve()),
            "metadata_path": str(json_path.resolve()),
            "image_size": {"width": 1920, "height": 1080},
            "status": "success"
        }
        json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        
        close_project(str(p), save=False, kill_processes=True)
        
        result = {
            "status": "success",
            "image_path": str(png_path.resolve()),
            "metadata_path": str(json_path.resolve()),
            "view_type": view_type,
            "view_params": {
                "azimuth": azimuth if view_type == "custom" else None,
                "elevation": elevation if view_type == "custom" else None,
                "zoom": zoom,
                "preset_name": preset_name if view_type == "preset" else None
            },
            "tool": "capture-3d-view",
            "adapter": "cst_runtime_cli"
        }
        
        # Optionally include base64-encoded image data for agent analysis
        if return_image_data:
            with open(png_path, "rb") as f:
                image_bytes = f.read()
            result["image_data_base64"] = base64.b64encode(image_bytes).decode("ascii")
        
        return result
        
    except Exception as e:
        return error_response("export_failed", f"Failed to capture 3D view: {e}")


def _set_preset_view(prj, preset_name: str) -> None:
    """Set camera to preset view using CST COM API RestoreView()."""
    # CST has predefined view names that can be restored
    # Verified working: Front, Back, Left, Right, Top, Bottom, Perspective
    # Note: "Isometric" is NOT a valid CST view name - use "Perspective" instead
    cst_view_name = preset_name
    if preset_name == "Isometric":
        cst_view_name = "Perspective"  # Closest equivalent in CST
    prj.modeler.Plot.RestoreView(cst_view_name)
    
    # Zoom to fit the model in view
    prj.modeler.Plot.ZoomToStructure()


def _set_custom_view(prj, azimuth: float, elevation: float, zoom: float) -> None:
    """Set camera to custom azimuth/elevation/zoom.
    
    Note: CST COM API does not directly support custom view angles.
    This is a placeholder for future implementation.
    Current behavior: uses current view without modification.
    """
    # TODO: Implement custom view control when CST API is available
    # Plot.Rotate() requires specific direction constants, not angles
    pass


def _export_image(prj, png_path: str) -> None:
    """Export current 3D view to PNG file."""
    # Verified working: prj.modeler.Plot.ExportImage(path, width, height)
    prj.modeler.Plot.ExportImage(png_path, 1920, 1080)
