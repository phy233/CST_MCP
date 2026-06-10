"""Example unit cell implementations.

This file demonstrates how to create custom unit cell classes by inheriting
from UnitCellBase. Users should create their own files for their specific
unit cell designs.

Usage:
    from my_unit_cells import CRingCell, CrossCell

    cell = CRingCell()
    cell.code_modeling("C:\\model.cst", code=0, center=(0, 0, 0), name="unit_0_0")
"""
from cst_runtime.lib.unit_cells import UnitCellBase
from cst_runtime.lib.geometry import brick, cylinder, boolean_subtract, boolean_add


class CRingCell(UnitCellBase):
    """C-ring (slit ring) unit cell example.

    This is an example implementation. Modify parameters and geometry
    creation logic for your specific design.
    """
    name = "c_ring"
    codes = [0, 1, 2, 3]  # 2-bit encoding
    params = {
        0: {"outer_r": 2.0, "inner_r": 1.5, "gap_angle": 0},
        1: {"outer_r": 2.0, "inner_r": 1.5, "gap_angle": 30},
        2: {"outer_r": 2.0, "inner_r": 1.5, "gap_angle": 60},
        3: {"outer_r": 2.0, "inner_r": 1.5, "gap_angle": 90},
    }

    def code_modeling(
        self,
        project_path: str,
        code: int,
        center: tuple[float, float, float],
        name: str,
    ) -> None:
        """Create C-ring unit cell geometry.

        Args:
            project_path: Path to .cst file
            code: Encoding value (0-3)
            center: (x, y, z) center position
            name: Unit cell name

        Raises:
            ValueError: If code is not supported
            RuntimeError: If geometry cannot be created
        """
        self.validate_code(code)
        p = self.get_params(code)

        # Create outer cylinder
        cylinder(
            project_path,
            component="component1",
            name=f"{name}_outer",
            material="PEC",
            axis="z",
            center=(center[0], center[1]),
            radius=p["outer_r"],
            z_range=(center[2], center[2] + 0.1),
        )

        # Create inner cylinder (to subtract)
        cylinder(
            project_path,
            component="component1",
            name=f"{name}_inner",
            material="PEC",
            axis="z",
            center=(center[0], center[1]),
            radius=p["inner_r"],
            z_range=(center[2], center[2] + 0.1),
        )

        # Boolean subtract to create ring
        boolean_subtract(
            project_path,
            target=f"component1:{name}_outer",
            tool=f"component1:{name}_inner",
        )

        # NOTE: Gap creation is simplified here
        # For actual gap, need to create a wedge and subtract
        if p["gap_angle"] > 0:
            # Implement gap geometry here
            pass


class CrossCell(UnitCellBase):
    """I-shaped (cross) unit cell example.

    This is an example implementation. Modify parameters and geometry
    creation logic for your specific design.
    """
    name = "cross"
    codes = [0, 1, 2, 3]  # 2-bit encoding
    params = {
        0: {"arm_length": 3.0, "arm_width": 0.5},
        1: {"arm_length": 3.0, "arm_width": 0.8},
        2: {"arm_length": 3.0, "arm_width": 1.0},
        3: {"arm_length": 3.0, "arm_width": 1.2},
    }

    def code_modeling(
        self,
        project_path: str,
        code: int,
        center: tuple[float, float, float],
        name: str,
    ) -> None:
        """Create Cross unit cell geometry.

        Args:
            project_path: Path to .cst file
            code: Encoding value (0-3)
            center: (x, y, z) center position
            name: Unit cell name

        Raises:
            ValueError: If code is not supported
            RuntimeError: If geometry cannot be created
        """
        self.validate_code(code)
        p = self.get_params(code)

        thickness = 0.1  # mm

        # Create horizontal arm
        brick(
            project_path,
            component="component1",
            name=f"{name}_h",
            material="PEC",
            x_range=(center[0] - p["arm_length"] / 2, center[0] + p["arm_length"] / 2),
            y_range=(center[1] - p["arm_width"] / 2, center[1] + p["arm_width"] / 2),
            z_range=(center[2], center[2] + thickness),
        )

        # Create vertical arm
        brick(
            project_path,
            component="component1",
            name=f"{name}_v",
            material="PEC",
            x_range=(center[0] - p["arm_width"] / 2, center[0] + p["arm_width"] / 2),
            y_range=(center[1] - p["arm_length"] / 2, center[1] + p["arm_length"] / 2),
            z_range=(center[2], center[2] + thickness),
        )

        # Boolean add to create cross
        boolean_add(
            project_path,
            shape1=f"component1:{name}_h",
            shape2=f"component1:{name}_v",
        )
