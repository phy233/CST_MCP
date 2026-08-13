from __future__ import annotations

import json
import math
import re
import time
import uuid
from pathlib import Path
from typing import Any

from .errors import UnsupportedFeatureError, error_response
from .identity import attach_expected_project
from .compatibility import result_item_exists as compatibility_result_item_exists


def result_item_exists(project_path: str, treepath: str) -> dict[str, Any]:
    """通过 core 兼容边界查询结果树节点是否存在。"""
    project, status = attach_expected_project(project_path)
    if project is None:
        return status
    try:
        exists = compatibility_result_item_exists(project, treepath)
        return {
            "status": "success",
            "project_path": project_path,
            "treepath": treepath,
            "exists": exists,
            "runtime_module": "cst_runtime.core.results",
        }
    except Exception as exc:
        return error_response(
            "result_tree_query_failed",
            str(exc),
            project_path=project_path,
            treepath=treepath,
            runtime_module="cst_runtime.core.results",
        )
from .utils import serialize_value as _serialize_value
from .compatibility import get_result2d_item, get_colormap_items, list_all_result_items


def _load_project(project_path: str, allow_interactive: bool = False, subproject_treepath: str = "") -> tuple[Any, dict[str, Any]]:
    import cst.results

    fullpath = str(Path(project_path).expanduser().resolve())
    project = cst.results.ProjectFile(fullpath, allow_interactive=allow_interactive)
    active_subproject = subproject_treepath or None
    if active_subproject:
        project = project.load_subproject(active_subproject)
    return project, {
        "fullpath": fullpath,
        "active_subproject": active_subproject,
        "allow_interactive": allow_interactive,
    }


def _get_result_module(project: Any, module_type: str) -> tuple[Any, str]:
    module_key = (module_type or "3d").lower()
    if module_key == "schematic":
        return project.get_schematic(), "schematic"
    return project.get_3d(), "3d"


def _canonical_run_ids(run_ids: Any) -> list[int]:
    """规范化 Run ID；仅在存在其他编号时把 0 视为最新结果别名。"""
    normalized = sorted({int(run_id) for run_id in run_ids})
    if not normalized:
        raise RuntimeError("结果节点没有可用的 Run ID")
    nonzero = [run_id for run_id in normalized if run_id != 0]
    return nonzero or [0]


def _latest_available_run_id(run_ids: Any) -> int:
    """选择最新可用结果；非参数化仿真的唯一真实 ID 可以是 0。"""
    return _canonical_run_ids(run_ids)[-1]


def _resolve_run_id(
    result_module: Any,
    requested_run_id: int,
    *,
    treepath: str = "",
) -> int:
    """解析 run_id=0；它既可能是别名，也可能是非参数化结果的真实 ID。"""
    requested = int(requested_run_id)
    if requested != 0:
        return requested
    if treepath:
        run_ids = result_module.get_run_ids(treepath, skip_nonparametric=False)
    else:
        run_ids = result_module.get_all_run_ids(max_mesh_passes_only=True)
    return _latest_available_run_id(run_ids)


def get_version_info() -> dict[str, Any]:
    try:
        import cst.results

        return {
            "status": "success",
            "version_info": _serialize_value(cst.results.get_version_info()),
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "get_version_info_failed",
            str(exc),
            runtime_module="cst_runtime.results",
        )


def open_project(project_path: str, allow_interactive: bool = False, subproject_treepath: str = "") -> dict[str, Any]:
    try:
        path = Path(project_path).expanduser().resolve()
        if not path.is_file():
            return error_response(
                "project_file_missing",
                "project_path does not exist",
                project_path=path.as_posix(),
                runtime_module="cst_runtime.results",
            )
        project, context = _load_project(path.as_posix(), allow_interactive, subproject_treepath)
        return {
            "status": "success",
            "fullpath": context["fullpath"],
            "filename": project.filename,
            "allow_interactive": allow_interactive,
            "active_subproject": context["active_subproject"],
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "open_results_project_failed",
            str(exc),
            project_path=str(project_path),
            runtime_module="cst_runtime.results",
        )


