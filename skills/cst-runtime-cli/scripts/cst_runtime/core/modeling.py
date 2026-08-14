from __future__ import annotations

import difflib
import math
import uuid
from pathlib import Path
from typing import Any

from . import buffer, gateway
from .error_gateway import submit_vba_history
from .errors import CSTRuntimeError, error_response, success_response
from .compatibility import (
    detect_compatibility_profile,
    get_result_metadata,
    result_item_exists,
)
from .compatibility.execution import vba_string
from .compatibility.modeling import (
    CST_2022_SOLVER_TYPES,
    analytical_curve_vba,
    background_vba,
    cone_vba,
    cylinder_vba,
    change_solver_type_vba,
    extrude_curve_vba,
    loft_vba,
    mesh_vba,
    monitor_vba,
    plot_export_vba,
    postprocess_activation_vba,
    polygon3d_vba,
    port_vba,
    rectangle_vba,
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


def _run_separate_cleanup(
    project_path: str,
    result: dict[str, Any],
    history_name: str,
    vba_line: str,
    *,
    target: str,
) -> None:
    """主体成功后单独清理；清理失败只能降级为警告。"""
    if result.get("status") == "error":
        return
    if result.get("submission") == "buffered":
        result["cleanup"] = {
            "status": "skipped",
            "target": target,
            "reason": "批处理尚未执行，不能提前确认主体成功并安排独立清理",
        }
        return

    cleanup_result = _single_vba(project_path, history_name, vba_line)
    if cleanup_result.get("status") == "error":
        result["cleanup"] = {
            "status": "warning",
            "target": target,
            "message": "主体操作成功，但后续临时对象清理失败",
            "result": cleanup_result,
        }
        return
    result["cleanup"] = {"status": "success", "target": target}


def begin_batch(project_path: str, summary: str = "Batch Execution") -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    try:
        buffer.begin_batch(normalized_project, summary=summary)
        return success_response(
            submission="buffered",
            execution="not_run",
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


def _material_mtd_path(material_name: str) -> Path:
    """返回当前 Skill 自带材料库中的 MTD 文件路径。"""
    skill_root = Path(__file__).resolve().parents[3]
    return skill_root / "references" / "Materials" / f"{material_name}.mtd"


def _material_vba_lines(material_name: str, mtd_content: str) -> list[str]:
    """从 MTD 的 Definition 节生成完整的 CST Material VBA 块。"""
    definition_lines: list[str] = []
    in_definition = False
    for raw_line in mtd_content.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_definition = stripped.casefold() == "[definition]"
            continue
        if in_definition and stripped:
            if not stripped.startswith("."):
                raise ValueError(
                    "MTD Definition 节包含不受支持的 VBA 行：" + stripped
                )
            definition_lines.append(stripped)

    if not definition_lines:
        raise ValueError("MTD 文件缺少有效的 [Definition] 节")
    if not any(line.casefold() == ".create" for line in definition_lines):
        raise ValueError("MTD Definition 节缺少 .Create")

    escaped_name = material_name.replace('"', '""')
    return [
        "With Material",
        "    .Reset",
        f'    .Name "{escaped_name}"',
        *(f"    {line}" for line in definition_lines),
        "End With",
    ]


def define_material_from_mtd(project_path: str, material_name: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    mtd_path = _material_mtd_path(material_name)
    if not mtd_path.exists():
        return error_response(
            "material_mtd_not_found",
            f"Material MTD file not found: {mtd_path}",
            project_path=normalized_project,
        )
    try:
        mtd_content = mtd_path.read_text(encoding="utf-8")
        vba_lines = _material_vba_lines(material_name, mtd_content)
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
        f'    .Xrange "{x_min}", "{x_max}"',
        f'    .Yrange "{y_min}", "{y_max}"',
        f'    .Zrange "{z_min}", "{z_max}"',
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
    axis_min: float | str | None = None,
    axis_max: float | str | None = None,
    range_min: float | str | None = None,
    range_max: float | str | None = None,
    z_min: float | str | None = None,
    z_max: float | str | None = None,
    center1: float | str | None = None,
    center2: float | str | None = None,
    x_center: float | str | None = None,
    y_center: float | str | None = None,
    segments: int = 0,
) -> dict[str, Any]:
    if axis_min is None:
        axis_min = range_min if range_min is not None else z_min
    if axis_max is None:
        axis_max = range_max if range_max is not None else z_max
    if center1 is None:
        center1 = x_center if x_center is not None else 0.0
    if center2 is None:
        center2 = y_center if y_center is not None else 0.0
    if axis_min is None or axis_max is None:
        return error_response(
            "missing_argument",
            "axis_min and axis_max are required",
        )

    return _submit_versioned_vba(
        project_path,
        f"Define Cylinder:{name}",
        cylinder_vba,
        name=name,
        component=component,
        material=material,
        outer_radius=outer_radius,
        inner_radius=inner_radius,
        axis=axis,
        range_min=axis_min,
        range_max=axis_max,
        center1=center1,
        center2=center2,
        segments=segments,
    )


def define_cone(
    project_path: str,
    name: str,
    component: str,
    material: str,
    bottom_radius: float | str,
    top_radius: float | str,
    axis: str,
    axis_min: float | str | None = None,
    axis_max: float | str | None = None,
    range_min: float | str | None = None,
    range_max: float | str | None = None,
    z_min: float | str | None = None,
    z_max: float | str | None = None,
    center1: float | str | None = None,
    center2: float | str | None = None,
    x_center: float | str | None = None,
    y_center: float | str | None = None,
    segments: int = 0,
) -> dict[str, Any]:
    if axis_min is None:
        axis_min = range_min if range_min is not None else z_min
    if axis_max is None:
        axis_max = range_max if range_max is not None else z_max
    if center1 is None:
        center1 = x_center if x_center is not None else 0.0
    if center2 is None:
        center2 = y_center if y_center is not None else 0.0
    if axis_min is None or axis_max is None:
        return error_response(
            "missing_argument",
            "axis_min and axis_max are required",
        )

    return _submit_versioned_vba(
        project_path,
        f"Define Cone:{name}",
        cone_vba,
        name=name,
        component=component,
        material=material,
        bottom_radius=bottom_radius,
        top_radius=top_radius,
        axis=axis,
        range_min=axis_min,
        range_max=axis_max,
        center1=center1,
        center2=center2,
        segments=segments,
    )


def define_rectangle(
    project_path: str,
    name: str,
    curve: str,
    x_min: float | str,
    x_max: float | str,
    y_min: float | str,
    y_max: float | str,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        f"Define Rectangle:{name}",
        rectangle_vba,
        name=name,
        curve=curve,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
    )


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
    normalized_component = str(component or "").strip()
    normalized_name = str(name or "").strip()
    if not normalized_name:
        return error_response(
            "invalid_arguments",
            "实体名称不能为空",
            phase="validation",
            project_path=_abs_project_path(project_path),
        )
    if normalized_component:
        if ":" in normalized_name:
            return error_response(
                "invalid_arguments",
                "component 非空时，name 必须是未包含组件前缀的裸实体名",
                phase="validation",
                project_path=_abs_project_path(project_path),
            )
        full_name = f"{normalized_component}:{normalized_name}"
    else:
        parts = normalized_name.split(":")
        if len(parts) != 2 or not all(part.strip() for part in parts):
            return error_response(
                "invalid_arguments",
                "component 为空时，name 必须是完整的 component:name",
                phase="validation",
                project_path=_abs_project_path(project_path),
            )
        full_name = f"{parts[0].strip()}:{parts[1].strip()}"
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
    return _submit_versioned_vba(
        project_path,
        f"change solver type to {solver_type}",
        change_solver_type_vba,
        solver_type=solver_type,
    )


_BACKGROUND_MANUAL_NOTE = (
    "CST 2022 手册（VBA Background Object）只定义写入方法"
    "（Reset/Type/Epsilon/Mu/ElConductivity/XminSpace…ZmaxSpace/"
    "ThermalType/ThermalConductivity/ApplyInAllDirections），"
    "未提供任何读取接口；运行时只能返回本会话内 define-background "
    "实际写入并跟踪的状态，不能读回 GUI 中的修改。"
)


def define_background(
    project_path: str,
    background_type: str = "Normal",
    epsilon: float = 1.0,
    mu: float = 1.0,
) -> dict[str, Any]:
    """按 CST 2022 手册写入背景类型与材料参数，并登记运行时跟踪状态。

    手册的 Background 对象只提供写入方法，因此无法从 CST 读回实际生效值；
    本工具在 execution=reported_ok 时把请求值登记为运行时跟踪状态（供
    get-background 返回），并在响应中返回 requested 值与远场监视器兼容性
    判定。远场监视器要求 Normal 且 ε=1、μ=1（等价 Vacuum）。
    """
    normalized_project = _abs_project_path(project_path)
    normalized_type = str(background_type or "Normal").strip()
    if normalized_type.casefold() not in {"normal", "pec"}:
        return error_response(
            "validation_error",
            'background_type 只允许 "Normal" 或 "PEC"',
            phase="validation",
            project_path=normalized_project,
        )
    epsilon_value = float(epsilon)
    mu_value = float(mu)
    result = _submit_versioned_vba(
        project_path,
        "define background",
        background_vba,
        background_type=normalized_type,
        epsilon=epsilon_value,
        mu=mu_value,
    )
    if result.get("status") == "error":
        return result
    requested = {
        "background_type": normalized_type,
        "epsilon": epsilon_value,
        "mu": mu_value,
    }
    farfield_compatible = (
        normalized_type.casefold() == "normal"
        and epsilon_value == 1.0
        and mu_value == 1.0
    )
    if result.get("execution") == "reported_ok":
        gateway.mark_background_state(
            normalized_project,
            background_type=normalized_type,
            epsilon=epsilon_value,
            mu=mu_value,
        )
        result["background_state"] = "tracked"
    else:
        # 批处理尚未执行，登记会在实际执行路径之外丢失，不提前声明已生效
        result["background_state"] = "not_tracked"
    result["requested"] = requested
    result["farfield_compatible"] = farfield_compatible
    result["farfield_basis"] = "requested"
    result["readback"] = {
        "status": "unsupported_by_manual",
        "manual_note": _BACKGROUND_MANUAL_NOTE,
    }
    if not farfield_compatible:
        result["warning"] = (
            "请求的背景不满足远场监视器要求（Farfield monitors are not "
            "supported with pec, dispersive, lossy or surface impedance as "
            "background material）；如需远场结果请恢复 Normal/Vacuum 背景"
        )
    return result


def get_background(project_path: str) -> dict[str, Any]:
    """返回本会话运行时跟踪的背景状态。

    CST 2022 手册未给 Background 对象定义任何读取接口（对比 Boundary
    对象手册中的 GetXmin/GetXmax 等 Get* 方法），因此本工具绝不调用
    未文档化的属性读取；唯一数据来源是本会话内 define-background 实际
    写入后登记的状态。没有跟踪状态时返回 error（background_state_unknown），
    调用方不应把该错误当作 CST 故障，而应使用 define-background 显式
    设置背景，或依赖 run-experiment/wait-simulation 回传的求解日志错误。
    """
    normalized_project = _abs_project_path(project_path)
    tracked = gateway.get_background_state(normalized_project)
    try:
        compatibility = detect_compatibility_profile().metadata()
    except Exception:
        compatibility = {}
    if tracked is None:
        return error_response(
            "background_state_unknown",
            "未取得背景状态：CST 2022 手册未提供背景读取接口，"
            "且本会话尚未通过 define-background 写入背景",
            project_path=normalized_project,
            manual_note=_BACKGROUND_MANUAL_NOTE,
            next_action=(
                "先调用 define-background 显式设置背景（响应返回 requested "
                "值与 farfield_compatible）；或依赖 run-experiment/"
                "wait-simulation 回传的求解日志错误判断远场-背景不兼容"
            ),
            compatibility=compatibility,
        )
    background_type = str(tracked["background_type"])
    epsilon = float(tracked["epsilon"])
    mu = float(tracked["mu"])
    return success_response(
        project_path=normalized_project,
        background_type=background_type,
        epsilon=epsilon,
        mu=mu,
        el_conductivity=None,
        spaces=None,
        apply_in_all_directions=None,
        farfield_compatible=(
            background_type.casefold() == "normal"
            and epsilon == 1.0
            and mu == 1.0
        ),
        source="runtime_tracked",
        manual_note=_BACKGROUND_MANUAL_NOTE,
        compatibility=compatibility,
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


def define_farfield_monitor(
    project_path: str,
    name: str,
    frequencies: list[float],
    enable_nearfield: bool = True,
    subvolume: list[float] | None = None,
) -> dict[str, Any]:
    """为每个频率创建独立的 CST 2022 单频远场监视器。"""
    base_name = str(name).strip()
    if not base_name:
        return error_response("invalid_monitor_name", "监视器名称不能为空")
    try:
        values = [float(value) for value in frequencies]
    except (TypeError, ValueError):
        return error_response("invalid_monitor_frequency", "frequencies 必须是有限数值数组")
    if not values or any(not math.isfinite(value) or value <= 0 for value in values):
        return error_response("invalid_monitor_frequency", "frequencies 必须包含至少一个大于零的有限频率")
    if len(set(values)) != len(values):
        return error_response("duplicate_monitor_frequency", "frequencies 不得重复")
    bounds: tuple[float, float, float, float, float, float] | None = None
    if subvolume is not None:
        if len(subvolume) != 6:
            return error_response("invalid_subvolume", "subvolume 必须包含六个坐标")
        raw_bounds = tuple(float(value) for value in subvolume)
        if not (raw_bounds[0] < raw_bounds[1] and raw_bounds[2] < raw_bounds[3] and raw_bounds[4] < raw_bounds[5]):
            return error_response("invalid_subvolume", "subvolume 每一轴的最小值必须小于最大值")
        bounds = raw_bounds

    requested = [
        {
            "name": base_name if len(values) == 1 else f"{base_name} (f={frequency:g})",
            "frequency": frequency,
        }
        for frequency in values
    ]
    created: list[dict[str, Any]] = []
    for monitor in requested:
        result = _submit_versioned_vba(
            project_path,
            f"Define Farfield Monitor:{monitor['name']}",
            monitor_vba,
            field_type="Farfield",
            start=monitor["frequency"],
            end=monitor["frequency"],
            samples=1,
            name=monitor["name"],
            subvolume=bounds,
            use_subvolume=bounds is not None,
            enable_nearfield=enable_nearfield,
        )
        if result.get("status") == "error":
            result["created_before_failure"] = created
            return result
        created.append(monitor)
    result.update(
        created_count=len(created),
        monitors=created,
        enable_nearfield=bool(enable_nearfield),
        subvolume=list(bounds) if bounds else None,
    )
    return result


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
    temperature: str = "Celsius",
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
    profile = detect_compatibility_profile()
    if profile.is_2022:
        monitor_name = f"e-field (f={start_freq})"
    else:
        monitor_name = f"e-field (f={start_freq}-{end_freq})"
    return _submit_versioned_vba(
        project_path,
        "Set Efield Monitor",
        monitor_vba,
        field_type="Efield",
        start=start_freq,
        end=end_freq,
        step=step,
        name=monitor_name,
        dimension=dimension,
        # 保留旧参数签名，但禁用子体积时不把无效坐标提交给 CST。
        subvolume=None,
        use_subvolume=False,
    )


def set_field_monitor(project_path: str, field_type: str, start_frequency: str, end_frequency: str, num_samples: str) -> dict[str, Any]:
    normalized_field = str(field_type).strip().casefold()
    if normalized_field not in {"e", "h"}:
        return error_response(
            "validation_error",
            'field_type 只允许 "E" 或 "H"',
            phase="validation",
            project_path=_abs_project_path(project_path),
        )
    field_name = "Efield" if normalized_field == "e" else "Hfield"
    profile = detect_compatibility_profile()
    if profile.is_2022:
        monitor_name = f"{normalized_field}-field (f={start_frequency})"
    else:
        monitor_name = f"{normalized_field}-field (f={start_frequency}-{end_frequency})"
    return _submit_versioned_vba(
        project_path,
        f"Set{normalized_field.upper()}Monitor",
        monitor_vba,
        field_type=field_name,
        start=start_frequency,
        end=end_frequency,
        samples=num_samples,
        name=monitor_name,
    )


def set_probe(project_path: str, field_type: str, x_pos: str, y_pos: str, z_pos: str) -> dict[str, Any]:
    normalized_field = str(field_type).strip().casefold()
    if normalized_field not in {"e", "h"}:
        return error_response(
            "validation_error",
            'field_type 只允许 "E" 或 "H"',
            phase="validation",
            project_path=_abs_project_path(project_path),
        )
    probe_field = "efield" if normalized_field == "e" else "hfield"
    vba = f'Probe.Reset\nProbe.AutoLabel 1\nProbe.Field "{probe_field}"\nProbe.Orientation "All"\nProbe.Xpos "{x_pos}"\nProbe.Ypos "{y_pos}"\nProbe.Zpos "{z_pos}"\nProbe.Create'
    return _single_vba(project_path, f"Set{normalized_field.upper()}Probe", vba)


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
    result = _submit_versioned_vba(
        project_path,
        "Set Background Space",
        background_vba,
        # 显式 Normal：CST 2022 的 .Reset 会把 Type 重置为默认 "pec"，
        # 只设空间而不设类型会留下远场监视器不兼容的背景。
        background_type="Normal",
        spaces=(x_min_space, x_max_space, y_min_space, y_max_space, z_min_space, z_max_space),
    )
    if result.get("status") != "error" and result.get("execution") == "reported_ok":
        # 本工具写入的背景为 Normal + 默认 ε/μ（等价 Vacuum），
        # 登记为运行时跟踪状态，供 get-background 返回。
        gateway.mark_background_state(
            project_path,
            background_type="Normal",
            epsilon=1.0,
            mu=1.0,
        )
    return result


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
    return _submit_versioned_vba(
        project_path,
        f"activate post process: {operation}",
        postprocess_activation_vba,
        operation=operation,
        enable=enable,
    )


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
    return _submit_versioned_vba(
        project_path,
        f"Define AnalyticalCurve: {name}",
        analytical_curve_vba,
        name=name,
        curve=curve,
        law_x=law_x,
        law_y=law_y,
        law_z=law_z,
        param_start=param_start,
        param_end=param_end,
    )


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
        if "delete_profile" in generated.not_applied:
            result["profile_retention"] = {
                "status": "not_applied",
                "requested_delete_profile": False,
                "reason": "CST 2022 ExtrudeCurve.Create 会自动消费输入曲线项，无法保留该轮廓",
            }
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
    vba = f'With Brick\n    .Reset\n    .Name "{name}"\n    .Component "{component}"\n    .Material "{material}"\n    .Xrange "{xmin}", "{xmax}"\n    .Yrange "{ymin}", "{ymax}"\n    .Zrange "{z}", "{z}"\n    .Create\nEnd With'
    return _single_vba(project_path, f"Create:{name}", vba, project=project)


def _pick_face(project_path, project, component, name):
    return _single_vba(project_path, f"Pick:{name}", f'Pick.PickFaceFromId "{component}:{name}", "1"', project=project)


def _do_loft(project_path, project, name, component, material, tangency, minimize_twist):
    profile = detect_compatibility_profile()
    generated = loft_vba(
        name=name,
        component=component,
        material=material,
        tangency=tangency,
        minimize_twist=minimize_twist,
        profile=profile,
    )
    result = _add_vba_history(
        project_path,
        f"Loft:{name}",
        list(generated.lines),
        project=project,
    )
    if result.get("status") != "error":
        result["compatibility"] = generated.metadata(profile)
    return result


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
    try:
        profile = detect_compatibility_profile()
        generated = arc_vba(
            name=name,
            curve=curve,
            center=center,
            radius=radius,
            start_angle=start_angle,
            end_angle=end_angle,
            segments=segments,
            profile=profile,
        )
    except (CSTRuntimeError, ValueError) as exc:
        if isinstance(exc, CSTRuntimeError):
            return exc.to_response(project_path=_abs_project_path(project_path))
        return error_response(
            "invalid_arguments",
            str(exc),
            project_path=_abs_project_path(project_path),
        )

    result = _add_vba_history(
        project_path,
        f"Define Arc: {name}",
        list(generated.lines),
    )
    if result.get("status") != "error":
        result["compatibility"] = generated.metadata(profile)
        cleanup_target = generated.not_applied.get("wcs_cleanup")
        if cleanup_target:
            _run_separate_cleanup(
                project_path,
                result,
                f"Cleanup Arc WCS: {name}",
                f'WCS.Delete "{cleanup_target}"',
                target=str(cleanup_target),
            )
    return result


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
    return _submit_versioned_vba(
        project_path,
        f"Define Loft:{name}",
        loft_vba,
        name=name,
        component=component,
        material=material,
        tangency=tangency,
        minimize_twist=minimize_twist,
    )


FIELD_RESULT_TYPES: dict[str, frozenset[str]] = {
    "e_field": frozenset({"Efield2D", "Efield2DTD", "Efield3D", "Efield3DTD", "Efield3D_tet", "Efield3D_srf"}),
    "h_field": frozenset({"Hfield2D", "Hfield2DTD", "Hfield3D", "Hfield3DTD", "Hfield3D_tet", "Hfield3D_srf"}),
    "surface_current": frozenset({"SurfaceCurrent", "SurfaceCurrentTD", "SurfaceCurrent_tet", "SurfaceCurrent_srf"}),
    "power_flow": frozenset({"Pfield2D", "Pfield2DTD", "Pfield3D", "Pfield3DTD", "Pfield3D_tet"}),
    "current_density": frozenset({"Current3D", "Current3DTD", "Current3D_tet"}),
    "power_loss_density": frozenset({"PowerLoss3D", "PowerLoss3DTD", "PowerLoss3D_tet"}),
}


def list_field_results(project_path: str) -> dict[str, Any]:
    """列出实际 2D/3D ResultTree 节点及官方 Result Type。"""
    normalized = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized)
    if project is None:
        return status
    try:
        rows = get_result_metadata(
            project,
            root_path="2D/3D Results",
            filter_type="2D/3D recursive",
        )
        reverse_types = {
            result_type: kind
            for kind, result_types in FIELD_RESULT_TYPES.items()
            for result_type in result_types
        }
        results = [
            {**row, "field_kind": reverse_types.get(row["result_type"])}
            for row in rows
        ]
        return success_response(
            project_path=normalized,
            count=len(results),
            results=results,
        )
    except CSTRuntimeError as exc:
        return exc.to_response(project_path=normalized)
    except Exception as exc:
        return error_response(
            "list_field_results_failed",
            str(exc),
            project_path=normalized,
        )


def _ascii_export(
    project_path: str,
    tree_path: str,
    file_path: str,
    history_name: str,
    *,
    mode: str = "FixedNumber",
    step_x: int | float | None = None,
    step_y: int | float | None = None,
    step_z: int | float | None = None,
    point_file: str = "",
    subvolume: list[float] | None = None,
    file_type: str = "ascii",
    csv_separator: str = ",",
) -> dict[str, Any]:
    mode_values = {"fixednumber": "FixedNumber", "fixedwidth": "FixedWidth"}
    normalized_mode = mode_values.get(mode.strip().casefold())
    if normalized_mode is None:
        return error_response("invalid_ascii_export_mode", "mode 必须是 FixedNumber 或 FixedWidth")
    normalized_file_type = file_type.strip().casefold()
    if normalized_file_type not in {"ascii", "csv"}:
        return error_response("invalid_ascii_export_type", "file_type 必须是 ascii 或 csv")
    if point_file and not Path(point_file).expanduser().is_file():
        return error_response("point_file_not_found", "point_file 不存在", point_file=point_file)
    if subvolume is not None:
        if len(subvolume) != 6:
            return error_response("invalid_subvolume", "subvolume 必须包含 xmin,xmax,ymin,ymax,zmin,zmax")
        values = [float(value) for value in subvolume]
        if not (values[0] < values[1] and values[2] < values[3] and values[4] < values[5]):
            return error_response("invalid_subvolume", "subvolume 每一轴的最小值必须小于最大值")
    else:
        values = []
    escaped_tree_path = vba_string(tree_path)
    output_path = Path(file_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(
        f".{output_path.stem}.{uuid.uuid4().hex}.tmp{output_path.suffix}"
    )
    escaped_file_path = vba_string(str(temporary_path))
    lines = [
        f'If Not SelectTreeItem("{escaped_tree_path}") Then\n'
        f'    ReportError "ASCIIExport: tree item was not selected: {escaped_tree_path}"\n'
        "End If",
        "With ASCIIExport",
        "    .Reset",
        f'    .FileName "{escaped_file_path}"',
        f'    .Mode "{normalized_mode}"',
        f'    .SetfileType "{normalized_file_type}"',
    ]
    for axis, value in (("X", step_x), ("Y", step_y), ("Z", step_z)):
        if value is not None:
            lines.append(f"    .Step{axis} {value}")
    if normalized_file_type == "csv":
        lines.append(f'    .SetCsvSeparator "{vba_string(csv_separator)}"')
    if point_file:
        lines.append(f'    .SetPointFile "{vba_string(str(Path(point_file).expanduser().resolve()))}"')
    if values:
        lines.append("    .SetSubvolume " + ", ".join(str(value) for value in values))
        lines.append('    .UseSubvolume "True"')
    lines.extend(["    .Execute", "End With"])
    vba = "\n".join(lines)
    result = _single_vba(project_path, history_name, vba)
    if result.get("status") == "error":
        temporary_path.unlink(missing_ok=True)
        return result
    if not temporary_path.is_file() or temporary_path.stat().st_size <= 0:
        temporary_path.unlink(missing_ok=True)
        return error_response(
            "export_file_missing",
            "CST 已执行 ASCIIExport，但导出文件不存在或为空",
            project_path=str(Path(project_path).expanduser().resolve()),
            tree_path=tree_path,
            output_file=str(output_path),
        )
    try:
        temporary_path.replace(output_path)
    except OSError as exc:
        temporary_path.unlink(missing_ok=True)
        return error_response(
            "export_file_replace_failed",
            f"导出文件生成成功，但无法替换目标文件: {exc}",
            output_file=str(output_path),
        )
    return {
        **result,
        "output_file": str(output_path),
        "file_size": output_path.stat().st_size,
    }


def export_field_result(
    project_path: str,
    result_path: str,
    file_path: str,
    field_kind: str,
    **sampling: Any,
) -> dict[str, Any]:
    """校验官方 Result Type 后导出精确场结果节点。"""
    listed = list_field_results(project_path)
    if listed.get("status") == "error":
        return listed
    matched = [
        item for item in listed.get("results", [])
        if str(item.get("result_path", "")).casefold() == result_path.casefold()
    ]
    if len(matched) != 1:
        return error_response(
            "field_result_not_found",
            "实际 ResultTree 中没有唯一匹配的场结果节点",
            result_path=result_path,
            candidates=[item.get("result_path") for item in listed.get("results", [])],
        )
    accepted_types = FIELD_RESULT_TYPES.get(field_kind)
    if accepted_types is None or matched[0].get("result_type") not in accepted_types:
        return error_response(
            "field_result_type_mismatch",
            "结果节点的官方 Result Type 与所选物理量不一致",
            result_path=result_path,
            result_type=matched[0].get("result_type"),
            expected_types=sorted(accepted_types or []),
        )
    result = _ascii_export(
        project_path,
        str(matched[0]["result_path"]),
        file_path,
        f"Export {field_kind}",
        **sampling,
    )
    if result.get("status") != "error":
        result.update(field_kind=field_kind, result_type=matched[0]["result_type"])
    return result


def export_voltage_result(project_path: str, result_path: str, file_path: str) -> dict[str, Any]:
    """按实际 0D/1D 电压结果路径导出，不拼接监视器编号。"""
    normalized = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized)
    if project is None:
        return status
    try:
        if not result_item_exists(project, result_path):
            return error_response(
                "voltage_result_not_found",
                "实际 ResultTree 中不存在指定电压结果节点",
                result_path=result_path,
            )
    except CSTRuntimeError as exc:
        return exc.to_response(project_path=normalized, result_path=result_path)
    return _ascii_export(project_path, result_path, file_path, "Export voltage result")


def capture_3d_view(
    project_path: str = "",
    output_dir: str = "",
    filename_prefix: str = "view",
    view_type: str = "preset",
    preset_name: str = "Perspective",
    horizontal_rotation_deg: float | None = None,
    vertical_rotation_deg: float | None = None,
    zoom: float = 1.0,
    return_image_data: bool = False,
    azimuth: float | None = None,
    elevation: float | None = None,
) -> dict[str, Any]:
    """Capture 3D view of CST model as PNG + JSON metadata.
    
    Args:
        project_path: Path to .cst file
        output_dir: Output directory (default: <project_dir>/exports/screenshots/)
        filename_prefix: Filename prefix (default: "view")
        view_type: "custom" or "preset"
        preset_name: CST reserved view name
        horizontal_rotation_deg: Custom view rotation from Front; positive is left
        vertical_rotation_deg: Custom view rotation from Front; positive is up
        zoom: Compatibility field; CST 2022 supports only automatic fit (1.0)
        return_image_data: If True, include base64-encoded image data in response
    
    Returns:
        dict with status, image_path, metadata_path, view_params, and optionally image_data_base64
    """
    import json
    import base64
    from datetime import datetime
    from .session import close_project, get_attached_project, open_project
    
    if not project_path:
        return error_response("project_path_required", "project_path is required")

    if not math.isclose(float(zoom), 1.0, rel_tol=0.0, abs_tol=1e-12):
        return error_response(
            "unsupported_zoom",
            "CST 2022 Plot 仅记录了自动填充结构，不支持数值缩放倍数；zoom 必须为 1.0",
            phase="compatibility",
        )

    horizontal_rotation = (
        float(horizontal_rotation_deg)
        if horizontal_rotation_deg is not None
        else float(azimuth) if azimuth is not None else 45.0
    )
    vertical_rotation = (
        float(vertical_rotation_deg)
        if vertical_rotation_deg is not None
        else float(elevation) if elevation is not None else 30.0
    )
    if not math.isfinite(horizontal_rotation) or not math.isfinite(vertical_rotation):
        return error_response("invalid_rotation", "rotation angles must be finite")

    if view_type not in {"custom", "preset"}:
        return error_response("invalid_view_type", f"view_type must be 'custom' or 'preset'")
    valid_presets = {
        "Front", "Back", "Top", "Bottom", "Left", "Right", "Perspective", "Isometric"
    }
    if view_type == "preset" and preset_name not in valid_presets:
        return error_response("invalid_preset_name", f"preset_name must be one of {sorted(valid_presets)}")

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
    ts_str = ts.strftime("%Y%m%d_%H%M%S_%f")
    png_path = out_dir / f"{filename_prefix}_{ts_str}.png"
    json_path = out_dir / f"{filename_prefix}_{ts_str}.json"
    
    open_result = open_project(str(p))
    if open_result.get("status") == "error":
        return open_result
    opened_here = not bool(open_result.get("already_open"))
    capture_result: dict[str, Any]

    try:
        prj = get_attached_project(str(p))
        if prj is None:
            capture_result = error_response(
                "project_attach_failed",
                "工程打开后没有取得对应的 CST Project 对象",
                project_path=str(p),
            )
        else:
            profile = detect_compatibility_profile()
            generated = plot_export_vba(
                preset_name=preset_name,
                output_path=str(png_path),
                view_type=view_type,
                horizontal_rotation_deg=horizontal_rotation,
                vertical_rotation_deg=vertical_rotation,
                width=1920,
                height=1080,
                profile=profile,
            )
            history_result = _add_vba_history(
                str(p),
                f"Capture 3D View:{preset_name if view_type == 'preset' else 'custom'}",
                list(generated.lines),
                project=prj,
            )
            if history_result.get("status") == "error":
                capture_result = history_result
            elif not png_path.is_file() or png_path.stat().st_size <= 0:
                capture_result = error_response(
                    "export_file_missing",
                    "CST 已完成截图 VBA，但 PNG 文件不存在或为空",
                    project_path=str(p),
                    image_path=str(png_path),
                )
            else:
                metadata = {
                    "project_path": str(p),
                    "timestamp": ts.isoformat(timespec="seconds"),
                    "view_type": view_type,
                    "view_params": {
                        "horizontal_rotation_deg": horizontal_rotation if view_type == "custom" else None,
                        "vertical_rotation_deg": vertical_rotation if view_type == "custom" else None,
                        "preset_name": preset_name if view_type == "preset" else None,
                    },
                    "image_path": str(png_path.resolve()),
                    "metadata_path": str(json_path.resolve()),
                    "image_size": {"width": 1920, "height": 1080},
                    "status": "success",
                }
                json_path.write_text(
                    json.dumps(metadata, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                capture_result = {
                    "status": "success",
                    "image_path": str(png_path.resolve()),
                    "metadata_path": str(json_path.resolve()),
                    "view_type": view_type,
                    "view_params": metadata["view_params"],
                    "compatibility": generated.metadata(profile),
                    "tool": "capture-3d-view",
                    "adapter": "cst_runtime_cli",
                }
                if return_image_data:
                    image_bytes = png_path.read_bytes()
                    capture_result["image_data_base64"] = base64.b64encode(
                        image_bytes
                    ).decode("ascii")
    except CSTRuntimeError as exc:
        capture_result = exc.to_response(project_path=str(p))
    except Exception as exc:
        capture_result = error_response(
            "export_failed",
            f"Failed to capture 3D view: {exc}",
            project_path=str(p),
        )

    if opened_here:
        close_result = close_project(str(p), save=False, kill_processes=False)
        if close_result.get("status") == "error":
            capture_result["cleanup"] = {
                "status": "warning",
                "message": "截图完成后未能关闭本次临时打开的工程",
                "result": close_result,
            }
    return capture_result
