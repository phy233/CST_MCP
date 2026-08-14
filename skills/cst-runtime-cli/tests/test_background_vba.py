"""背景设置 VBA 生成与运行时跟踪状态（get_background/define_background）单元测试。"""
from __future__ import annotations

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


# ---------------------------------------------------------------------------
# get_background：CST 2022 手册未定义背景读取接口，只能返回运行时跟踪状态
# ---------------------------------------------------------------------------

def test_get_background_returns_tracked_state(monkeypatch):
    from cst_runtime.core import modeling

    monkeypatch.setattr(
        modeling.gateway,
        "get_background_state",
        lambda path: {
            "background_type": "Normal",
            "epsilon": 1.0,
            "mu": 1.0,
            "source": "runtime_tracked",
        },
    )

    result = modeling.get_background("C:/work/working.cst")

    assert result["status"] == "success"
    assert result["background_type"] == "Normal"
    assert result["epsilon"] == 1.0
    assert result["mu"] == 1.0
    assert result["farfield_compatible"] is True
    assert result["source"] == "runtime_tracked"
    assert "手册" in result["manual_note"]


def test_get_background_flags_lossy_tracked_state(monkeypatch):
    from cst_runtime.core import modeling

    monkeypatch.setattr(
        modeling.gateway,
        "get_background_state",
        lambda path: {
            "background_type": "Normal",
            "epsilon": 4.3,
            "mu": 1.0,
            "source": "runtime_tracked",
        },
    )

    result = modeling.get_background("C:/work/working.cst")

    assert result["status"] == "success"
    assert result["farfield_compatible"] is False


def test_get_background_flags_pec_tracked_state(monkeypatch):
    from cst_runtime.core import modeling

    monkeypatch.setattr(
        modeling.gateway,
        "get_background_state",
        lambda path: {
            "background_type": "PEC",
            "epsilon": 1.0,
            "mu": 1.0,
            "source": "runtime_tracked",
        },
    )

    result = modeling.get_background("C:/work/working.cst")

    assert result["status"] == "success"
    assert result["farfield_compatible"] is False


def test_get_background_unknown_state_returns_manual_error(monkeypatch):
    from cst_runtime.core import modeling

    monkeypatch.setattr(modeling.gateway, "get_background_state", lambda path: None)

    result = modeling.get_background("C:/work/working.cst")

    assert result["status"] == "error"
    assert result["error_type"] == "background_state_unknown"
    assert "手册" in result["manual_note"]
    assert "define-background" in result["next_action"]


def test_get_background_never_calls_undocumented_vba_reads(monkeypatch):
    """CST 2022 手册无 Background 读取接口，get_background 不得调用任何 VBA 查询。"""
    from cst_runtime.core import modeling

    monkeypatch.setattr(modeling.gateway, "get_background_state", lambda path: None)
    # modeling 模块根本不保留 VBA 文本查询通道：不存在该导入即无法调用
    assert not hasattr(modeling, "execute_text_query")

    result = modeling.get_background("C:/work/working.cst")

    assert result["error_type"] == "background_state_unknown"


# ---------------------------------------------------------------------------
# define_background：请求值 + 运行时跟踪登记 + 手册依据的 readback 说明
# ---------------------------------------------------------------------------

def test_define_background_registers_state_and_returns_requested(monkeypatch):
    from cst_runtime.core import modeling

    marked = {}
    monkeypatch.setattr(
        modeling,
        "_submit_versioned_vba",
        lambda *args, **kwargs: {
            "status": "success",
            "submission": "accepted",
            "execution": "reported_ok",
        },
    )
    monkeypatch.setattr(
        modeling.gateway,
        "mark_background_state",
        lambda path, **state: marked.update(state),
    )

    result = modeling.define_background("C:/work/working.cst")

    assert result["status"] == "success"
    assert result["requested"] == {
        "background_type": "Normal",
        "epsilon": 1.0,
        "mu": 1.0,
    }
    assert result["farfield_compatible"] is True
    assert result["farfield_basis"] == "requested"
    assert result["background_state"] == "tracked"
    assert result["readback"]["status"] == "unsupported_by_manual"
    assert "手册" in result["readback"]["manual_note"]
    assert marked == {"background_type": "Normal", "epsilon": 1.0, "mu": 1.0}


def test_define_background_pec_requested_is_not_farfield_compatible(monkeypatch):
    from cst_runtime.core import modeling

    monkeypatch.setattr(
        modeling,
        "_submit_versioned_vba",
        lambda *args, **kwargs: {
            "status": "success",
            "submission": "accepted",
            "execution": "reported_ok",
        },
    )
    monkeypatch.setattr(
        modeling.gateway,
        "mark_background_state",
        lambda path, **state: None,
    )

    result = modeling.define_background("C:/work/working.cst", background_type="PEC")

    assert result["status"] == "success"
    assert result["farfield_compatible"] is False
    assert "远场监视器" in result["warning"]
    assert result["requested"]["background_type"] == "PEC"


def test_define_background_buffered_not_tracked(monkeypatch):
    from cst_runtime.core import modeling

    marked = []
    monkeypatch.setattr(
        modeling,
        "_submit_versioned_vba",
        lambda *args, **kwargs: {
            "status": "success",
            "submission": "buffered",
            "execution": "not_run",
        },
    )
    monkeypatch.setattr(
        modeling.gateway,
        "mark_background_state",
        lambda path, **state: marked.append(state),
    )

    result = modeling.define_background("C:/work/working.cst")

    assert result["status"] == "success"
    assert result["background_state"] == "not_tracked"
    assert marked == []


def test_set_background_with_space_tracks_normal_state(monkeypatch):
    from cst_runtime.core import modeling

    marked = {}
    monkeypatch.setattr(
        modeling,
        "_submit_versioned_vba",
        lambda *args, **kwargs: {
            "status": "success",
            "submission": "accepted",
            "execution": "reported_ok",
        },
    )
    monkeypatch.setattr(
        modeling.gateway,
        "mark_background_state",
        lambda path, **state: marked.update(state),
    )

    result = modeling.set_background_with_space("C:/work/working.cst")

    assert result["status"] == "success"
    assert marked == {"background_type": "Normal", "epsilon": 1.0, "mu": 1.0}


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
