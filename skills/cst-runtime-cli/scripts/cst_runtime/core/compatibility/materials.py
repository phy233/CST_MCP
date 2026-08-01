from __future__ import annotations

from typing import Any

from .execution import execute_text_query


def list_material_names(project: Any) -> list[str]:
    """使用 CST 2022 Material VBA 对象按零基索引枚举工程材料。"""
    output = execute_text_query(
        project,
        [
            "Dim cstRtMaterialCount As Long",
            "Dim cstRtMaterialIndex As Long",
            "cstRtMaterialCount = Material.GetNumberOfMaterials",
            "For cstRtMaterialIndex = 0 To cstRtMaterialCount - 1",
            "Print #cstRtQueryFile, Material.GetNameOfMaterialFromIndex(cstRtMaterialIndex)",
            "Next cstRtMaterialIndex",
        ],
    )
    names: list[str] = []
    seen: set[str] = set()
    for line in output:
        name = line.strip()
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


__all__ = ["list_material_names"]
