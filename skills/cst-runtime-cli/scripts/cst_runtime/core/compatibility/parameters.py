"""参数枚举的 COM 优先、即时 VBA 回退实现。"""
from __future__ import annotations

from typing import Any

from .execution import execute_text_query


def supports_parameter_api(project: Any) -> bool:
    return _parameter_object(project) is not None


def _parameter_object(project: Any) -> Any | None:
    for candidate in (
        getattr(project, "model3d", None),
        getattr(project, "modeler", None),
        project,
    ):
        if candidate is not None and callable(getattr(candidate, "GetNumberOfParameters", None)):
            return candidate
    return None


def _coerce_parameter_value(expression: str, numeric: Any) -> Any:
    expression = str(expression or "").strip()
    try:
        numeric_value = float(numeric)
    except (TypeError, ValueError):
        numeric_value = None
    if expression:
        try:
            expression_number = float(expression)
        except ValueError:
            return expression
        if numeric_value is None:
            return expression_number
    if numeric_value is not None:
        return numeric_value
    return expression or numeric


def _read_parameter(parameter_api: Any, name: str) -> Any:
    expression: Any = ""
    expression_getter = getattr(parameter_api, "RestoreParameterExpression", None)
    if callable(expression_getter):
        try:
            expression = expression_getter(name)
        except Exception:
            expression = ""
    numeric: Any = None
    for method_name in ("RestoreDoubleParameter", "GetParameterValue", "RestoreParameter"):
        method = getattr(parameter_api, method_name, None)
        if callable(method):
            try:
                numeric = method(name)
                break
            except Exception:
                continue
    return _coerce_parameter_value(str(expression or ""), numeric)


def _list_parameters_via_vba(project: Any) -> dict[str, Any]:
    lines = execute_text_query(
        project,
        [
            "Dim cstRtIndex As Long",
            "Dim cstRtName As String",
            "Dim cstRtExpression As String",
            "Dim cstRtValue As Double",
            "For cstRtIndex = 0 To GetNumberOfParameters() - 1",
            "cstRtName = GetParameterName(cstRtIndex)",
            "cstRtExpression = \"\"",
            "cstRtValue = 0",
            "On Error Resume Next",
            "cstRtExpression = RestoreParameterExpression(cstRtName)",
            "Err.Clear",
            "cstRtValue = RestoreDoubleParameter(cstRtName)",
            "On Error GoTo 0",
            'cstRtName = Replace(Replace(Replace(cstRtName, vbTab, " "), vbCr, " "), vbLf, " ")',
            'cstRtExpression = Replace(Replace(Replace(cstRtExpression, vbTab, " "), vbCr, " "), vbLf, " ")',
            "Print #cstRtQueryFile, cstRtName & vbTab & cstRtExpression & vbTab & CStr(cstRtValue)",
            "Next cstRtIndex",
        ],
    )
    parameters: dict[str, Any] = {}
    for line in lines:
        fields = line.split("\t", 2)
        if not fields or not fields[0]:
            continue
        expression = fields[1] if len(fields) > 1 else ""
        numeric = fields[2] if len(fields) > 2 else None
        parameters[fields[0]] = _coerce_parameter_value(expression, numeric)
    return parameters


def list_parameter_values(project: Any) -> dict[str, Any]:
    """枚举工程参数；无可调用 Python 对象时自动使用 CST 2022 VBA。"""
    parameter_api = _parameter_object(project)
    if parameter_api is None:
        return _list_parameters_via_vba(project)
    parameters: dict[str, Any] = {}
    for index in range(int(parameter_api.GetNumberOfParameters())):
        name = str(parameter_api.GetParameterName(index))
        parameters[name] = _read_parameter(parameter_api, name)
    return parameters


__all__ = ["list_parameter_values", "supports_parameter_api"]
