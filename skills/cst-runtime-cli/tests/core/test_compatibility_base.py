from __future__ import annotations

from cst_runtime.core.compatibility import base


def test_profile_can_be_detected_from_explicit_runtime_version(monkeypatch):
    monkeypatch.setenv("CST_RUNTIME_CST_VERSION", "2022.0")
    base.reset_profile_cache()

    profile = base.detect_compatibility_profile()

    assert profile.label == "cst2022"
    assert profile.supports("project_path")
    assert not profile.supports("project_path_name")
    base.reset_profile_cache()


def test_unknown_profile_does_not_guess_vba_capabilities(monkeypatch):
    monkeypatch.delenv("CST_RUNTIME_CST_VERSION", raising=False)
    monkeypatch.setattr(base, "_extract_year", lambda _value: None)
    base.reset_profile_cache()

    profile = base.detect_compatibility_profile()

    assert profile.label == "unknown"
    assert not profile.supports("project_path")
    assert not profile.supports("project_path_name")
    base.reset_profile_cache()


def test_unsupported_feature_uses_compatibility_error_contract(monkeypatch):
    monkeypatch.setenv("CST_RUNTIME_CST_VERSION", "2022")
    base.reset_profile_cache()

    response = base.unsupported_feature(
        "mesh.fpbavoid_nonreg_unite",
        required_capability="mesh.fpbavoid_nonreg_unite",
        unsupported_arguments=["enable"],
    ).to_response()

    assert response["error_type"] == "unsupported_feature"
    assert response["error"]["phase"] == "compatibility"
    assert response["context"]["detected_version"] == "2022"
    assert response["context"]["unsupported_arguments"] == ["enable"]
    base.reset_profile_cache()
