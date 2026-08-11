"""S 参数本地 JSON 恢复和插值测试。"""
from __future__ import annotations

import json
import math

import pytest


def _core_result(tmp_path, *, xdata, ydata):
    export_path = tmp_path / "s11.json"
    export_path.write_text(
        json.dumps({"xdata": xdata, "ydata": ydata}),
        encoding="utf-8",
    )
    return {
        "status": "success",
        "mode": "local_export_only",
        "treepath": "1D Results\\S-Parameters\\S1,1",
        "export_path": str(export_path),
    }


def test_get_sparam_reads_complex_json_and_sorts_frequency(monkeypatch, tmp_path) -> None:
    from cst_runtime.lib import results

    core_result = _core_result(
        tmp_path,
        xdata=[10.0, 8.0, 9.0],
        ydata=[
            {"real": -1.0, "imag": 0.0},
            {"real": 0.0, "imag": 1.0},
            {"real": 0.5, "imag": 0.5},
        ],
    )
    monkeypatch.setattr(results, "_get_1d_result", lambda *args, **kwargs: core_result)

    result = results.get_sparam("model.cst", core_result["treepath"])

    assert result["status"] == "success"
    assert result["xdata"] == [8.0, 9.0, 10.0]
    assert result["ydata"][0] == {"frequency": 8.0, "real": 0.0, "imag": 1.0}


@pytest.mark.parametrize(
    ("xdata", "ydata", "error_type"),
    [
        ([], [], "result_data_empty"),
        ([8.0], [], "result_data_empty"),
        ([8.0, 9.0], [{"real": 1.0, "imag": 0.0}], "result_data_length_mismatch"),
        (
            [8.0, 8.0],
            [{"real": 1.0, "imag": 0.0}, {"real": 0.0, "imag": 1.0}],
            "duplicate_result_frequency",
        ),
        ([float("nan")], [{"real": 1.0, "imag": 0.0}], "result_data_invalid"),
    ],
)
def test_get_sparam_rejects_invalid_export(
    monkeypatch,
    tmp_path,
    xdata,
    ydata,
    error_type,
) -> None:
    from cst_runtime.lib import results

    core_result = _core_result(tmp_path, xdata=xdata, ydata=ydata)
    monkeypatch.setattr(results, "_get_1d_result", lambda *args, **kwargs: core_result)

    result = results.get_sparam("model.cst", core_result["treepath"])

    assert result["status"] == "error"
    assert result["error_type"] == error_type


def test_get_sparam_at_freq_interpolates_real_and_imag(monkeypatch) -> None:
    from cst_runtime.lib import results
    from cst_runtime.lib.contracts import success_result

    monkeypatch.setattr(
        results,
        "get_sparam",
        lambda *args, **kwargs: success_result(
            ydata=[
                {"frequency": 8.0, "real": 0.0, "imag": 0.0},
                {"frequency": 10.0, "real": 2.0, "imag": 4.0},
            ]
        ),
    )

    result = results.get_sparam_at_freq("model.cst", "S1,1", 9.0)

    assert result["real"] == pytest.approx(1.0)
    assert result["imag"] == pytest.approx(2.0)
    assert result["magnitude"] == pytest.approx(math.sqrt(5.0))
    assert result["phase_deg"] == pytest.approx(math.degrees(math.atan2(2.0, 1.0)))


def test_get_sparam_at_freq_rejects_out_of_range(monkeypatch) -> None:
    from cst_runtime.lib import results
    from cst_runtime.lib.contracts import success_result

    monkeypatch.setattr(
        results,
        "get_sparam",
        lambda *args, **kwargs: success_result(
            ydata=[
                {"frequency": 8.0, "real": 0.0, "imag": 0.0},
                {"frequency": 10.0, "real": 1.0, "imag": 0.0},
            ]
        ),
    )

    result = results.get_sparam_at_freq("model.cst", "S1,1", 7.9)

    assert result["status"] == "error"
    assert result["error_type"] == "frequency_out_of_range"
