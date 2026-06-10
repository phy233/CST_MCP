"""CST parameter sweep operations.

This module provides parameter sweep functionality similar to MATLAB's crossProcess.m.
It allows scanning multiple parameters and building lookup tables (LUT).

Usage:
    from cst_runtime.lib.sweep import ParameterSweep

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

from .parameters import list_params, set_param, param_exists
from .solver import start, wait, rebuild, delete_results
from .results import get_sparam, get_sparam_at_freq

logger = logging.getLogger(__name__)


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

        # Calculate total steps
        self.total_steps = 1
        for r in self.ranges:
            self.total_steps *= len(r)

    def _validate_parameters(self) -> None:
        """Validate that all parameters exist in the project."""
        for param in self.parameters:
            if not param_exists(self.project_path, param):
                raise ValueError(f"Parameter '{param}' does not exist in project")

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
            set_param(self.project_path, name, value)

        # Delete old results and rebuild
        delete_results(self.project_path)
        rebuild(self.project_path)

        # Run simulation
        start(self.project_path)
        wait(self.project_path)

        # Extract results
        results = {"params": params, "sparams": {}}

        for result_path in self.result_paths:
            try:
                # Get S-parameter at target frequency
                sparam_result = get_sparam_at_freq(
                    self.project_path,
                    result_path,
                    self.target_freq_ghz,
                )
                results["sparams"][result_path] = sparam_result

                # Save full S-parameter data to file
                self._save_sparam_data(
                    result_path, params, sparam_dir
                )

            except Exception as e:
                logger.warning(f"Failed to read {result_path}: {e}")
                results["sparams"][result_path] = {"error": str(e)}

        return results

    def _save_sparam_data(
        self,
        result_path: str,
        params: dict[str, float],
        sparam_dir: Path,
    ) -> None:
        """Save full S-parameter data to file.

        Args:
            result_path: Result tree path
            params: Parameter values
            sparam_dir: Directory for exports
        """
        try:
            # Read full S-parameter data
            sparam_data = get_sparam(self.project_path, result_path)

            # Create filename from result path and parameters
            safe_name = result_path.replace("\\", "_").replace(" ", "_")
            param_str = "_".join(f"{k}{v:.4f}" for k, v in params.items())
            filename = f"{safe_name}_{param_str}.csv"
            filepath = sparam_dir / filename

            # Save to CSV
            ydata = sparam_data.get("ydata", [])
            if ydata:
                df = pd.DataFrame(ydata)
                df.to_csv(filepath, index=False)
                logger.debug(f"Saved S-parameter data to {filepath}")

        except Exception as e:
            logger.warning(f"Failed to save S-parameter data: {e}")

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
        # Setup output directory
        if output_dir is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_dir = Path.cwd() / f"sweep_results_{timestamp}"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        sparam_dir = output_dir / "S_Parameters"
        sparam_dir.mkdir(exist_ok=True)

        # Validate parameters
        self._validate_parameters()

        # Generate parameter grid
        grid = self._generate_grid()
        logger.info(f"Starting parameter sweep: {self.total_steps} steps")

        # Initialize results
        lut_rows = []
        successful_steps = 0
        failed_steps = 0
        start_time = time.time()

        # Run sweep
        for step, params in enumerate(grid, 1):
            try:
                results = self._run_single_step(params, sparam_dir, step)

                # Build LUT row
                row = dict(params)
                for result_path, sparam_result in results["sparams"].items():
                    if "error" not in sparam_result:
                        # Extract magnitude and phase
                        safe_name = result_path.split("\\")[-1]
                        row[f"{safe_name}_mag"] = sparam_result.get("magnitude", 0)
                        row[f"{safe_name}_mag_db"] = sparam_result.get("magnitude_db", 0)
                        row[f"{safe_name}_phase_deg"] = sparam_result.get("phase_deg", 0)
                        row[f"{safe_name}_real"] = sparam_result.get("real", 0)
                        row[f"{safe_name}_imag"] = sparam_result.get("imag", 0)

                lut_rows.append(row)
                successful_steps += 1

                # Call callback if provided
                if self.callback:
                    self.callback(step, params, results)

                logger.info(
                    f"Step {step}/{self.total_steps} completed: "
                    f"{', '.join(f'{k}={v:.4f}' for k, v in params.items())}"
                )

            except Exception as e:
                logger.error(f"Step {step}/{self.total_steps} failed: {e}")
                failed_steps += 1

                # Add failed row with NaN values
                row = dict(params)
                for result_path in self.result_paths:
                    safe_name = result_path.split("\\")[-1]
                    row[f"{safe_name}_mag"] = np.nan
                    row[f"{safe_name}_mag_db"] = np.nan
                    row[f"{safe_name}_phase_deg"] = np.nan
                    row[f"{safe_name}_real"] = np.nan
                    row[f"{safe_name}_imag"] = np.nan
                lut_rows.append(row)

        # Create LUT DataFrame
        lut = pd.DataFrame(lut_rows)
        sweep_time = time.time() - start_time

        # Save results
        if save_csv:
            csv_path = output_dir / "lut.csv"
            lut.to_csv(csv_path, index=False)
            logger.info(f"Saved LUT to {csv_path}")

        if save_lut:
            npz_path = output_dir / "lut.npz"
            lut_dict = {col: lut[col].values for col in lut.columns}
            np.savez(npz_path, **lut_dict)
            logger.info(f"Saved LUT to {npz_path}")

        # Create result
        result = SweepResult(
            lut=lut,
            output_dir=output_dir,
            sweep_time=sweep_time,
            total_steps=self.total_steps,
            successful_steps=successful_steps,
            failed_steps=failed_steps,
        )

        logger.info(
            f"Sweep completed: {successful_steps}/{self.total_steps} successful, "
            f"{failed_steps} failed, time: {sweep_time:.1f}s"
        )

        return result


def quick_sweep(
    project_path: str,
    parameters: dict[str, Sequence[float]],
    target_freq_ghz: float,
    result_path: str = "1D Results\\S-Parameters\\S1,1",
    output_dir: str | Path | None = None,
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
        from cst_runtime.lib.sweep import quick_sweep

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
    )

    return sweep.run(output_dir=output_dir)


def load_lut(filepath: str | Path) -> pd.DataFrame:
    """Load a saved LUT file.

    Args:
        filepath: Path to .csv or .npz file

    Returns:
        DataFrame with LUT data

    Raises:
        ValueError: If file format is not supported
    """
    filepath = Path(filepath)

    if filepath.suffix == ".csv":
        return pd.read_csv(filepath)
    elif filepath.suffix == ".npz":
        data = np.load(filepath)
        return pd.DataFrame({k: data[k] for k in data.files})
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")


def interpolate_lut(
    lut: pd.DataFrame,
    param_columns: list[str],
    value_column: str,
    target_params: dict[str, float],
) -> float:
    """Interpolate a value from a LUT.

    Args:
        lut: LUT DataFrame
        param_columns: Parameter column names
        value_column: Value column name
        target_params: Target parameter values

    Returns:
        Interpolated value

    Example:
        lut = load_lut("C:\\results\\lut.csv")
        value = interpolate_lut(
            lut,
            param_columns=["lx", "ly1"],
            value_column="S1,1_mag_db",
            target_params={"lx": 5.0, "ly1": 6.0},
        )
    """
    from scipy.interpolate import RegularGridInterpolator

    # Extract parameter values
    param_values = [lut[col].unique() for col in param_columns]

    # Reshape value grid
    shape = [len(vals) for vals in param_values]
    value_grid = lut[value_column].values.reshape(shape)

    # Create interpolator
    interpolator = RegularGridInterpolator(
        param_values, value_grid, method="linear"
    )

    # Interpolate
    target_point = [target_params[col] for col in param_columns]
    return float(interpolator(target_point))
