"""tell-study / create-study Schema 契约的离线单测。

覆盖 P0-3：
- json_schema 通过 Draft7 check_schema；
- tell-study 的 value XOR values 语义；
- create-study 必填收敛与 parameters 双形态；
- handler 层守卫（direction 冲突、state 非法、value/values 均缺）。
"""
from __future__ import annotations

from jsonschema import Draft7Validator

from cst_runtime.tools import all_defs
from cst_runtime.tools.optimization import tool_create_study, tool_tell_study

TELL_BASE = {
    "storage_path": "C:/x/opt.db",
    "study_name": "study_x",
    "trial_number": 1,
}
CREATE_BASE = {
    "storage_path": "C:/x/opt.db",
    "study_name": "study_x",
}


class TestSchemaContract:

    def test_optimization_schemas_are_valid_draft7(self):
        names = {
            "create-study", "ask-study", "tell-study", "best-study",
            "study-add-trials", "study-param-importances",
            "study-terminate-check", "run-probe-phase", "run-optimization-step",
        }
        defs = all_defs()
        assert names <= set(defs)
        for name in sorted(names):
            Draft7Validator.check_schema(defs[name]["json_schema"])

    def test_tell_study_requires_only_core_fields(self):
        required = all_defs()["tell-study"]["json_schema"]["required"]
        assert set(required) == {"storage_path", "study_name", "trial_number"}

    def test_create_study_requires_only_core_fields(self):
        required = all_defs()["create-study"]["json_schema"]["required"]
        assert set(required) == {"storage_path", "study_name", "parameters"}

    def test_tell_value_xor_values(self):
        validator = Draft7Validator(all_defs()["tell-study"]["json_schema"])
        assert validator.is_valid({**TELL_BASE, "value": -35.5})
        assert validator.is_valid({**TELL_BASE, "values": [-35.5, 12.3]})
        assert not validator.is_valid({**TELL_BASE, "value": -35.5, "values": [-35.5]})
        assert not validator.is_valid(dict(TELL_BASE))

    def test_tell_state_enum(self):
        state = all_defs()["tell-study"]["json_schema"]["properties"]["state"]
        assert state["enum"] == ["complete", "pruned"]
        assert state["default"] == "complete"

    def test_create_parameters_accepts_object_and_string(self):
        schema = all_defs()["create-study"]["json_schema"]
        validator = Draft7Validator(schema)
        assert validator.is_valid({
            **CREATE_BASE,
            "parameters": {"R": {"type": "float", "min": 0.1, "max": 0.5}},
        })
        assert validator.is_valid({
            **CREATE_BASE,
            "parameters": '{"R": {"type": "float", "min": 0.1}}',
        })
        assert not validator.is_valid(dict(CREATE_BASE))


class TestHandlerGuards:

    def test_create_rejects_conflicting_directions(self):
        result = tool_create_study({
            **CREATE_BASE,
            "parameters": {},
            "direction": "minimize",
            "directions": ["maximize"],
        })
        assert result["status"] == "error"
        assert result["error_type"] == "invalid_arguments"

    def test_tell_rejects_missing_value_and_values(self):
        result = tool_tell_study(dict(TELL_BASE))
        assert result["status"] == "error"
        assert result["error_type"] == "invalid_arguments"

    def test_tell_rejects_invalid_state(self):
        result = tool_tell_study({**TELL_BASE, "value": -1.0, "state": "fail"})
        assert result["status"] == "error"
        assert result["error_type"] == "invalid_arguments"
