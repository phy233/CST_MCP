"""CST parameter sweep operations.

This module provides parameter sweep functionality similar to MATLAB's crossProcess.m.
It allows scanning multiple parameters and building lookup tables (LUT).

Usage:
    from cst_runtime.lib.session import open_project
    from cst_runtime.workflows.sweep import ParameterSweep

    # 工程生命周期由调用方管理，扫描不会自动打开或关闭工程
    open_project("C:\\path\\to\\model.cst").raise_for_error()

    # Create a parameter sweep
    sweep = ParameterSweep(
        project_path="C:\\path\\to\\model.cst",
        parameters=["lx", "ly1"],
        ranges=[np.arange(3, 10.5, 0.4), np.arange(3, 10.5, 0.4)],
        target_freq_ghz=8.0,
        result_paths=["1D Results\\S-Parameters\\SZmax(1),Zmax(1)",
                      "1D Results\\S-Parameters\\SZmax(2),Zmax(2)"],
    )

    # Run the sweep
    results = sweep.run(output_dir="C:\\results")

    # Access results
    print(results.lut)  # DataFrame with parameter values and S-parameter results
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd

from ..lib.parameters import get_param, param_exists, set_param
from ..lib.results import get_sparam, get_sparam_at_freq
from ..lib.session import reattach_project
from ..lib.solver import delete_results, rebuild, start
from ..lib.contracts import CSTOperationError


def _raise_if_error(result: Any) -> Any:
    """检查统一结果，同时兼容第三方测试替身的旧返回值。"""
    if isinstance(result, dict) and result.get("status") == "error":
        raise RuntimeError(result.get("message", "工作流原子操作失败"))
    return result


def _result_value(result: Any, field: str) -> Any:
    """从统一结果取值；普通标量仅作为旧扩展兼容。"""
    _raise_if_error(result)
    if isinstance(result, dict) and "status" in result:
        return result[field]
    return result

logger = logging.getLogger(__name__)


def _json_safe(value: Any) -> Any:
    """递归转换 NumPy 标量等非标准 JSON 值。"""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


@dataclass
class SweepResult:
    """Result of a parameter sweep."""
    lut: pd.DataFrame
    output_dir: Path
    sweep_time: float
    total_steps: int
    successful_steps: int
    failed_steps: int
    exported_files: list[Path] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为 JSON 可序列化字典。"""
        records = (
            self.lut.astype(object)
            .where(pd.notna(self.lut), None)
            .to_dict(orient="records")
        )
        return {
            "status": (
                "success"
                if self.failed_steps == 0 and not self.errors
                else "partial"
            ),
            "output_dir": str(self.output_dir),
            "sweep_time": self.sweep_time,
            "total_steps": self.total_steps,
            "successful_steps": self.successful_steps,
            "failed_steps": self.failed_steps,
            "records": _json_safe(records),
            "exported_files": [str(path) for path in self.exported_files],
            "errors": _json_safe(self.errors),
        }