def list_subprojects(project_path: str, allow_interactive: bool = False) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive)
        subprojects = project.list_subprojects()
        return {
            "status": "success",
            "project_path": context["fullpath"],
            "count": len(subprojects),
            "subprojects": _serialize_value(subprojects),
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "list_subprojects_failed",
            str(exc),
            project_path=str(project_path),
            runtime_module="cst_runtime.results",
        )


def list_result_items(
    project_path: str,
    module_type: str = "3d",
    filter_type: str = "0D/1D",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive, subproject_treepath)
        result_module, normalized_module = _get_result_module(project, module_type)
        normalized_filter = (filter_type or "0D/1D").strip()
        if normalized_filter.lower() == "all":
            items = list_all_result_items(result_module)
        else:
            items = [str(item) for item in result_module.get_tree_items(filter=normalized_filter)]
        return {
            "status": "success",
            "project_path": context["fullpath"],
            "module_type": normalized_module,
            "filter_type": normalized_filter,
            "active_subproject": context["active_subproject"],
            "count": len(items),
            "items": items,
            "runtime_module": "cst_runtime.results",
        }
    except UnsupportedFeatureError as exc:
        return exc.to_response(project_path=str(project_path))
    except Exception as exc:
        return error_response(
            "list_result_items_failed",
            str(exc),
            project_path=str(project_path),
            runtime_module="cst_runtime.results",
        )


def list_run_ids(
    project_path: str,
    treepath: str = "",
    module_type: str = "3d",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
    skip_nonparametric: bool = False,
    max_mesh_passes_only: bool = True,
) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive, subproject_treepath)
        result_module, normalized_module = _get_result_module(project, module_type)
        if treepath:
            run_ids = result_module.get_run_ids(treepath, skip_nonparametric=skip_nonparametric)
        else:
            run_ids = result_module.get_all_run_ids(max_mesh_passes_only=max_mesh_passes_only)
        return {
            "status": "success",
            "project_path": context["fullpath"],
            "module_type": normalized_module,
            "active_subproject": context["active_subproject"],
            "treepath": treepath or None,
            "count": len(run_ids),
            "run_ids": _serialize_value(run_ids),
            "runtime_module": "cst_runtime.results",
        }
    except UnsupportedFeatureError as exc:
        return exc.to_response(project_path=str(project_path), treepath=treepath)
    except Exception as exc:
        return error_response(
            "list_run_ids_failed",
            str(exc),
            project_path=str(project_path),
            runtime_module="cst_runtime.results",
        )


def get_parameter_combination(
    project_path: str,
    run_id: int,
    module_type: str = "3d",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive, subproject_treepath)
        result_module, normalized_module = _get_result_module(project, module_type)
        resolved_run_id = _resolve_run_id(result_module, run_id)
        params = result_module.get_parameter_combination(resolved_run_id)
        return {
            "status": "success",
            "project_path": context["fullpath"],
            "requested_run_id": int(run_id),
            "run_id": resolved_run_id,
            "module_type": normalized_module,
            "active_subproject": context["active_subproject"],
            "parameters": _serialize_value(params),
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "get_parameter_combination_failed",
            str(exc),
            project_path=str(project_path),
            run_id=run_id,
            runtime_module="cst_runtime.results",
        )


def get_1d_result(
    project_path: str,
    treepath: str,
    module_type: str = "3d",
    run_id: int = 0,
    load_impedances: bool = True,
    export_path: str = "",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive, subproject_treepath)
        result_module, normalized_module = _get_result_module(project, module_type)
        return _get_1d_result_from_module(
            result_module=result_module,
            context=context,
            normalized_module=normalized_module,
            treepath=treepath,
            run_id=run_id,
            load_impedances=load_impedances,
            export_path=export_path,
        )
    except Exception as exc:
        return error_response(
            "get_1d_result_failed",
            str(exc),
            project_path=str(project_path),
            treepath=treepath,
            run_id=run_id,
            runtime_module="cst_runtime.results",
        )


