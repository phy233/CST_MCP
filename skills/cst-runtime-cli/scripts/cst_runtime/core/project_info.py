"""project_info.py — offline project metadata reader via cst_project_info_reader.

Wraps CST's _cst_interface.cst_project_info_reader C extension so that all
direct CST API access stays within the core/ layer.  No DE process required.
"""
from __future__ import annotations

from typing import Any

from .errors import error_response
from .utils import abs_project_path as _abs_project_path


def read_project_info(project_path: str) -> dict[str, Any]:
    """Read project metadata from a .cst file without starting a DE process.

    Returns a dict with:
        status, entities, entities_count, solver_name, min_frequency,
        max_frequency, frequency_unit, cst_version
    """
    normalized = _abs_project_path(project_path)
    try:
        from _cst_interface import cst_project_info_reader as pir
    except Exception as exc:
        return error_response(
            "pir_import_failed",
            f"cst_project_info_reader unavailable: {exc}",
            project_path=normalized,
            runtime_module="cst_runtime.core.project_info",
        )

    try:
        uri = pir.get_document_uri_for_file(normalized)
        explorer = pir.CSTProjectPropertiesExplorer(uri)
        data = explorer.get_project_data()

        entities: list[dict[str, str]] = []
        for bname in (data.block_names or []):
            parts = str(bname).split(":", 1)
            component = parts[0] if len(parts) > 1 else ""
            name = parts[1] if len(parts) > 1 else parts[0]
            entities.append({"component": component, "name": name})

        return {
            "status": "success",
            "project_path": normalized,
            "entities": entities,
            "entities_count": len(entities),
            "solver_name": data.active_solver_name or "",
            "min_frequency": data.min_frequency,
            "max_frequency": data.max_frequency,
            "frequency_unit": str(data.frequency_unit) if data.is_frequency_unit_set else "",
            "cst_version": data.full_version_string or "",
            "runtime_module": "cst_runtime.core.project_info",
        }
    except Exception as exc:
        return error_response(
            "read_project_info_failed",
            str(exc),
            project_path=normalized,
            runtime_module="cst_runtime.core.project_info",
        )