class ParameterSweep:
    """Parameter sweep for CST simulations.

    This class implements parameter scanning functionality similar to
    MATLAB's crossProcess.m, allowing systematic exploration of parameter
    space and building lookup tables.

    Args:
        project_path: Path to .cst file
        parameters: List of parameter names to sweep
        ranges: List of parameter ranges (one per parameter)
        target_freq_ghz: Target frequency for S-parameter extraction
        result_paths: List of result tree paths to read
        callback: Optional callback function called after each step

    Example:
        sweep = ParameterSweep(
            project_path="C:\\model.cst",
            parameters=["lx", "ly1"],
            ranges=[np.arange(3, 10.5, 0.4), np.arange(3, 10.5, 0.4)],
            target_freq_ghz=8.0,
        )
        results = sweep.run()
    """

    def __init__(
        self,
        project_path: str,
        parameters: list[str],
        ranges: list[Sequence[float]],
        target_freq_ghz: float,
        result_paths: list[str] | None = None,
        callback: Callable[[int, dict[str, float], dict[str, Any]], None] | None = None,
        continue_on_error: bool = True,
        restore_parameters: bool = True,
    ) -> None:
        if len(parameters) != len(ranges):
            raise ValueError("Number of parameters must match number of ranges")

        self.project_path = project_path
        self.parameters = parameters
        self.ranges = [list(r) for r in ranges]
        self.target_freq_ghz = target_freq_ghz
        self.result_paths = result_paths or [
            "1D Results\\S-Parameters\\S1,1"
        ]
        self.callback = callback
        self.continue_on_error = continue_on_error
        self.restore_parameters = restore_parameters

        # Calculate total steps
        self.total_steps = 1
        for r in self.ranges:
            self.total_steps *= len(r)

    def _validate_parameters(self) -> None:
        """Validate that all parameters exist in the project."""
        for param in self.parameters:
            exists_result = param_exists(self.project_path, param)
            exists = _result_value(exists_result, "exists")
            if not bool(exists):
                raise ValueError(f"Parameter '{param}' does not exist in project")

    def _require_open_project(self) -> None:
        """确认工程已由调用方打开，不在扫描中隐式管理会话。"""
        result = reattach_project(self.project_path)
        if result.get("status") == "error":
            payload = dict(result)
            if payload.get("error_type") in {"no_cst_session", "project_not_open"}:
                payload["cause_error_type"] = payload.get("error_type")
                payload["error_type"] = "project_not_open"
                payload["message"] = (
                    "参数扫描要求调用方先通过 open_project() 打开指定工程"
                )
            raise CSTOperationError(payload)

    def _generate_grid(self) -> list[dict[str, float]]:
        """Generate parameter grid for sweep.

        Returns:
            List of parameter dictionaries
        """
        import itertools
        grid = []
        for combo in itertools.product(*self.ranges):
            grid.append(dict(zip(self.parameters, combo)))
        return grid

    def _run_single_step(
        self,
        params: dict[str, float],
        sparam_dir: Path,
        step: int,
    ) -> dict[str, Any]:
        """Run a single simulation step.

        Args:
            params: Parameter values for this step
            sparam_dir: Directory for S-parameter exports
            step: Current step number

        Returns:
            Dict with results for this step
        """
        logger.info(f"Step {step}/{self.total_steps}: {params}")

        # Set parameters
        for name, value in params.items():
            _raise_if_error(set_param(self.project_path, name, value))

        # Delete old results and rebuild
        _raise_if_error(delete_results(self.project_path))
        _raise_if_error(rebuild(self.project_path))

        # Run simulation（同步 run_solver；日志含错误块时即使返回 True 也按失败处理）
        started = start(self.project_path)
        _raise_if_error(started)
        if isinstance(started, dict) and started.get("cst_errors"):
            raise RuntimeError(
                "求解完成后 Result 日志含 CST 报错：" + str(started["cst_errors"][0])
            )

        # Extract results
        results = {
            "params": params,
            "sparams": {},
            "exported_files": [],
        }

        created_files: list[Path] = []
        try:
            for result_path in self.result_paths:
                # Get S-parameter at target frequency
                sparam_result = get_sparam_at_freq(
                    self.project_path,
                    result_path,
                    self.target_freq_ghz,
                    allow_interactive=True,
                )
                _raise_if_error(sparam_result)
                results["sparams"][result_path] = sparam_result

                # Save full S-parameter data to file
                exported_path = self._save_sparam_data(
                    result_path, params, sparam_dir
                )
                results["exported_files"].append(exported_path)
                created_files.append(exported_path)
        except Exception:
            for path in created_files:
                path.unlink(missing_ok=True)
            raise

        return results

    def _save_sparam_data(
        self,
        result_path: str,
        params: dict[str, float],
        sparam_dir: Path,
    ) -> Path:
        """Save full S-parameter data to file.

        Args:
            result_path: Result tree path
            params: Parameter values
            sparam_dir: Directory for exports
        """
        sparam_data = get_sparam(
            self.project_path,
            result_path,
            allow_interactive=True,
        )
        _raise_if_error(sparam_data)
        ydata = sparam_data.get("ydata")
        if not isinstance(ydata, list) or not ydata:
            raise RuntimeError(f"S 参数结果为空: {result_path}")

        safe_name = result_path.replace("\\", "_").replace(" ", "_")
        param_str = "_".join(f"{k}{v:.4f}" for k, v in params.items())
        filename = f"{safe_name}_{param_str}.csv"
        filepath = sparam_dir / filename
        dataframe = pd.DataFrame(ydata)
        required_columns = ["frequency", "real", "imag"]
        if list(dataframe.columns) != required_columns:
            raise RuntimeError(
                f"S 参数列不完整: 期望 {required_columns}，实际 {list(dataframe.columns)}"
            )
        dataframe.to_csv(filepath, index=False)
        logger.debug("Saved S-parameter data to %s", filepath)
        return filepath

    def run(
        self,
        output_dir: str | Path | None = None,
        save_lut: bool = True,
        save_csv: bool = True,
    ) -> SweepResult:
        """Run the parameter sweep.

        Args:
            output_dir: Output directory for results (default: auto-generated)
            save_lut: Whether to save LUT to .npz file
            save_csv: Whether to save LUT to .csv file

        Returns:
            SweepResult with LUT and metadata

        Raises:
            RuntimeError: If sweep fails
        """
        self._require_open_project()
        self._validate_parameters()
        original_values = {
            name: _result_value(get_param(self.project_path, name), "value")
            for name in self.parameters
        }
        grid = self._generate_grid()
        result_dir = (
            Path.cwd() / f"sweep_results_{time.strftime('%Y%m%d_%H%M%S')}"
            if output_dir is None
            else Path(output_dir)
        )
        result_dir.mkdir(parents=True, exist_ok=True)
        sparam_dir = result_dir / "S_Parameters"
        sparam_dir.mkdir(exist_ok=True)
        logger.info("开始参数扫描，共 %s 步", self.total_steps)

        lut_rows: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        successful_steps = 0
        failed_steps = 0
        exported_files: list[Path] = []
        start_time = time.time()

        try:
            for step, params in enumerate(grid, 1):
                try:
                    results = self._run_single_step(params, sparam_dir, step)
                    missing_results = [
                        path for path in self.result_paths
                        if path not in results.get("sparams", {})
                    ]
                    if missing_results:
                        raise RuntimeError(
                            "扫描步骤缺少结果: " + ", ".join(missing_results)
                        )
                    row: dict[str, Any] = dict(params)
                    for result_path in self.result_paths:
                        sparam_result = results["sparams"][result_path]
                        _raise_if_error(sparam_result)
                        safe_name = result_path.split("\\")[-1]
                        row[f"{safe_name}_mag"] = sparam_result["magnitude"]
                        row[f"{safe_name}_mag_db"] = sparam_result["magnitude_db"]
                        row[f"{safe_name}_phase_deg"] = sparam_result["phase_deg"]
                        row[f"{safe_name}_real"] = sparam_result["real"]
                        row[f"{safe_name}_imag"] = sparam_result["imag"]
                    exported_files.extend(results.get("exported_files", []))
                    lut_rows.append(row)
                    successful_steps += 1
                    if self.callback:
                        self.callback(step, params, results)
                except Exception as exc:
                    failed_steps += 1
                    errors.append(
                        {"step": step, "parameters": dict(params), "message": str(exc)}
                    )
                    row = dict(params)
                    for result_path in self.result_paths:
                        safe_name = result_path.split("\\")[-1]
                        for suffix in ("mag", "mag_db", "phase_deg", "real", "imag"):
                            row[f"{safe_name}_{suffix}"] = np.nan
                    lut_rows.append(row)
                    if not self.continue_on_error:
                        raise
        finally:
            if self.restore_parameters:
                restore_errors: list[str] = []
                for name, value in original_values.items():
                    try:
                        _raise_if_error(set_param(self.project_path, name, value))
                    except Exception as exc:
                        restore_errors.append(f"{name}: {exc}")
                try:
                    _raise_if_error(rebuild(self.project_path))
                except Exception as exc:
                    restore_errors.append(f"rebuild: {exc}")
                if restore_errors:
                    errors.append(
                        {
                            "step": None,
                            "parameters": original_values,
                            "message": "参数恢复失败: " + "; ".join(restore_errors),
                        }
                    )

        lut = pd.DataFrame(lut_rows)
        if save_csv:
            csv_path = result_dir / "lut.csv"
            lut.to_csv(csv_path, index=False)
            exported_files.append(csv_path)
        if save_lut:
            npz_path = result_dir / "lut.npz"
            np.savez(npz_path, **{column: lut[column].values for column in lut.columns})
            exported_files.append(npz_path)

        result = SweepResult(
            lut=lut,
            output_dir=result_dir,
            sweep_time=time.time() - start_time,
            total_steps=self.total_steps,
            successful_steps=successful_steps,
            failed_steps=failed_steps,
            exported_files=exported_files,
            errors=errors,
        )
        logger.info(
            "参数扫描完成：成功 %s/%s，失败 %s",
            successful_steps,
            self.total_steps,
            failed_steps,
        )
        return result