def list_sparameter_results(project_path: str) -> dict[str, Any]:
    """枚举真实 S 参数节点及各节点可用 Run ID。"""
    try:
        project, context = _load_project(project_path, allow_interactive=False)
        result_module, normalized_module = _get_result_module(project, "3d")
        prefix = "1D Results\\S-Parameters\\"
        items = [
            str(item)
            for item in result_module.get_tree_items(filter="0D/1D")
            if str(item).casefold().startswith(prefix.casefold())
        ]
        results: list[dict[str, Any]] = []
        for treepath in sorted(set(items), key=str.casefold):
            run_ids = result_module.get_run_ids(
                treepath,
                skip_nonparametric=False,
            )
            results.append(
                {
                    "result_path": treepath,
                    "name": treepath.rsplit("\\", 1)[-1],
                    "run_ids": _serialize_value(run_ids),
                }
            )
        return {
            "status": "success",
            "project_path": context["fullpath"],
            "module_type": normalized_module,
            "count": len(results),
            "results": results,
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "list_sparameter_results_failed",
            str(exc),
            project_path=str(project_path),
            runtime_module="cst_runtime.results",
        )


def inspect_1d_result(
    project_path: str,
    treepath: str,
    run_id: int,
    allow_interactive: bool = False,
) -> dict[str, Any]:
    """读取指定 Run 的 0D/1D 数据用于完成性验证，不创建导出文件。"""
    try:
        project, context = _load_project(
            project_path,
            allow_interactive=allow_interactive,
        )
        result_module, normalized_module = _get_result_module(project, "3d")
        result_item = result_module.get_result_item(
            treepath,
            run_id=int(run_id),
            load_impedances=True,
        )
        ydata = result_item.get_ydata()
        if isinstance(ydata, (int, float, complex)):
            xdata = None
            point_count = 1
        else:
            xdata = result_item.get_xdata()
            try:
                point_count = len(ydata)
            except TypeError:
                point_count = int(result_item.length)
        return {
            "status": "success",
            "project_path": context["fullpath"],
            "module_type": normalized_module,
            "result_path": result_item.treepath,
            "run_id": int(result_item.run_id),
            "point_count": int(point_count),
            "xdata": _serialize_value(xdata),
            "ydata": _serialize_value(ydata),
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "inspect_1d_result_failed",
            str(exc),
            project_path=str(project_path),
            treepath=treepath,
            run_id=run_id,
            runtime_module="cst_runtime.results",
        )


