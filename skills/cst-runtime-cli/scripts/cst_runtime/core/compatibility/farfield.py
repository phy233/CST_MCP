from __future__ import annotations

from typing import Any
from ..errors import UnsupportedFeatureError
from .base import get_model3d


def supports_farfield_calculator(project: Any) -> bool:
    """
    Checks if the CST version supports the new FarfieldCalculator API.
    """
    if not hasattr(project, "model3d"):
        return False
    # Additional check to ensure FarfieldCalculator exists on model3d could be added here
    # but for now, model3d existence implies CST 2023+ which supports it.
    return hasattr(project.model3d, "FarfieldCalculator")


def get_farfield_calculator(project: Any) -> Any:
    """Gets the FarfieldCalculator if available, otherwise raises UnsupportedFeatureError."""
    if not supports_farfield_calculator(project):
        raise UnsupportedFeatureError("FarfieldCalculator is not supported in this version of CST.")
    return project.model3d.FarfieldCalculator
