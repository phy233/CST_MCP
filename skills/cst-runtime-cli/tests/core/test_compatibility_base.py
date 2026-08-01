from __future__ import annotations

from cst_runtime.core.compatibility import base


def test_extract_year_prefers_native_cst_release_over_wrapper_date():
    version_info = {
        "cst.results": {
            "Version": "2021-06-30",
            "File": "D:/CST Studio Suite 2022/python_cst_libraries/cst/results.py",
        },
        "_cst_results": {
            "Version": "2022.5 Release from 2022-06-03",
            "File": "D:/CST Studio Suite 2022/_cst_results.pyd",
        },
    }

    assert base._extract_year(version_info) == (
        2022,
        "2022.5 Release from 2022-06-03",
    )


def test_extract_year_does_not_treat_plain_date_as_product_version():
    assert base._extract_year("2021-06-30") is None


def test_extract_year_supports_cst_installation_path():
    path = "D:/Program Files/CST Studio Suite 2022/AMD64/python_cst_libraries"

    assert base._extract_year(path) == (2022, path)


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
