"""超表面工具注册、严格 Schema 与暴露级别测试。"""
from __future__ import annotations

from jsonschema import ValidationError, validate
import pytest

from cst_runtime.api.atomic import atomic_definitions


NEW_TOOLS = {
    "define-unit-cell-boundary",
    "define-floquet-port",
    "define-plane-wave",
    "configure-frequency-domain-solver",
    "inspect-boundary",
    "inspect-floquet-ports",
    "inspect-plane-wave",
    "list-monitors",
    "analyze-metasurface-sparameters",
}


def test_all_new_tools_are_registered_for_agent() -> None:
    definitions = {item["name"]: item for item in atomic_definitions()}
    assert NEW_TOOLS <= definitions.keys()
    assert {definitions[name]["exposure"] for name in NEW_TOOLS} == {"agent"}
    assert "inspect-solver-settings" not in definitions


def test_top_level_schemas_reject_unknown_fields() -> None:
    definitions = {item["name"]: item for item in atomic_definitions()}
    for name in NEW_TOOLS:
        schema = definitions[name]["input_schema"]
        assert schema["additionalProperties"] is False


def test_nested_floquet_schema_rejects_unknown_fields() -> None:
    definitions = {item["name"]: item for item in atomic_definitions()}
    schema = definitions["define-floquet-port"]["input_schema"]
    payload = {
        "project_path": "model.cst",
        "ports": [{
            "position": "Zmin",
            "mode_strategy": "explicit",
            "modes_considered": 1,
            "reference_distance": 0,
            "modes": [{"type": "TE", "order_x": 0, "order_yprime": 0, "unknown": 1}],
        }],
    }
    with pytest.raises(ValidationError):
        validate(payload, schema)


def test_solver_schema_only_exposes_mesh_and_excitation() -> None:
    definitions = {item["name"]: item for item in atomic_definitions()}
    properties = definitions["configure-frequency-domain-solver"]["input_schema"]["properties"]
    assert set(properties) == {"project_path", "mesh_method", "excitation"}
    assert not ({"accuracy", "sweep", "adaptive_mesh", "convergence"} & properties.keys())


def test_analysis_output_schema_contains_non_empty_file_evidence() -> None:
    definitions = {item["name"]: item for item in atomic_definitions()}
    properties = definitions["analyze-metasurface-sparameters"]["output_schema"]["properties"]
    assert properties["file_size"]["minimum"] == 1
    assert "summary" in properties
    assert "warning_count" in properties
