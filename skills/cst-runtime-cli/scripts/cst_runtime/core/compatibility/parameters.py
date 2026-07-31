from __future__ import annotations

from typing import Any
from ..errors import UnsupportedFeatureError


def supports_parameter_api(project: Any) -> bool:
    """
    Checks if the CST version supports direct reading of parameters
    via the new COM API (project.model3d).
    """
    return hasattr(project, "model3d")


def _parameter_object(project: Any) -> Any:
    """按新旧版本顺序取得参数 API 对象。"""
    candidates = [
        getattr(project, "model3d", None),
        getattr(project, "modeler", None),
        project,
    ]
    for candidate in candidates:
        if candidate is not None and hasattr(candidate, "GetNumberOfParameters"):
            return candidate
    raise UnsupportedFeatureError("当前 CST 会话未提供可用的参数枚举 API")


def list_parameter_values(project: Any) -> dict[str, Any]:
    """屏蔽 CST 2022/2026 参数对象位置和读取方法差异。"""
    parameter_api = _parameter_object(project)
    parameters: dict[str, Any] = {}
    for index in range(int(parameter_api.GetNumberOfParameters())):
        name = str(parameter_api.GetParameterName(index))
        value: Any = None
        for method_name in (
            "RestoreDoubleParameter",
            "GetParameterValue",
            "RestoreParameter",
        ):
            method = getattr(parameter_api, method_name, None)
            if not callable(method):
                continue
            try:
                value = method(name)
                break
            except Exception:
                continue
        parameters[name] = value
    return parameters
