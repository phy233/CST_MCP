"""超表面多通道 S 参数离线分析测试。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cst_runtime.core.metasurface import analyze_metasurface_sparameters


def _write_channel(path: Path, run_id: int, points: list[tuple[float, complex]]) -> Path:
    payload = {
        "run_id": run_id,
        "points": [
            {"frequency": frequency, "real": value.real, "imag": value.imag}
            for frequency, value in points
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _channel(name: str, path: Path, kind: str, polarization: str, include: bool = True) -> dict:
    return {
        "name": name,
        "file_path": str(path),
        "kind": kind,
        "polarization": polarization,
        "include_in_total_power": include,
    }


def test_analysis_calculates_complex_phase_rta_pcr_and_writes_json(tmp_path: Path) -> None:
    frequencies = [9.0, 10.0, 11.0]
    rco = _write_channel(tmp_path / "rco.json", 7, list(zip(frequencies, [0.5 + 0j, -0.5 + 0j, -0.5j])))
    rcross = _write_channel(tmp_path / "rcross.json", 7, list(zip(frequencies, [0.5 + 0j] * 3)))
    tco = _write_channel(tmp_path / "tco.json", 7, list(zip(frequencies, [0.5 + 0j] * 3)))
    output = tmp_path / "analysis.json"
    result = analyze_metasurface_sparameters(
        channels=[
            _channel("r_co", rco, "reflection", "co"),
            _channel("r_cross", rcross, "reflection", "cross"),
            _channel("t_co", tco, "transmission", "co"),
        ],
        target_phases=[{"channel": "r_co", "frequency_ghz": 10.5, "phase_deg": -135.0}],
        passivity_tolerance=1e-9,
        output_path=str(output),
    )
    assert result["status"] == "success"
    assert result["file_size"] > 0
    assert result["run_id"] == 7
    payload = json.loads(output.read_text(encoding="utf-8"))
    first = payload["frequency_metrics"][0]
    assert first["R_co"] == pytest.approx(0.25)
    assert first["R_cross"] == pytest.approx(0.25)
    assert first["R_total"] == pytest.approx(0.5)
    assert first["T_total"] == pytest.approx(0.25)
    assert first["A"] == pytest.approx(0.25)
    assert first["reflection_pcr"] == pytest.approx(0.5)
    phases = payload["channels"][0]["points"]
    assert phases[1]["phase_deg"] in {180.0, -180.0}
    # ±180° 处存在等价分支；关键是展开结果没有产生额外的 360° 跳变。
    assert phases[2]["unwrapped_phase_deg"] == pytest.approx(-90.0)
    target = payload["target_phase_errors"][0]
    assert target["actual_phase_deg"] == pytest.approx(-135.0)
    assert target["phase_error_deg"] == pytest.approx(0.0)


def test_pcr_zero_denominator_returns_null(tmp_path: Path) -> None:
    zero = _write_channel(tmp_path / "zero.json", 1, [(10.0, 0j)])
    output = tmp_path / "analysis.json"
    result = analyze_metasurface_sparameters(
        channels=[_channel("r", zero, "reflection", "co")],
        output_path=str(output),
    )
    assert result["status"] == "success"
    metric = json.loads(output.read_text(encoding="utf-8"))["frequency_metrics"][0]
    assert metric["reflection_pcr"] is None
    assert metric["transmission_pcr"] is None


def test_excluded_channel_does_not_enter_total_power(tmp_path: Path) -> None:
    included = _write_channel(tmp_path / "included.json", 1, [(10.0, 0.5 + 0j)])
    excluded = _write_channel(tmp_path / "excluded.json", 1, [(10.0, 2.0 + 0j)])
    output = tmp_path / "analysis.json"
    result = analyze_metasurface_sparameters(
        channels=[
            _channel("included", included, "reflection", "co"),
            _channel("excluded", excluded, "reflection", "cross", include=False),
        ],
        output_path=str(output),
    )
    assert result["status"] == "success"
    metric = json.loads(output.read_text(encoding="utf-8"))["frequency_metrics"][0]
    assert metric["R_total"] == pytest.approx(0.25)


def test_passivity_tolerance_and_warning_count(tmp_path: Path) -> None:
    over = _write_channel(tmp_path / "over.json", 1, [(10.0, (1.0001 + 0j))])
    allowed_output = tmp_path / "allowed.json"
    allowed = analyze_metasurface_sparameters(
        channels=[_channel("r", over, "reflection", "co")],
        passivity_tolerance=0.001,
        output_path=str(allowed_output),
    )
    assert allowed["warning_count"] == 0
    strict_output = tmp_path / "strict.json"
    strict = analyze_metasurface_sparameters(
        channels=[_channel("r", over, "reflection", "co")],
        passivity_tolerance=0.0,
        output_path=str(strict_output),
    )
    assert strict["warning_count"] == 1
    assert json.loads(strict_output.read_text(encoding="utf-8"))["frequency_metrics"][0]["passive"] is False


@pytest.mark.parametrize("mismatch", ["run_id", "grid"])
def test_run_id_or_grid_mismatch_is_rejected_without_output(tmp_path: Path, mismatch: str) -> None:
    first = _write_channel(tmp_path / "first.json", 1, [(9.0, 0j), (10.0, 0j)])
    second_run = 2 if mismatch == "run_id" else 1
    second_grid = [(9.0, 0j), (10.0 if mismatch == "run_id" else 10.5, 0j)]
    second = _write_channel(tmp_path / "second.json", second_run, second_grid)
    output = tmp_path / "analysis.json"
    result = analyze_metasurface_sparameters(
        channels=[
            _channel("a", first, "reflection", "co"),
            _channel("b", second, "transmission", "co"),
        ],
        output_path=str(output),
    )
    assert result["status"] == "error"
    assert not output.exists()


def test_non_increasing_grid_is_rejected(tmp_path: Path) -> None:
    source = _write_channel(tmp_path / "source.json", 1, [(10.0, 0j), (10.0, 1 + 0j)])
    output = tmp_path / "analysis.json"
    result = analyze_metasurface_sparameters(
        channels=[_channel("a", source, "reflection", "co")],
        output_path=str(output),
    )
    assert result["status"] == "error"
    assert not output.exists()
