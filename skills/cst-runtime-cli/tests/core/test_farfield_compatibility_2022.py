from __future__ import annotations

import pytest

from cst_runtime.core import farfield
from cst_runtime.core.compatibility import farfield as compatibility_farfield
from cst_runtime.core.compatibility.base import CompatibilityProfile
from cst_runtime.core.compatibility.farfield import (
    legacy_farfield_query_vba,
    read_legacy_farfield_list,
)
from cst_runtime.core.errors import VerificationError


CST2022 = CompatibilityProfile(major=2022, version="2022", source="test")
CST2026 = CompatibilityProfile(major=2026, version="2026", source="test")


def test_legacy_farfield_query_uses_farfield_plot_list_api() -> None:
    text = "\n".join(
        legacy_farfield_query_vba(
            tree_path="Farfields\\farfield (f=10) [1]",
            plot_mode="Realized Gain",
            frequency_ghz=10,
            theta_values=[0, 90],
            phi_values=[0, 180],
        )
    )

    assert 'FarfieldPlot.SetPlotMode "realized gain"' in text
    assert 'If Not SelectTreeItem("Farfields\\farfield (f=10) [1]") Then' in text
    assert "__CST_TREE_SELECTION_FAILED__" in text
    assert text.count("FarfieldPlot.AddListEvaluationPoint") == 4
    assert 'FarfieldPlot.CalculateList ""' in text
    assert 'FarfieldPlot.GetList("spherical abs")' in text
    assert 'FarfieldPlot.GetList("Point_T")' in text
    assert "FarfieldCalculator" not in text


def test_legacy_farfield_reader_reports_tree_selection_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        compatibility_farfield,
        "execute_text_query",
        lambda *_args, **_kwargs: [
            "__CST_TREE_SELECTION_FAILED__Farfields\\missing"
        ],
    )

    with pytest.raises(VerificationError, match="未能选中"):
        read_legacy_farfield_list(
            object(),
            tree_path="Farfields\\missing",
            plot_mode="Gain",
            frequency_ghz=8,
            theta_values=[0],
            phi_values=[0],
        )


def test_scalar_grid_selects_2022_legacy_reader(monkeypatch) -> None:
    calls = {}

    monkeypatch.setattr(compatibility_farfield, "profile_for", lambda _project: CST2022)

    def fake_reader(project, **kwargs):
        calls.update(project=project, **kwargs)
        return [1.0, 2.0, 3.0, 4.0], [0.0, 90.0, 0.0, 90.0], [0.0, 0.0, 180.0, 180.0]

    monkeypatch.setattr(compatibility_farfield, "read_legacy_farfield_list", fake_reader)
    monkeypatch.setattr(
        compatibility_farfield,
        "get_farfield_calculator",
        lambda _project: (_ for _ in ()).throw(AssertionError("CST 2022 不得访问 FarfieldCalculator")),
    )

    result = farfield._read_farfield_scalar_grid(
        project=object(),
        farfield_name="farfield (f=10) [1]",
        result_type="Gain",
        unit="dBi",
        theta_step_deg=90,
        phi_step_deg=180,
        theta_min_deg=0,
        theta_max_deg=90,
        phi_min_deg=0,
        phi_max_deg=180,
    )

    assert result["status"] == "success"
    assert result["source"] == "FarfieldPlot"
    assert result["grid_values"] == [[1.0, 2.0], [3.0, 4.0]]
    assert result["compatibility"]["profile"] == "cst2022"
    assert calls["plot_mode"] == "Gain"


def test_scalar_grid_uses_farfield_plot_in_2026_too(monkeypatch) -> None:
    monkeypatch.setattr(compatibility_farfield, "profile_for", lambda _project: CST2026)
    monkeypatch.setattr(
        compatibility_farfield,
        "read_legacy_farfield_list",
        lambda _project, **_kwargs: (
            [1.0, 2.0, 3.0, 4.0],
            [0.0, 90.0, 0.0, 90.0],
            [0.0, 0.0, 180.0, 180.0],
        ),
    )
    monkeypatch.setattr(
        compatibility_farfield,
        "get_farfield_calculator",
        lambda _project: (_ for _ in ()).throw(
            AssertionError("角度列表方法不得错误调用 FarfieldCalculator")
        ),
    )

    result = farfield._read_farfield_scalar_grid(
        project=object(),
        farfield_name="farfield (f=10) [1]",
        result_type="Gain",
        unit="dBi",
        theta_step_deg=90,
        phi_step_deg=180,
        theta_min_deg=0,
        theta_max_deg=90,
        phi_min_deg=0,
        phi_max_deg=180,
    )

    assert result["status"] == "success"
    assert result["source"] == "FarfieldPlot"
    assert result["compatibility"]["profile"] == "cst2026"


def test_ascii_export_cut_template_remains_2022_compatible() -> None:
    text = farfield._build_farfield_cut_export_command(
        "Farfields\\Farfield Cuts\\Phi=0",
        "D:/temp/cut.txt",
    )

    assert "With ASCIIExport" in text
    assert "If Not SelectTreeItem" in text
    assert "ReportError" in text
    assert ".Reset" in text
    assert ".FileName" in text
    assert ".Execute" in text