def export_touchstone(
    project_path: str,
    output_base_path: str,
    parameter_type: str = "S",
    data_format: str = "MA",
    frequency_range: str = "Full",
    fmin: float | None = None,
    fmax: float | None = None,
    impedance: float = 50.0,
    renormalize: bool = True,
    sample_count: int = 0,
    use_ar_results: bool = False,
) -> dict[str, Any]:
    """使用 CST 2022 TOUCHSTONE Object 导出完整 S/Y/Z 矩阵。"""
    from .compatibility.execution import vba_string
    from .modeling import _single_vba

    export_type = parameter_type.strip().upper()
    value_format = data_format.strip().upper()
    range_mode = frequency_range.strip().title()
    if export_type not in {"S", "Y", "Z"}:
        return error_response("invalid_touchstone_type", "parameter_type 必须是 S、Y 或 Z")
    if value_format not in {"MA", "DB", "RI"}:
        return error_response("invalid_touchstone_format", "data_format 必须是 MA、DB 或 RI")
    if range_mode not in {"Full", "Limited"}:
        return error_response("invalid_touchstone_range", "frequency_range 必须是 Full 或 Limited")
    if range_mode == "Limited" and (fmin is None or fmax is None or float(fmin) >= float(fmax)):
        return error_response("invalid_touchstone_range", "Limited 模式要求 fmin 小于 fmax")
    if isinstance(sample_count, bool) or int(sample_count) < 0:
        return error_response("invalid_touchstone_samples", "sample_count 必须是非负整数")
    if float(impedance) <= 0:
        return error_response("invalid_touchstone_impedance", "impedance 必须大于零")

    requested = Path(output_base_path).expanduser().resolve()
    requested.parent.mkdir(parents=True, exist_ok=True)
    temporary_base = requested.parent / f"cst_touchstone_{uuid.uuid4().hex}"
    lines = [
        "With TOUCHSTONE",
        "    .Reset",
        f'    .FileName "{vba_string(str(temporary_base))}"',
        f"    .Impedance {float(impedance)}",
        f'    .ExportType "{export_type}"',
        f'    .Format "{value_format}"',
        f'    .FrequencyRange "{range_mode}"',
    ]
    if range_mode == "Limited":
        lines.extend([f"    .Fmin {float(fmin)}", f"    .Fmax {float(fmax)}"])
    lines.extend(
        [
            f"    .Renormalize {'True' if renormalize else 'False'}",
            f"    .UseARResults {'True' if use_ar_results else 'False'}",
            f"    .SetNSamples {int(sample_count)}",
            "    .Write",
            "End With",
        ]
    )
    result = _single_vba(project_path, "Export TOUCHSTONE", "\n".join(lines))
    if result.get("status") == "error":
        return result
    generated = [
        path for path in requested.parent.glob(f"{temporary_base.name}*")
        if path.is_file() and path.stat().st_size > 0
    ]
    if len(generated) != 1:
        for path in generated:
            path.unlink(missing_ok=True)
        return error_response(
            "touchstone_file_not_found",
            "CST 已执行 TOUCHSTONE.Write，但没有生成唯一的非空文件",
            output_base_path=str(requested),
        )
    generated_file = generated[0]
    final_path = requested if requested.suffix else requested.with_suffix(generated_file.suffix)
    try:
        generated_file.replace(final_path)
        text = final_path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as exc:
        generated_file.unlink(missing_ok=True)
        return error_response("touchstone_file_finalize_failed", str(exc), output_file=str(final_path))
    lines_text = [line.strip() for line in text.splitlines() if line.strip()]
    has_option_line = any(line.startswith("#") for line in lines_text)
    header_lines = [line for line in lines_text if line.startswith("!")]
    has_data = any(not line.startswith(("!", "#", "[")) for line in lines_text)
    if not has_option_line or not header_lines or not has_data:
        final_path.unlink(missing_ok=True)
        return error_response(
            "touchstone_file_invalid",
            "导出文件缺少 CST 端口/模式注释头、TOUCHSTONE 选项行或网络数据",
            output_file=str(final_path),
        )
    return {
        **result,
        "output_file": str(final_path),
        "file_size": final_path.stat().st_size,
        "parameter_type": export_type,
        "data_format": value_format,
        "header_lines": header_lines,
    }
