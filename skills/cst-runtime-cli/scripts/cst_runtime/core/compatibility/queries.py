"""工程级命令与查询的跨版本适配。"""
from __future__ import annotations

from typing import Any

from .base import compatibility_metadata
from .execution import execute_immediate_vba, execute_text_query


def delete_project_results(project: Any) -> dict[str, Any]:
    """删除结果，不要求 CST 2022 提供 model3d。"""
    for candidate in (getattr(project, "model3d", None), getattr(project, "modeler", None), project):
        method = getattr(candidate, "DeleteResults", None)
        if callable(method):
            method()
            return compatibility_metadata(project, path="common", transport="python_api")
    execute_immediate_vba(project, ["DeleteResults"])
    return compatibility_metadata(project, transport="immediate_vba")


def get_project_solver_type(project: Any) -> tuple[str, dict[str, Any]]:
    """读取求解器类型，不要求 CST 2022 提供 model3d。"""
    for candidate in (getattr(project, "model3d", None), getattr(project, "modeler", None), project):
        method = getattr(candidate, "GetSolverType", None)
        if callable(method):
            return str(method()), compatibility_metadata(project, path="common", transport="python_api")
    output = execute_text_query(project, ["Print #cstRtQueryFile, CStr(GetSolverType())"])
    return (output[0].strip() if output else ""), compatibility_metadata(
        project,
        transport="immediate_vba",
    )


__all__ = ["delete_project_results", "get_project_solver_type"]
