"""simulation.py — simulation lifecycle operations (start, poll, stop, configure).

Extracted from project.py for single-responsibility separation.
All functions go through gateway guard checks.
"""
from __future__ import annotations

from typing import Any

from . import gateway
from .errors import error_response
from .compatibility import get_model3d
from .identity import attach_expected_project
from .utils import abs_project_path as _abs_project_path
from .modeling import _add_vba_history, _single_vba


def start_simulation(project_path: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    rejected = gateway.guard_before_simulation(normalized_project)
    if rejected:
        return rejected

    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    try:
        project.modeler.run_solver()
        return {
            "status": "success",
            "project_path": normalized_project,
            "message": "simulation completed",
            "runtime_module": "cst_runtime.simulation",
        }
    except Exception as exc:
        return error_response(
            "start_simulation_failed",
            str(exc),
            project_path=normalized_project,
            runtime_module="cst_runtime.simulation",
        )


def start_simulation_async(project_path: str) -> dict[str, Any]:
    normalized_project = _abs_project_path(project_path)
    rejected = gateway.guard_before_simulation(normalized_project)
    if rejected:
        return rejected

    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status
    try:
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
    normalized_project = _abs_project_path(project_path)
    project, status = attach_expected_project(normalized_project)
    if project is None:
        return status

    def _b(v: bool) -> str:
        return "True" if v else "False"

    vba = [
        "With Solver",
        f'     .UseParallelization "{_b(use_parallelization)}"',
        f'     .MaximumNumberOfThreads "{max_threads}"',
        f'     .MaximumNumberOfCPUDevices "{max_cpu_devices}"',
        f'     .RemoteCalculation "{_b(remote_calc)}"',
        f'     .UseDistributedComputing "{_b(use_distributed)}"',
        f'     .MaxNumberOfDistributedComputingPorts "{max_distributed_ports}"',
        f'     .DistributeMatrixCalculation "{_b(distribute_matrix)}"',
        f'     .MPIParallelization "{_b(mpi_parallel)}"',
        f'     .AutomaticMPI "{_b(auto_mpi)}"',
        f'     .HardwareAcceleration "{_b(hardware_accel)}"',
        f'     .MaximumNumberOfGPUs "{max_gpus}"',
        "End With",
    ]
    try:
        res = _add_vba_history(normalized_project, "Set Solver Acceleration", vba, project=project)
        if res.get("status") == "error":
            return res
        return {"status": "success", "project_path": normalized_project, "runtime_module": "cst_runtime.simulation"}
    except Exception as exc:
        return error_response("set_solver_acceleration_failed", str(exc), project_path=normalized_project, runtime_module="cst_runtime.simulation")


def set_fdsolver_extrude_open_bc(project_path: str, enable: bool = True) -> dict[str, Any]:
    return _single_vba_pops(project_path, "set FDSolver ExtrudeOpenBC", f'FDSolver.ExtrudeOpenBC {"True" if enable else "False"}')


def set_mesh_fpbavoid_nonreg_unite(project_path: str, enable: bool = True) -> dict[str, Any]:
    return _single_vba_pops(project_path, "set Mesh.FPBAAvoidNonRegUnite", f'Mesh.FPBAAvoidNonRegUnite {"True" if enable else "False"}')


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
    """根据当前参数重建结构。"""
    return _single_vba_pops(project_path, "Rebuild", "Application.Rebuild")


def delete_results(project_path: str) -> dict[str, Any]:
    """删除工程结果，隐藏 model3d 具体访问。"""
    project, status = attach_expected_project(project_path)
    if project is None:
        return status
    try:
        get_model3d(project).DeleteResults()
        return {"status": "success", "project_path": project_path, "deleted": True}
    except Exception as exc:
        return error_response("delete_results_failed", str(exc), project_path=project_path)


def get_solver_type(project_path: str) -> dict[str, Any]:
    """读取当前求解器类型。"""
    project, status = attach_expected_project(project_path)
    if project is None:
        return status
    try:
        solver_type = str(get_model3d(project).GetSolverType())
        return {"status": "success", "project_path": project_path, "solver_type": solver_type}
    except Exception as exc:
        return error_response("get_solver_type_failed", str(exc), project_path=project_path)