def _get_1d_result_from_module(
    *,
    result_module: Any,
    context: dict[str, Any],
    normalized_module: str,
    treepath: str,
    run_id: int,
    load_impedances: bool,
    export_path: str = "",
) -> dict[str, Any]:
    """使用已加载的结果模块读取并导出 1D 结果，避免重复打开结果工程。"""
    if export_path:
        export_file = Path(export_path).expanduser()
        if export_file.suffix.lower() != ".json":
            return error_response(
                "invalid_export_extension",
                "get_1d_result export_path only supports .json",
                export_path=str(export_file),
                runtime_module="cst_runtime.results",
            )

    requested_run_id = int(run_id)
    resolved_run_id = _resolve_run_id(
        result_module,
        requested_run_id,
        treepath=treepath,
    )
    result_item = result_module.get_result_item(
        treepath,
        run_id=resolved_run_id,
        load_impedances=load_impedances,
    )
    ydata = result_item.get_ydata()
    if isinstance(ydata, (int, float, complex)):
        # CST 2022 手册明确说明 0D 结果的 ydata 是单个标量。
        xdata = None
    else:
        xdata = result_item.get_xdata()

    # 参数组合只是辅助元数据。CST 2022 对非参数化 Run 0 会在这里误报
    # “run id does not exist: 0”，但曲线数据本身已经成功读取。
    parameter_combination: Any = {}
    parameter_combination_warning: str | None = None
    try:
        parameter_combination = _serialize_value(result_item.get_parameter_combination())
    except Exception as exc:
        parameter_combination_warning = str(exc)

    if export_path:
        export_file.parent.mkdir(parents=True, exist_ok=True)
        export_file = export_file.resolve()
    else:
        leaf_name = treepath.rsplit("\\", 1)[-1].strip()
        if leaf_name.lower() == "s1,1":
            export_stem = "s11"
        else:
            export_stem = re.sub(r"[^0-9A-Za-z._-]+", "_", leaf_name).strip("._-")
            export_stem = export_stem or "result_0d1d"
        export_file = (
            Path(context["fullpath"]).parent.parent
            / "exports"
            / f"{export_stem}_run{resolved_run_id}.json"
        ).resolve()
        export_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        point_count = int(result_item.length)
    except (AttributeError, TypeError, ValueError):
        try:
            point_count = len(ydata)
        except TypeError:
            point_count = 1

    payload = {
        "treepath": result_item.treepath,
        "title": result_item.title,
        "xlabel": result_item.xlabel,
        "ylabel": result_item.ylabel,
        "length": point_count,
        "requested_run_id": requested_run_id,
        "run_id": result_item.run_id,
        "parameter_combination": parameter_combination,
        "parameter_combination_available": parameter_combination_warning is None,
        "xdata": _serialize_value(xdata),
        "ydata": _serialize_value(ydata),
    }
    if parameter_combination_warning:
        payload["parameter_combination_warning"] = parameter_combination_warning
    export_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "status": "success",
        "mode": "local_export_only",
        "project_path": context["fullpath"],
        "module_type": normalized_module,
        "active_subproject": context.get("active_subproject"),
        "treepath": result_item.treepath,
        "requested_run_id": requested_run_id,
        "run_id": result_item.run_id,
        "point_count": point_count,
        "export_path": str(export_file),
        "runtime_module": "cst_runtime.results",
    }
    if parameter_combination_warning:
        result["parameter_combination_warning"] = parameter_combination_warning
    return result


def get_2d_result(
    project_path: str,
    treepath: str,
    module_type: str = "3d",
    export_path: str = "",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
    include_data: bool = False,
) -> dict[str, Any]:
    try:
        project, context = _load_project(project_path, allow_interactive, subproject_treepath)
        result_module, normalized_module = _get_result_module(project, module_type)
        result_2d = get_result2d_item(result_module, treepath)
        if export_path:
            export_file = Path(export_path).expanduser()
            if export_file.suffix.lower() != ".json":
                return error_response(
                    "invalid_export_extension",
                    "get_2d_result export_path only supports .json",
                    export_path=str(export_file),
                    runtime_module="cst_runtime.results",
                )
            export_file.parent.mkdir(parents=True, exist_ok=True)
            export_file = export_file.resolve()
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            export_file = (
                Path(context["fullpath"]).parent.parent
                / "exports"
                / f"result_2d_{result_2d.ny}x{result_2d.nx}_{timestamp}.json"
            ).resolve()
            export_file.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "treepath": treepath,
            "title": result_2d.title,
            "xlabel": result_2d.xlabel,
            "ylabel": result_2d.ylabel,
            "xunit": result_2d.xunit,
            "yunit": result_2d.yunit,
            "dataunit": result_2d.dataunit,
            "xmin": result_2d.xmin,
            "xmax": result_2d.xmax,
            "ymin": result_2d.ymin,
            "ymax": result_2d.ymax,
            "nx": result_2d.nx,
            "ny": result_2d.ny,
            "xpositions": _serialize_value(result_2d.get_xpositions()),
            "ypositions": _serialize_value(result_2d.get_ypositions()),
            "data": _serialize_value(result_2d.get_data()),
        }
        export_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "status": "success",
            "mode": "local_export_only",
            "project_path": context["fullpath"],
            "module_type": normalized_module,
            "active_subproject": context["active_subproject"],
            "treepath": treepath,
            "nx": result_2d.nx,
            "ny": result_2d.ny,
            "export_path": str(export_file),
            "include_data_ignored": bool(include_data),
            "runtime_module": "cst_runtime.results",
        }
    except UnsupportedFeatureError as exc:
        return exc.to_response(project_path=str(project_path), treepath=treepath)
    except Exception as exc:
        return error_response(
            "get_2d_result_failed",
            str(exc),
            project_path=str(project_path),
            treepath=treepath,
            runtime_module="cst_runtime.results",
        )


