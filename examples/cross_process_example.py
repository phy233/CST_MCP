"""Example: Cross-shaped unit cell parameter sweep.

This example demonstrates how to use the CrossProcessSweep class
to perform parameter sweep for cross-shaped metasurface unit cells.
"""
import logging
import numpy as np
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Import cross_process module
from cst_runtime.lib.cross_process import CrossProcessSweep, quick_cross_sweep


def example_cross_sweep():
    """Example: Cross-shaped unit cell parameter sweep."""

    # Define project path
    project_path = "C:\\path\\to\\your\\cross_unit.cst"

    # Define parameter ranges (similar to MATLAB: 3:0.4:10.5)
    lx_range = np.arange(3.0, 10.5, 0.4)
    ly1_range = np.arange(3.0, 10.5, 0.4)

    # Create sweep object
    sweep = CrossProcessSweep(
        project_path=project_path,
        lx_range=lx_range,
        ly1_range=ly1_range,
        target_freq_ghz=8.0,
    )

    # Run sweep
    results = sweep.run(output_dir="C:\\results\\cross_sweep")

    # Print results summary
    print("\n" + "=" * 60)
    print("Cross-shaped Unit Cell Parameter Sweep Results")
    print("=" * 60)
    print(f"\nProject: {project_path}")
    print(f"Target frequency: 8.0 GHz")
    print(f"\nParameter ranges:")
    print(f"  lx: {lx_range[0]:.1f} to {lx_range[-1]:.1f} mm ({len(lx_range)} points)")
    print(f"  ly1: {ly1_range[0]:.1f} to {ly1_range[-1]:.1f} mm ({len(ly1_range)} points)")
    print(f"\nSweep statistics:")
    print(f"  Total steps: {results.total_steps}")
    print(f"  Successful: {results.successful_steps}")
    print(f"  Failed: {results.failed_steps}")
    print(f"  Time: {results.sweep_time:.1f} s")
    print(f"  Output: {results.output_dir}")

    # Display LUT
    print(f"\nLUT shape: {results.lut.shape}")
    print(f"\nLUT columns: {list(results.lut.columns)}")
    print(f"\nLUT head:")
    print(results.lut.head(10))

    # Find best parameters (minimum Y-polarization magnitude)
    y_mag_col = [c for c in results.lut.columns if "Y_pol" in c and "mag_db" in c.lower()]
    if y_mag_col:
        col = y_mag_col[0]
        min_idx = results.lut[col].idxmin()
        min_row = results.lut.loc[min_idx]

        print(f"\nBest parameters (minimum Y-polarization):")
        print(f"  lx: {min_row['lx']:.4f} mm")
        print(f"  ly1: {min_row['ly1']:.4f} mm")
        print(f"  Y-pol magnitude: {min_row[col]:.2f} dB")

    return results


def example_quick_cross_sweep():
    """Example: Quick cross sweep with simplified interface."""

    # Define parameter ranges
    parameters = {
        "lx": np.arange(3.0, 10.5, 0.4),
        "ly1": np.arange(3.0, 10.5, 0.4),
    }

    # Run quick sweep
    results = quick_cross_sweep(
        project_path="C:\\path\\to\\your\\cross_unit.cst",
        lx_range=parameters["lx"],
        ly1_range=parameters["ly1"],
        target_freq_ghz=8.0,
        output_dir="C:\\results\\quick_cross_sweep",
    )

    print(f"\nQuick cross sweep completed: {results.successful_steps}/{results.total_steps}")
    return results


