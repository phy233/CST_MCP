"""simulation.py — simulation lifecycle operations (start, poll, stop, configure).

Extracted from project.py for single-responsibility separation.
All functions go through gateway guard checks.
"""
from __future__ import annotations

from typing import Any

from . import gateway
from .errors import error_response
from .compatibility import (
    delete_project_results,
    get_project_solver_type,
)
from .compatibility.modeling import (
    fdsolver_stimulation_vba,
    mesh_fpbavoid_nonreg_unite_vba,
    solver_acceleration_vba,
)
from .identity import attach_expected_project
from .solver_diagnostics import (
    capture_solver_log_baseline,
    read_appended_solver_logs,
    save_solver_log_baseline,
)
from .utils import abs_project_path as _abs_project_path
from .modeling import _single_vba, _submit_versioned_vba


def start_simulation(project_path: str) -> dict[str, Any]:
    """同步运行求解器；仅当 CST 的 run_solver 返回 True 时报告成功。

    求解失败时附上本次求解新增到 Result/*.log 的 CST 原始报错块，
    让调用方无需查看 GUI Message Window 即可拿到错误文本。
    """
    normalized_project = _abs_project_path(project_path)
    rejected = gateway.guard_before_simulation(normalized_project)
    if rejected:
        return rejected

    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    baseline = capture_solver_log_baseline(normalized_project)
    try:
        solver_successful = bool(project.modeler.run_solver())
    except Exception as exc:
        return error_response(
            "start_simulation_failed",
            str(exc),
            project_path=normalized_project,
            runtime_module="cst_runtime.simulation",
        )
    diagnostics = read_appended_solver_logs(normalized_project, baseline=baseline)
    if not solver_successful:
        errors = list(diagnostics.get("errors") or [])
        first_error = errors[0] if errors else ""
        message = "CST 求解器已经结束，但 run_solver 返回 False，求解未成功完成"
        if first_error:
            message += f"；CST 原始报错：{first_error}"
        return error_response(
            "solver_run_failed",
            message,
            project_path=normalized_project,
            cst_errors=diagnostics.get("errors", []),
            cst_error_lines=diagnostics.get("error_lines", []),
            log_files=diagnostics.get("log_files", []),
            runtime_module="cst_runtime.simulation",
        )
    success_payload: dict[str, Any] = {
        "status": "success",
        "project_path": normalized_project,
        "message": "simulation completed",
        "solver_success": True,
        "cst_errors": diagnostics.get("errors", []),
        "runtime_module": "cst_runtime.simulation",
    }
    errors = diagnostics.get("errors") or []
    if errors:
        # run_solver 返回 True 但日志仍出现 Error 块：求解“完成”但 CST 已报错，
        # 用 warning 明确标记，调用方（如 sweep）应将其视为步骤失败。
        success_payload["warning"] = (
            "求解器返回成功，但 Result 日志中包含 CST 错误块：" + errors[0]
        )
    return success_payload


def start_simulation_async(project_path: str) -> dict[str, Any]:
    """异步启动求解器；返回成功仅表示 start_solver 调用已完成。"""
    normalized_project = _abs_project_path(project_path)
    rejected = gateway.guard_before_simulation(normalized_project)
    if rejected:
        return rejected

    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    try:
        # 落盘日志基线：start 与 wait 是两次独立调用，若求解器在两次调用
        # 之间就报错退出，wait 必须能跳过启动前已有的日志字节才能检出错误。
        save_solver_log_baseline(normalized_project)
        project.modeler.start_solver()
        return {
            "status": "success",
            "project_path": normalized_project,
            "message": "simulation started",
            "runtime_module": "cst_runtime.simulation",
        }
    except Exception as exc:
        return error_response(
            "start_simulation_async_failed",
            str(exc),
            project_path=normalized_project,
            runtime_module="cst_runtime.simulation",
        )