def plot_project_result(
    project_path: str,
    treepath: str,
    module_type: str = "3d",
    run_id: int = 0,
    load_impedances: bool = True,
    output_html: str = "",
    page_title: str = "",
    allow_interactive: bool = False,
    subproject_treepath: str = "",
    result_kind: str = "auto",
    intermediate_json: str = "",
) -> dict[str, Any]:
    try:
        if not treepath:
            return error_response("treepath_missing", "treepath is required")
        output_target = Path(output_html).expanduser().resolve() if output_html else None
        if intermediate_json:
            export_path = Path(intermediate_json).expanduser().resolve()
        elif output_target is not None:
            export_path = output_target.with_suffix(".json")
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            export_path = Path(project_path).expanduser().resolve().parent.parent / "exports" / f"project_result_{timestamp}.json"
        export_path.parent.mkdir(parents=True, exist_ok=True)

        normalized_kind = (result_kind or "auto").strip().lower()
        attempts: list[tuple[str, dict[str, Any]]] = []
        if normalized_kind in {"auto", "1d", "0d/1d", "0d1d"}:
            attempts.append(
                (
                    "1d",
                    get_1d_result(
                        project_path=project_path,
                        treepath=treepath,
                        module_type=module_type,
                        run_id=run_id,
                        load_impedances=load_impedances,
                        export_path=str(export_path),
                        allow_interactive=allow_interactive,
                        subproject_treepath=subproject_treepath,
                    ),
                )
            )
        if normalized_kind in {"auto", "2d"} and (not attempts or attempts[-1][1].get("status") != "success"):
            attempts.append(
                (
                    "2d",
                    get_2d_result(
                        project_path=project_path,
                        treepath=treepath,
                        module_type=module_type,
                        export_path=str(export_path),
                        allow_interactive=allow_interactive,
                        subproject_treepath=subproject_treepath,
                    ),
                )
            )
        success = next(((kind, result) for kind, result in attempts if result.get("status") == "success"), None)
        if success is None:
            return error_response(
                "plot_project_result_export_failed",
                "could not export project result as 1D or 2D JSON",
                attempts=attempts,
                runtime_module="cst_runtime.results",
            )
        detected_kind, export_result = success
        from ..render.dashboard import plot_exported_file as _plot_exported
        plot_result = _plot_exported(
            file_path=str(export_path),
            output_html=str(output_target or ""),
            page_title=page_title or f"CST Result Preview - {treepath}",
        )
        if plot_result.get("status") != "success":
            return plot_result
        return {
            **plot_result,
            "source": "project_result",
            "detected_kind": detected_kind,
            "project_path": str(Path(project_path).expanduser().resolve()),
            "treepath": treepath,
            "run_id": run_id,
            "module_type": module_type,
            "intermediate_json": str(export_path),
            "runtime_module": "cst_runtime.results",
        }
    except Exception as exc:
        return error_response(
            "plot_project_result_failed",
            str(exc),
            project_path=str(project_path),
            treepath=treepath,
            runtime_module="cst_runtime.results",
        )


def generate_report(
    data_dir: str = "",
    output_html: str = "",
    page_title: str = "",
    modules: str = "",
    split: bool = False,
) -> dict[str, Any]:
    from ..render.dashboard import generate_report as _impl
    return _impl(
        data_dir=data_dir,
        output_html=output_html,
        page_title=page_title,
        modules=modules,
        split=split,
    )


def plot_exported_file(
    file_path: str = "",
    output_html: str = "",
    page_title: str = "",
) -> dict[str, Any]:
    from ..render.dashboard import plot_exported_file as _impl
    return _impl(
        file_path=file_path,
        output_html=output_html,
        page_title=page_title,
    )
