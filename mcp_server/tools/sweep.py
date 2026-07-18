"""MCP Tool definitions: CST Sweep operations."""
from typing import Any, Sequence, Tuple, List, Dict, Optional, Union

from ..proxy import call_cst

def quick_sweep(project_path: str, parameters: dict[str, list[float]], target_freq_ghz: float, result_path: str = '1D Results\\S-Parameters\\S1,1', output_dir: str | Path | None = None) -> dict[str, Any]:
    """
    Quick parameter sweep with simple interface.

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
            project_path="C:\model.cst",
            parameters={"lx": np.arange(3, 10.5, 0.4), "ly1": np.arange(3, 10.5, 0.4)},
            target_freq_ghz=8.0,
        )
        print(results.lut)
    """
    return call_cst("lib.sweep", "quick_sweep", project_path=project_path, parameters=parameters, target_freq_ghz=target_freq_ghz, result_path=result_path, output_dir=output_dir)

SWEEP_TOOLS = [
    {"name": "quick-sweep", "handler": quick_sweep},
]
