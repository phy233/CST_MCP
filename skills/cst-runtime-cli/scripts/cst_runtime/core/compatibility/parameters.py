from __future__ import annotations

from typing import Any
from ..errors import UnsupportedFeatureError


def supports_parameter_api(project: Any) -> bool:
    """
    Checks if the CST version supports direct reading of parameters
    via the new COM API (project.model3d).
    """
    return hasattr(project, "model3d")
