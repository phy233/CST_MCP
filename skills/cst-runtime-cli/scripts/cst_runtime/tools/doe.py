from __future__ import annotations

from typing import Any

from ..lib import doe as _doe
from . import _register_tool_defs


_register_tool_defs({
    "design-probes": {
        "category": "optimization",
        "risk": "read",
        "description": (
            "Use this to generate a Plackett-Burman parameter-screening plan without "
            "running CST. Evaluate the returned experiments with prepare-experiment and "
            "run-experiment, then pass parameter and objective values to analyze-probes."
        ),
        "handler": "tool_design_probes",
        "json_schema": {
        "type": "object",
        "properties": {
            "parameters": {
                "type": "object",
                "examples": [
                    {
                        "R": {
                            "min": 0.1,
                            "max": 0.5
                        },
                        "g": {
                            "min": 20,
                            "max": 30
                        },
                        "L": {
                            "min": 100,
                            "max": 150
                        }
                    }
                ]
            },
            "max_probes": {
                "type": "integer",
                "examples": [
                    12
                ]
            },
            "include_center": {
                "type": "boolean",
                "examples": [
                    True
                ]
            }
        },
        "required": [
            "parameters",
            "max_probes",
            "include_center"
        ]
    },
    },
    "analyze-probes": {
        "category": "optimization",
        "risk": "read",
        "description": (
            "Use this to analyze completed probe data offline and estimate main effects and "
            "two-way interactions. Each probe must include its parameter values and objective; "
            "this tool neither runs CST nor asks or updates an Optuna study."
        ),
        "handler": "tool_analyze_probes",
        "json_schema": {
        "type": "object",
        "properties": {
            "parameters": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "examples": [
                    [
                        "R",
                        "g",
                        "L"
                    ]
                ]
            },
            "probes": {
                "type": "array",
                "items": {
                    "type": "object"
                },
                "examples": [
                    [
                        {
                            "params": {
                                "R": 0.1,
                                "g": 20,
                                "L": 100
                            },
                            "value": -28.7
                        },
                        {
                            "params": {
                                "R": 0.5,
                                "g": 30,
                                "L": 150
                            },
                            "value": -26.3
                        }
                    ]
                ]
            }
        },
        "required": [
            "parameters",
            "probes"
        ]
    },
    },
})


def tool_design_probes(args: dict) -> dict:
    return _doe.design_probes(
        parameters=args.get("parameters", {}),
        max_probes=int(args.get("max_probes", 12)),
        include_center=bool(args.get("include_center", True)),
    )


def tool_analyze_probes(args: dict) -> dict:
    return _doe.analyze_probes(
        parameters=args.get("parameters", []),
        probes=args.get("probes", []),
    )
