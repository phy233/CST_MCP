"""超表面离线后处理工具定义。"""
from __future__ import annotations

from . import _register_tool_defs
from ..lib import metasurface as _metasurface


_CHANNEL = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "file_path": {"type": "string", "minLength": 1},
        "kind": {"type": "string", "enum": ["reflection", "transmission"]},
        "polarization": {"type": "string", "enum": ["co", "cross"]},
        "include_in_total_power": {"type": "boolean", "default": True},
    },
    "required": ["name", "file_path", "kind", "polarization"],
}
_TARGET_PHASE = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "channel": {"type": "string", "minLength": 1},
        "frequency_ghz": {"type": "number"},
        "phase_deg": {"type": "number"},
    },
    "required": ["channel", "frequency_ghz", "phase_deg"],
}


TOOL_DEFS = {
    "analyze-metasurface-sparameters": {
        "category": "results",
        "risk": "filesystem-write",
        "description": (
            "Use this to perform offline multi-channel metasurface S-parameter analysis "
            "from existing export-sparameter JSON files and write a nonempty analysis JSON. "
            "It does not call CST; R/T/A channel summation and phase-reference behavior "
            "remain the documented current implementation and are not corrected by this tool."
        ),
        "handler": "tool_analyze_metasurface_sparameters",
        "json_schema": {
            "type": "object",
            "properties": {
                "channels": {"type": "array", "minItems": 1, "items": _CHANNEL},
                "target_phases": {"type": "array", "items": _TARGET_PHASE, "default": []},
                "passivity_tolerance": {"type": "number", "minimum": 0, "default": 1e-6},
                "output_path": {"type": "string", "minLength": 1},
            },
            "required": ["channels", "output_path"],
        },
    }
}


def tool_analyze_metasurface_sparameters(args: dict) -> dict:
    return _metasurface.analyze_metasurface_sparameters(
        channels=args["channels"],
        target_phases=args.get("target_phases", []),
        passivity_tolerance=args.get("passivity_tolerance", 1e-6),
        output_path=args["output_path"],
    )


_register_tool_defs(TOOL_DEFS)
