"""Cross-shaped unit cell parameter sweep.

This module implements parameter sweep for cross-shaped metasurface unit cells,
similar to MATLAB's crossProcess.m.

Usage:
    from cst_runtime.lib.cross_process import CrossProcessSweep

    # Create sweep for cross-shaped unit cell
    sweep = CrossProcessSweep(
        project_path="C:\\path\\to\\model.cst",
        lx_range=np.arange(3.0, 10.5, 0.4),
        ly1_range=np.arange(3.0, 10.5, 0.4),
        target_freq_ghz=8.0,
    )

    # Run sweep
    results = sweep.run(output_dir="C:\\results\\cross_sweep")
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .sweep import ParameterSweep, SweepResult

logger = logging.getLogger(__name__)


class CrossProcessSweep:
    """Parameter sweep for cross-shaped unit cells.

    This class implements the parameter sweep logic from MATLAB's crossProcess.m,
    specifically designed for cross-shaped metasurface unit cells.

    Args:
        project_path: Path to .cst file
        lx_range: Range for lx parameter (cross arm length)
        ly1_range: Range for ly1 parameter (cross arm width)
        target_freq_ghz: Target frequency in GHz
        y_polarization_path: Result path for Y-polarization S-parameter
        x_polarization_path: Result path for X-polarization S-parameter

    Example:
        sweep = CrossProcessSweep(
            project_path="C:\\model.cst",
            lx_range=np.arange(3.0, 10.5, 0.4),
            ly1_range=np.arange(3.0, 10.5, 0.4),
            target_freq_ghz=8.0,
        )
        results = sweep.run()
    """

    def __init__(
        self,
        project_path: str,
        lx_range: np.ndarray,
        ly1_range: np.ndarray,
        target_freq_ghz: float,
        y_polarization_path: str = "1D Results\\S-Parameters\\SZmax(1),Zmax(1)",
        x_polarization_path: str = "1D Results\\S-Parameters\\SZmax(2),Zmax(2)",
    ) -> None:
        self.project_path = project_path
        self.lx_range = lx_range
        self.ly1_range = ly1_range
        self.target_freq_ghz = target_freq_ghz
        self.y_polarization_path = y_polarization_path
        self.x_polarization_path = x_polarization_path

    def _callback(
        self,
        step: int,
        params: dict[str, float],
        results: dict[str, Any],
    ) -> None:
        """Callback for progress reporting.

        Args:
            step: Current step number
            params: Parameter values
            results: Simulation results
        """
        # Extract results for both polarizations
        y_result = results["sparams"].get(self.y_polarization_path, {})
        x_result = results["sparams"].get(self.x_polarization_path, {})

        y_mag = y_result.get("magnitude_db", 0)
        y_phase = y_result.get("phase_deg", 0)
        x_mag = x_result.get("magnitude_db", 0)
        x_phase = x_result.get("phase_deg", 0)

        lx = params.get("lx", 0)
        ly1 = params.get("ly1", 0)

        logger.info(
            f"    -> Results: lx={lx:.4f}, ly1={ly1:.4f} | "
            f"Y: Mag={y_mag:.3f} dB, Phase={y_phase:.2f} deg | "
            f"X: Mag={x_mag:.3f} dB, Phase={x_phase:.2f} deg"
        )

    def run(
        self,
        output_dir: str | Path | None = None,
    ) -> SweepResult:
        """Run the cross-shaped unit cell parameter sweep.

        Args:
            output_dir: Output directory for results

        Returns:
            SweepResult with LUT containing both polarization results
        """
        # Create sweep object
        sweep = ParameterSweep(
            project_path=self.project_path,
            parameters=["lx", "ly1"],
            ranges=[self.lx_range, self.ly1_range],
            target_freq_ghz=self.target_freq_ghz,
            result_paths=[
                self.y_polarization_path,
                self.x_polarization_path,
            ],
            callback=self._callback,
        )

        # Run sweep
        results = sweep.run(output_dir=output_dir)

        # Rename columns for clarity
        results.lut = self._rename_columns(results.lut)

        return results

    def _rename_columns(self, lut: pd.DataFrame) -> pd.DataFrame:
        """Rename columns for better readability.

        Args:
            lut: Original LUT DataFrame

        Returns:
            DataFrame with renamed columns
        """
        rename_map = {}
        for col in lut.columns:
            if "SZmax(1),Zmax(1)" in col:
                rename_map[col] = col.replace("SZmax(1),Zmax(1)", "Y_pol")
            elif "SZmax(2),Zmax(2)" in col:
                rename_map[col] = col.replace("SZmax(2),Zmax(2)", "X_pol")

        return lut.rename(columns=rename_map)


def quick_cross_sweep(
    project_path: str,
    lx_range: np.ndarray,
    ly1_range: np.ndarray,
    target_freq_ghz: float,
    output_dir: str | Path | None = None,
) -> SweepResult:
    """Quick parameter sweep for cross-shaped unit cells.

    Args:
        project_path: Path to .cst file
        lx_range: Range for lx parameter
        ly1_range: Range for ly1 parameter
        target_freq_ghz: Target frequency in GHz
        output_dir: Output directory

    Returns:
        SweepResult with LUT

    Example:
        import numpy as np
        from cst_runtime.lib.cross_process import quick_cross_sweep

        results = quick_cross_sweep(
            project_path="C:\\model.cst",
            lx_range=np.arange(3.0, 10.5, 0.4),
            ly1_range=np.arange(3.0, 10.5, 0.4),
            target_freq_ghz=8.0,
        )
    """
    sweep = CrossProcessSweep(
        project_path=project_path,
        lx_range=lx_range,
        ly1_range=ly1_range,
        target_freq_ghz=target_freq_ghz,
    )

    return sweep.run(output_dir=output_dir)