def is_simulation_running(project_path: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    try:
        running = bool(project.modeler.is_solver_running())
        return {
            "status": "success",
            "project_path": normalized_project,
            "running": running,
            "runtime_module": "cst_runtime.simulation",
        }
    except Exception as exc:
        return error_response(
            "is_simulation_running_failed",
            str(exc),
            project_path=normalized_project,
            runtime_module="cst_runtime.simulation",
        )


def stop_simulation(project_path: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    try:
        project.modeler.abort_solver()
        return {
            "status": "success",
            "project_path": normalized_project,
            "runtime_module": "cst_runtime.simulation",
        }
    except Exception as exc:
        return error_response(
            "stop_simulation_failed",
            str(exc),
            project_path=normalized_project,
            runtime_module="cst_runtime.simulation",
        )


def pause_simulation(project_path: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    try:
        project.modeler.pause_solver()
        return {
            "status": "success",
            "project_path": normalized_project,
            "message": "simulation paused",
            "runtime_module": "cst_runtime.simulation",
        }
    except Exception as exc:
        return error_response(
            "pause_simulation_failed",
            str(exc),
            project_path=normalized_project,
            runtime_module="cst_runtime.simulation",
        )


def resume_simulation(project_path: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    try:
        project.modeler.resume_solver()
        return {
            "status": "success",
            "project_path": normalized_project,
            "message": "simulation resumed",
            "runtime_module": "cst_runtime.simulation",
        }
    except Exception as exc:
        return error_response(
            "resume_simulation_failed",
            str(exc),
            project_path=normalized_project,
            runtime_module="cst_runtime.simulation",
        )


def set_solver_acceleration(
    project_path: str,
    use_parallelization: bool = True,
    max_threads: int = 1024,
    max_cpu_devices: int = 2,
    remote_calc: bool = False,
    use_distributed: bool = False,
    max_distributed_ports: int = 64,
    distribute_matrix: bool = True,
    mpi_parallel: bool = False,
    auto_mpi: bool = False,
    hardware_accel: bool = True,
    max_gpus: int = 4,
) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "Set Solver Acceleration",
        solver_acceleration_vba,
        use_parallelization=use_parallelization,
        max_threads=max_threads,
        max_cpu_devices=max_cpu_devices,
        remote_calc=remote_calc,
        use_distributed=use_distributed,
        max_distributed_ports=max_distributed_ports,
        distribute_matrix=distribute_matrix,
        mpi_parallel=mpi_parallel,
        auto_mpi=auto_mpi,
        hardware_accel=hardware_accel,
        max_gpus=max_gpus,
    )


def set_fdsolver_extrude_open_bc(project_path: str, enable: bool = True) -> dict[str, Any]:
    return _single_vba_pops(project_path, "set FDSolver ExtrudeOpenBC", f'FDSolver.ExtrudeOpenBC {"True" if enable else "False"}')


def define_fdsolver_stimulation(
    project_path: str,
    port: int | str,
    mode: int | str,
) -> dict[str, Any]:
    """依据 CST 2022 手册仅配置激励源，不执行 FDSolver.Reset。"""
    return _submit_versioned_vba(
        project_path,
        "Define FDSolver Stimulation",
        fdsolver_stimulation_vba,
        port=port,
        mode=mode,
    )


def set_mesh_fpbavoid_nonreg_unite(project_path: str, enable: bool = True) -> dict[str, Any]:
    return _submit_versioned_vba(
        project_path,
        "set nonregular FPBA union handling",
        mesh_fpbavoid_nonreg_unite_vba,
        enable=enable,
    )


def set_mesh_minimum_step_number(project_path: str, num_steps: int = 5) -> dict[str, Any]:
    return _single_vba_pops(project_path, "set Mesh.MinimumStepNumber", f'Mesh.MinimumStepNumber "{num_steps}"')


def _single_vba_pops(project_path: str, history_name: str, vba_line: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    try:
        res = _single_vba(normalized_project, history_name, vba_line, project=project)
        if res.get("status") == "error":
            return res
        return {"status": "success", "project_path": normalized_project, "runtime_module": "cst_runtime.simulation"}
    except Exception as exc:
        return error_response(f"{history_name}_failed", str(exc), project_path=normalized_project, runtime_module="cst_runtime.simulation")
def set_frequency_range(project_path: str, fmin: float, fmax: float) -> dict[str, Any]:
    """设置求解频率范围。"""
    return _single_vba_pops(
        project_path,
        "Set Frequency Range",
        f'Solver.FrequencyRange "{fmin}", "{fmax}"',
    )


def rebuild_structure(project_path: str) -> dict[str, Any]:
    """根据当前参数重建结构；CST 官方说明该操作会删除全部结果。"""
    result = _single_vba_pops(
        project_path,
        "Rebuild",
        "\n".join(
            [
                "If Not Rebuild Then",
                '    ReportError "Rebuild returned False"',
                "End If",
            ]
        ),
    )
    if result.get("status") != "error":
        result["results_deleted"] = True
        result["warning"] = "Rebuild 会删除当前工程中的全部求解结果"
    return result


def delete_results(project_path: str) -> dict[str, Any]:
    """删除工程结果，自动选择 Python API 或旧版即时 VBA。"""
    project, status = attach_expected_project(project_path)
    if project is None:
        return status
    try:
        compatibility = delete_project_results(project)
        return {
            "status": "success",
            "project_path": project_path,
            "deleted": True,
            "compatibility": compatibility,
        }
    except Exception as exc:
        return error_response("delete_results_failed", str(exc), project_path=project_path)


def get_solver_type(project_path: str) -> dict[str, Any]:
    """读取当前求解器类型。"""
    project, status = attach_expected_project(project_path)
    if project is None:
        return status
    try:
        solver_type, compatibility = get_project_solver_type(project)
        return {
            "status": "success",
            "project_path": project_path,
            "solver_type": solver_type,
            "compatibility": compatibility,
        }
    except Exception as exc:
        return error_response("get_solver_type_failed", str(exc), project_path=project_path)
