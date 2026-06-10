"""Example: Parameter sweep for CST simulation.

This example demonstrates how to use the parameter sweep functionality
to scan multiple parameters and build a lookup table (LUT).
"""
import logging
import numpy as np
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Import sweep module
from cst_runtime.lib.sweep import ParameterSweep, quick_sweep, load_lut


def example_basic_sweep():
    """Basic parameter sweep example."""

    # Define project path
    project_path = "C:\\path\\to\\your\\model.cst"

    # Define parameters to sweep
    parameters = ["lx", "ly1"]
    ranges = [
        np.arange(3.0, 10.5, 0.4),  # lx range
        np.arange(3.0, 10.5, 0.4),  # ly1 range
    ]

    # Create sweep object
    sweep = ParameterSweep(
        project_path=project_path,
        parameters=parameters,
        ranges=ranges,
        target_freq_ghz=8.0,
        result_paths=[
            "1D Results\\S-Parameters\\SZmax(1),Zmax(1)",
            "1D Results\\S-Parameters\\SZmax(2),Zmax(2)",
        ],
    )

    # Run sweep
    results = sweep.run(output_dir="C:\\results\\sweep_example")

    # Print results summary
    print(f"\nSweep completed:")
    print(f"  Total steps: {results.total_steps}")
    print(f"  Successful: {results.successful_steps}")
    print(f"  Failed: {results.failed_steps}")
    print(f"  Time: {results.sweep_time:.1f}s")
    print(f"  Output: {results.output_dir}")

    # Display LUT
    print(f"\nLUT shape: {results.lut.shape}")
    print(f"\nLUT head:")
    print(results.lut.head())

    return results


def example_quick_sweep():
    """Quick sweep with simplified interface."""

    # Define parameters as dict
    parameters = {
        "lx": np.arange(3.0, 10.5, 0.4),
        "ly1": np.arange(3.0, 10.5, 0.4),
    }

    # Run quick sweep
    results = quick_sweep(
        project_path="C:\\path\\to\\your\\model.cst",
        parameters=parameters,
        target_freq_ghz=8.0,
        result_path="1D Results\\S-Parameters\\S1,1",
        output_dir="C:\\results\\quick_sweep",
    )

    print(f"\nQuick sweep completed: {results.successful_steps}/{results.total_steps}")
    return results


def example_with_callback():
    """Sweep with callback function for progress monitoring."""

    def progress_callback(step: int, params: dict, results: dict):
        """Callback called after each simulation step."""
        print(f"\n--- Step {step} completed ---")
        print(f"  Parameters: {params}")
        for path, sparam in results.get("sparams", {}).items():
            if "error" not in sparam:
                print(f"  {path}: {sparam.get('magnitude_db', 0):.2f} dB")

    # Create sweep with callback
    sweep = ParameterSweep(
        project_path="C:\\path\\to\\your\\model.cst",
        parameters=["lx", "ly1"],
        ranges=[
            np.arange(3.0, 10.5, 1.0),  # Larger step for faster example
            np.arange(3.0, 10.5, 1.0),
        ],
        target_freq_ghz=8.0,
        callback=progress_callback,
    )

    results = sweep.run()
    return results


def example_load_and_analyze():
    """Load and analyze saved LUT."""

    # Load LUT from CSV
    lut_path = Path("C:\\results\\sweep_example\\lut.csv")
    if lut_path.exists():
        lut = load_lut(lut_path)

        print(f"\nLoaded LUT: {lut.shape}")
        print(f"\nColumns: {list(lut.columns)}")

        # Find minimum S11
        s11_col = [c for c in lut.columns if "mag_db" in c.lower()][0]
        min_idx = lut[s11_col].idxmin()
        min_row = lut.loc[min_idx]

        print(f"\nMinimum S11:")
        print(f"  Value: {min_row[s11_col]:.2f} dB")
        for param in ["lx", "ly1"]:
            if param in min_row:
                print(f"  {param}: {min_row[param]:.4f}")

        # Statistics
        print(f"\nStatistics:")
        print(f"  Mean: {lut[s11_col].mean():.2f} dB")
        print(f"  Std: {lut[s11_col].std():.2f} dB")
        print(f"  Min: {lut[s11_col].min():.2f} dB")
        print(f"  Max: {lut[s11_col].max():.2f} dB")

    else:
        print(f"LUT file not found: {lut_path}")


if __name__ == "__main__":
    # Run basic example
    print("=" * 60)
    print("Parameter Sweep Example")
    print("=" * 60)

    # Uncomment to run:
    # results = example_basic_sweep()
    # results = example_quick_sweep()
    # results = example_with_callback()
    # example_load_and_analyze()

    print("\nNote: Uncomment the examples above to run them.")
    print("Make sure to update the project_path to your actual CST project.")
