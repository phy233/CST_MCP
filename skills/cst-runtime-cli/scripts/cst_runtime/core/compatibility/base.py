from __future__ import annotations

from typing import Any
from ..errors import UnsupportedFeatureError


def get_model3d(project: Any) -> Any:
    """Gets project.model3d if available, otherwise raises UnsupportedFeatureError."""
    if not hasattr(project, "model3d"):
        raise UnsupportedFeatureError("The 'model3d' API is not supported in this version of CST (requires CST 2023+).")
    return project.model3d