def example_custom_result_paths():
    """Example: Custom result paths for different S-parameters."""

    # Define project path
    project_path = "C:\\path\\to\\your\\cross_unit.cst"

    # Define parameter ranges
    lx_range = np.arange(3.0, 10.5, 1.0)  # Larger step for faster example
    ly1_range = np.arange(3.0, 10.5, 1.0)

    # Custom result paths (e.g., for different port configurations)
    y_pol_path = "1D Results\\S-Parameters\\SZmax(1),Zmax(1)"
    x_pol_path = "1D Results\\S-Parameters\\SZmax(2),Zmax(2)"

    # Create sweep with custom paths
    sweep = CrossProcessSweep(
        project_path=project_path,
        lx_range=lx_range,
        ly1_range=ly1_range,
        target_freq_ghz=8.0,
        y_polarization_path=y_pol_path,
        x_polarization_path=x_pol_path,
    )

    results = sweep.run()
    return results


def example_with_analysis():
    """Example: Sweep with post-sweep analysis."""

    # Run sweep
    results = example_cross_sweep()

    # Analyze results
    print("\n" + "=" * 60)
    print("Post-Sweep Analysis")
    print("=" * 60)

    # Find columns
    y_mag_col = [c for c in results.lut.columns if "Y_pol" in c and "mag_db" in c.lower()]
    x_mag_col = [c for c in results.lut.columns if "X_pol" in c and "mag_db" in c.lower()]

    if y_mag_col and x_mag_col:
        y_col = y_mag_col[0]
        x_col = x_mag_col[0]

        # Statistics
        print(f"\nY-polarization statistics:")
        print(f"  Mean: {results.lut[y_col].mean():.2f} dB")
        print(f"  Std: {results.lut[y_col].std():.2f} dB")
        print(f"  Min: {results.lut[y_col].min():.2f} dB")
        print(f"  Max: {results.lut[y_col].max():.2f} dB")

        print(f"\nX-polarization statistics:")
        print(f"  Mean: {results.lut[x_col].mean():.2f} dB")
        print(f"  Std: {results.lut[x_col].std():.2f} dB")
        print(f"  Min: {results.lut[x_col].min():.2f} dB")
        print(f"  Max: {results.lut[x_col].max():.2f} dB")

        # Find parameters with minimum S11 for both polarizations
        y_min_idx = results.lut[y_col].idxmin()
        x_min_idx = results.lut[x_col].idxmin()

        print(f"\nBest parameters for Y-polarization:")
        print(f"  lx: {results.lut.loc[y_min_idx, 'lx']:.4f} mm")
        print(f"  ly1: {results.lut.loc[y_min_idx, 'ly1']:.4f} mm")
        print(f"  Magnitude: {results.lut.loc[y_min_idx, y_col]:.2f} dB")

        print(f"\nBest parameters for X-polarization:")
        print(f"  lx: {results.lut.loc[x_min_idx, 'lx']:.4f} mm")
        print(f"  ly1: {results.lut.loc[x_min_idx, 'ly1']:.4f} mm")
        print(f"  Magnitude: {results.lut.loc[x_min_idx, x_col]:.2f} dB")

        # Find parameters with balanced performance
        results.lut["combined"] = (results.lut[y_col] + results.lut[x_col]) / 2
        combined_min_idx = results.lut["combined"].idxmin()

        print(f"\nBest balanced parameters:")
        print(f"  lx: {results.lut.loc[combined_min_idx, 'lx']:.4f} mm")
        print(f"  ly1: {results.lut.loc[combined_min_idx, 'ly1']:.4f} mm")
        print(f"  Y-pol: {results.lut.loc[combined_min_idx, y_col]:.2f} dB")
        print(f"  X-pol: {results.lut.loc[combined_min_idx, x_col]:.2f} dB")
        print(f"  Combined: {results.lut.loc[combined_min_idx, 'combined']:.2f} dB")


if __name__ == "__main__":
    print("=" * 60)
    print("Cross-shaped Unit Cell Parameter Sweep Examples")
    print("=" * 60)

    # Uncomment to run:
    # results = example_cross_sweep()
    # results = example_quick_cross_sweep()
    # results = example_custom_result_paths()
    # example_with_analysis()

    print("\nNote: Uncomment the examples above to run them.")
    print("Make sure to update the project_path to your actual CST project.")