def quick_sweep(
    project_path: str,
    parameters: dict[str, Sequence[float]],
    target_freq_ghz: float,
    result_path: str = "1D Results\\S-Parameters\\S1,1",
    output_dir: str | Path | None = None,
    continue_on_error: bool = True,
    restore_parameters: bool = True,
) -> SweepResult:
    """Quick parameter sweep with simple interface.

    Args:
        project_path: Path to .cst file
        parameters: Dict mapping parameter names to ranges
        target_freq_ghz: Target frequency in GHz
        result_path: Result tree path to read
        output_dir: Output directory

    Returns:
        SweepResult with LUT

    Example:
        from cst_runtime.workflows.sweep import quick_sweep

        results = quick_sweep(
            project_path="C:\\model.cst",
            parameters={"lx": np.arange(3, 10.5, 0.4), "ly1": np.arange(3, 10.5, 0.4)},
            target_freq_ghz=8.0,
        )
        print(results.lut)
    """
    param_names = list(parameters.keys())
    param_ranges = list(parameters.values())

    sweep = ParameterSweep(
        project_path=project_path,
        parameters=param_names,
        ranges=param_ranges,
        target_freq_ghz=target_freq_ghz,
        result_paths=[result_path],
        continue_on_error=continue_on_error,
        restore_parameters=restore_parameters,
    )

    return sweep.run(output_dir=output_dir)
