"""超表面目标函数与 run-experiment 复数序列的离线单测。

覆盖 P0-1 数据链：
- lib.experiments._metric_from_result 保留复数 xdata/ydata 并支持降采样；
- core.objective 的 amp_at_freq / phase_at_freq 注册目标；
- expression 沙箱新增的 phase_deg/amp_db/wrap 辅助函数；
- 既有的 s11/gain/bandwidth 行为保持兼容。
"""
from __future__ import annotations

import math

from cst_runtime.core.objective import compute_objective
from cst_runtime.lib.experiments import _MAX_METRIC_SERIES_POINTS, _metric_from_result


def _complex_point(real: float, imag: float) -> dict[str, float]:
    return {"real": real, "imag": imag}


def _channel_metric(
    result_path: str = "1D Results\\S-Parameters\\SZmin(1),Zmax(1)",
    freqs: list[float] | None = None,
    points: list[tuple[float, float]] | None = None,
    point_count: int | None = None,
) -> dict:
    if freqs is None:
        freqs = [9.9, 10.0, 10.1]
    if points is None:
        # 默认 10 GHz 相位约 +90°
        points = [(0.0, 1.0)] * len(freqs)
    ydata = [_complex_point(r, i) for r, i in points]
    return {
        "result_path": result_path,
        "run_id": 7,
        "point_count": point_count if point_count is not None else len(freqs),
        "xdata": list(freqs),
        "ydata": ydata,
    }


class TestMetricSeriesRetention:
    """run_experiment 指标层应保留复数序列供 objective 使用。"""

    def test_complex_series_preserved(self):
        inspected = {
            "result_path": "1D Results\\S-Parameters\\S1,1",
            "run_id": 3,
            "point_count": 3,
            "xdata": [2.38, 2.39, 2.40],
            "ydata": [
                _complex_point(0.1, 0.0),
                _complex_point(0.0562, 0.0),
                _complex_point(0.0316, 0.0),
            ],
        }
        metric = _metric_from_result(inspected)
        assert metric["xdata"] == [2.38, 2.39, 2.40]
        assert metric["ydata"] == [
            _complex_point(0.1, 0.0),
            _complex_point(0.0562, 0.0),
            _complex_point(0.0316, 0.0),
        ]
        assert abs(metric["min_db"] - (-30.0)) < 0.5
        assert "downsampled" not in metric

    def test_summary_uses_full_data_when_downsampled(self):
        total = _MAX_METRIC_SERIES_POINTS * 3
        freqs = [round(1.0 + idx * 0.001, 4) for idx in range(total)]
        valley_idx = total // 2
        ydata = [_complex_point(0.5, 0.0)] * total
        ydata[valley_idx] = _complex_point(0.00001, 0.0)
        inspected = {
            "result_path": "p",
            "run_id": 1,
            "point_count": total,
            "xdata": freqs,
            "ydata": ydata,
        }
        metric = _metric_from_result(inspected)
        assert metric["downsampled"] is True
        assert metric["source_point_count"] == total
        assert len(metric["xdata"]) <= _MAX_METRIC_SERIES_POINTS
        # min_db/best_freq 必须来自完整原始数据的谷底，而非降采样视图
        assert metric["best_freq"] == freqs[valley_idx]

    def test_unparseable_values_keep_legacy_shape(self):
        inspected = {
            "result_path": "p",
            "run_id": 1,
            "point_count": 2,
            "xdata": [1, 2],
            "ydata": ["garbage", None],
        }
        metric = _metric_from_result(inspected)
        assert set(metric) == {"result_path", "run_id", "point_count"}


