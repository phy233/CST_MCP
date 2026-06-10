"""CST unit cell abstract base class.

This module provides the abstract interface for unit cell parameterization.
Users should inherit from UnitCellBase and implement the code_modeling method
for their specific unit cell geometry.

Usage Example:
    from cst_runtime.lib.unit_cells import UnitCellBase
    from cst_runtime.lib.geometry import brick, cylinder, boolean_subtract

    class MyCRingCell(UnitCellBase):
        name = "c_ring"
        codes = [0, 1, 2, 3]
        params = {
            0: {"outer_r": 2.0, "inner_r": 1.5, "gap_angle": 0},
            1: {"outer_r": 2.0, "inner_r": 1.5, "gap_angle": 30},
            2: {"outer_r": 2.0, "inner_r": 1.5, "gap_angle": 60},
            3: {"outer_r": 2.0, "inner_r": 1.5, "gap_angle": 90},
        }

        def code_modeling(self, project_path, code, center, name):
            p = self.params[code]
            # Implement your geometry creation here
            cylinder(project_path, component="component1",
                    name=f"{name}_outer", material="PEC",
                    axis="z", center=(center[0], center[1]),
                    radius=p["outer_r"],
                    z_range=(center[2], center[2] + 0.1))
            # ...

    # Usage
    cell = MyCRingCell()
    cell.code_modeling("C:\\model.cst", code=0, center=(0, 0, 0), name="unit_0_0")
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class UnitCellBase(ABC):
    """Unit cell parameterized base class.

    Subclasses must define:
        name (str): Unit cell type name
        codes (list[int]): Supported encoding values
        params (dict[int, dict]): Geometry parameters for each code
        code_modeling(): Method to create geometry for a given code

    Example:
        class CrossCell(UnitCellBase):
            name = "cross"
            codes = [0, 1, 2, 3]
            params = {
                0: {"arm_length": 3.0, "arm_width": 0.5},
                1: {"arm_length": 3.0, "arm_width": 0.8},
                # ...
            }

            def code_modeling(self, project_path, code, center, name):
                from cst_runtime.lib.geometry import brick, boolean_add
                p = self.params[code]
                # Create horizontal arm
                brick(project_path, "component1", f"{name}_h", "PEC",
                      x_range=(center[0] - p["arm_length"]/2, center[0] + p["arm_length"]/2),
                      y_range=(center[1] - p["arm_width"]/2, center[1] + p["arm_width"]/2),
                      z_range=(center[2], center[2] + 0.1))
                # Create vertical arm
                brick(project_path, "component1", f"{name}_v", "PEC",
                      x_range=(center[0] - p["arm_width"]/2, center[0] + p["arm_width"]/2),
                      y_range=(center[1] - p["arm_length"]/2, center[1] + p["arm_length"]/2),
                      z_range=(center[2], center[2] + 0.1))
                # Boolean add
                boolean_add(project_path, f"component1:{name}_h", f"component1:{name}_v")
    """
    name: str
    codes: list[int]
    params: dict[int, dict[str, Any]]

    @abstractmethod
    def code_modeling(
        self,
        project_path: str,
        code: int,
        center: tuple[float, float, float],
        name: str,
    ) -> None:
        """Create unit cell geometry based on code value.

        This method should be implemented by subclasses to create the
        specific geometry for the unit cell type.

        Args:
            project_path: Path to .cst file
            code: Encoding value (must be in self.codes)
            center: (x, y, z) center position in mm
            name: Unit cell name (must be unique within component)

        Raises:
            ValueError: If code is not in self.codes
            RuntimeError: If geometry cannot be created
        """
        ...

    def validate_code(self, code: int) -> None:
        """Validate that a code is supported.

        Args:
            code: Encoding value to validate

        Raises:
            ValueError: If code is not supported
        """
        if code not in self.codes:
            raise ValueError(
                f"Code {code} not supported for {self.name}. "
                f"Available codes: {self.codes}"
            )

    def get_params(self, code: int) -> dict[str, Any]:
        """Get parameters for a specific code.

        Args:
            code: Encoding value

        Returns:
            Parameter dictionary for the code

        Raises:
            ValueError: If code is not supported
        """
        self.validate_code(code)
        return self.params[code]
