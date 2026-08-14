"""背景设置 VBA 生成与 get_background 查询解析的单元测试。"""
from __future__ import annotations

from types import SimpleNamespace

from cst_runtime.core.compatibility.base import CompatibilityProfile
from cst_runtime.core.compatibility.modeling import background_vba

_PROFILE_2022 = CompatibilityProfile(major=2022, version="2022.0", source="test")


def _lines(**kwargs):
    return background_vba(profile=_PROFILE_2022, **kwargs).lines


def test_background_vba_normal_defaults_to_vacuum_equivalent():
    lines = _lines()
    assert '    .Type "Normal"' in lines
    assert '    .Epsilon "1.0"' in lines
    assert '    .Mu "1.0"' in lines
    assert '    .ElConductivity "0"' in lines
    assert any(".Reset" in line for line in lines)


def test_background_vba_normal_honors_custom_material():
    lines = _lines(background_type="Normal", epsilon=2.2, mu=1.0)
    assert '    .Type "Normal"' in lines
    assert '    .Epsilon "2.2"' in lines
    assert '    .Mu "1.0"' in lines


def test_background_vba_pec_omits_material_lines():
    lines = _lines(background_type="PEC")
    assert '    .Type "PEC"' in lines
    assert not any(".Epsilon" in line for line in lines)
    assert not any(".Mu" in line for line in lines)


def test_background_vba_spaces_keeps_explicit_normal_type():
    lines = _lines(spaces=(30, 30, 30, 30, 50, 100))
    assert '    .Type "Normal"' in lines
    assert '    .Epsilon "1.0"' in lines
    assert '    .XminSpace "30"' in lines
    assert '    .ZmaxSpace "100"' in lines
    assert '    .ApplyInAllDirections "False"' in lines


def test_get_background_parses_query_and_flags_compatibility(monkeypatch):
    from cst_runtime.core import modeling

    monkeypatch.setattr(
        modeling,
        "attach_expected_project",
        lambda path: (SimpleNamespace(), None),
    )
    monkeypatch.setattr(
        modeling,
        "execute_text_query",
        lambda project, lines: [
            "Type=normal",
            "Epsilon=1.0",
            "Mu=1.0",
            "ElConductivity=0",
            "XminSpace=30",
            "XmaxSpace=30",
            "YminSpace=30",
            "YmaxSpace=30",
            "ZminSpace=50",
            "ZmaxSpace=100",
            "ApplyInAllDirections=False",
        ],
    )
    monkeypatch.setattr(
        modeling,
        "compatibility_metadata",
        lambda project: {"transport": "immediate_vba"},
    )

    result = modeling.get_background("C:/work/working.cst")

    assert result["status"] == "success"
    assert result["background_type"] == "normal"
    assert result["epsilon"] == 1.0
    assert result["mu"] == 1.0
    assert result["el_conductivity"] == 0
    assert result["spaces"]["zmax_space"] == 100.0
    assert result["apply_in_all_directions"] is False
    assert result["farfield_compatible"] is True


def test_get_background_flags_lossy_background(monkeypatch):
    from cst_runtime.core import modeling

    monkeypatch.setattr(
        modeling,
        "attach_expected_project",
        lambda path: (SimpleNamespace(), None),
    )
    monkeypatch.setattr(
        modeling,
        "execute_text_query",
        lambda project, lines: [
            "Type=normal",
            "Epsilon=4.3",
            "Mu=1.0",
            "ElConductivity=0",
        ],
    )
    monkeypatch.setattr(
        modeling,
        "compatibility_metadata",
        lambda project: {},
    )

    result = modeling.get_background("C:/work/working.cst")

    assert result["status"] == "success"
    assert result["farfield_compatible"] is False


def test_get_background_flags_pec(monkeypatch):
    from cst_runtime.core import modeling

    monkeypatch.setattr(
        modeling,
        "attach_expected_project",
        lambda path: (SimpleNamespace(), None),
    )
    monkeypatch.setattr(
        modeling,
        "execute_text_query",
        lambda project, lines: ["Type=pec"],
    )
    monkeypatch.setattr(
        modeling,
        "compatibility_metadata",
        lambda project: {},
    )

    result = modeling.get_background("C:/work/working.cst")

    assert result["status"] == "success"
    assert result["farfield_compatible"] is False


def test_define_background_rejects_unknown_type(monkeypatch):
    from cst_runtime.core import modeling

    monkeypatch.setattr(
        modeling,
        "_submit_versioned_vba",
        lambda *args, **kwargs: {"status": "success"},
    )

    result = modeling.define_background(
        "C:/work/working.cst",
        background_type="Lossy",
    )

    assert result["status"] == "error"
    assert result["error_type"] == "validation_error"