class TestAmpAtFreqObjective:

    def test_db_at_nearest_freq(self):
        run_output = {
            "result_metrics": [
                _channel_metric(
                    points=[(0.5, 0.0), (0.0562, 0.0), (0.2, 0.0)],
                )
            ]
        }
        result = compute_objective(
            {"type": "amp_at_freq", "freq": 10.02}, run_output
        )
        expected = 20.0 * math.log10(0.0562)
        assert abs(result["value"] - expected) < 1e-6
        assert result["direction"] == "minimize"
        assert result["details"]["freq_ghz"] == 10.0

    def test_direction_override_for_transmission(self):
        run_output = {
            "result_metrics": [
                _channel_metric(
                    result_path="1D Results\\S-Parameters\\SZmin(1),Zmax(1)",
                    points=[(0.05, 0.0), (0.7, 0.0), (0.05, 0.0)],
                )
            ]
        }
        result = compute_objective(
            {"type": "amp_at_freq", "freq": 10.0, "direction": "maximize"},
            run_output,
        )
        assert abs(result["value"] - 20.0 * math.log10(0.7)) < 1e-6
        assert result["direction"] == "maximize"

    def test_missing_freq_param_is_error(self):
        run_output = {"result_metrics": [_channel_metric()]}
        result = compute_objective({"type": "amp_at_freq"}, run_output)
        assert "error" in result

    def test_unknown_channel_lists_available(self):
        run_output = {"result_metrics": [_channel_metric()]}
        result = compute_objective(
            {"type": "amp_at_freq", "result_path": "S33,33", "freq": 10},
            run_output,
        )
        assert "error" in result
        assert "zmax(1)" in result["error"]

    def test_no_complex_metrics_reports_error(self):
        result = compute_objective(
            {"type": "amp_at_freq", "freq": 10},
            {"result_metrics": [{"result_path": "p", "run_id": 1}]},
        )
        assert "error" in result


class TestPhaseAtFreqObjective:

    def test_on_target_returns_near_zero(self):
        run_output = {"result_metrics": [_channel_metric()]}
        result = compute_objective(
            {"type": "phase_at_freq", "freq": 10, "target_deg": 90},
            run_output,
        )
        assert abs(result["value"]) < 1e-6
        assert result["direction"] == "minimize"
        assert math.isclose(
            result["details"]["raw_phase_deg"], 90.0, abs_tol=1e-9
        )

    def test_wrapping_across_boundary(self):
        run_output = {
            "result_metrics": [
                _channel_metric(points=[(math.cos(math.radians(-179)), math.sin(math.radians(-179)))])
            ]
        }
        result = compute_objective(
            {"type": "phase_at_freq", "freq": 9.9, "target_deg": 179.0},
            run_output,
        )
        assert abs(result["value"] - 2.0) < 1e-6

    def test_freq_alias_and_substring_match(self):
        run_output = {"result_metrics": [_channel_metric()]}
        result = compute_objective(
            {
                "type": "phase_at_freq",
                "result_path": "zmax(1)",
                "freq_ghz": 10.1,
                "target_deg": 180.0,
            },
            run_output,
        )
        # 10.1 GHz 最近点相位为 90 度，与 180 目标差 90 度
        assert abs(result["value"] - 90.0) < 1e-6


class TestExpressionSandboxExtension:

    def test_phase_helper_expression(self):
        run_output = {"result_metrics": [_channel_metric()]}
        expr = "abs(wrap(phase_deg('zmax(1)', 10.0) - 90))"
        result = compute_objective({"type": "expression", "expr": expr}, run_output)
        assert abs(result["value"]) < 1e-6

    def test_amp_helper_expression(self):
        run_output = {
            "result_metrics": [
                _channel_metric(points=[(0.1, 0.0), (0.1, 0.0), (0.1, 0.0)])
            ]
        }
        result = compute_objective(
            {
                "type": "expression",
                "expr": "amp_db('szmin(1)', 10.0)",
            },
            run_output,
        )
        assert abs(result["value"] - 20.0 * math.log10(0.1)) < 1e-6

    def test_expression_rejects_unknown_names(self):
        run_output = {"result_metrics": [_channel_metric()]}
        result = compute_objective(
            {"type": "expression", "expr": "__import__('os').getcwd()"},
            run_output,
        )
        assert "error" in result

    def test_legacy_s11_expression_still_works(self):
        run_output = {
            "s11_metric": {
                "all_db": [-10, -20, -30],
                "all_freq": [2.3, 2.4, 2.5],
            },
            "s11_export_path": "",
            "farfield_exported": [],
        }
        result = compute_objective(
            {"type": "expression", "expr": "min(s11_db)"}, run_output
        )
        assert abs(result["value"] - (-30.0)) < 1e-9

    def test_no_data_reports_error(self):
        result = compute_objective(
            {"type": "expression", "expr": "len(channels)"},
            {},
        )
        assert result["error"] == "no_s11_data"
