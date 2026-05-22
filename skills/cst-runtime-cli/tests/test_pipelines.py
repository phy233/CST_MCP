from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path

SCRIPTS = str(Path(__file__).resolve().parents[1] / "scripts")
sys.path.insert(0, SCRIPTS)

from cst_runtime.cli.dispatch import TOOLS


class TestPipelineHelpers:
    def test_safe_log_db_positive(self):
        from cst_runtime.cli.pipelines.impl import _safe_log_db
        assert abs(_safe_log_db(0.5) - 20 * math.log10(0.5)) < 0.01

    def test_safe_log_db_zero(self):
        from cst_runtime.cli.pipelines.impl import _safe_log_db
        assert abs(_safe_log_db(0) - 20 * math.log10(1e-15)) < 0.01

    def test_parse_s11_json_valid(self):
        from cst_runtime.cli.pipelines.impl import _parse_s11_json
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "s11_run1.json"
            payload = {
                "run_id": 1,
                "xdata": [9.0, 10.0, 11.0],
                "ydata": [
                    {"real": 0.3, "imag": 0.0},
                    {"real": 0.1, "imag": 0.0},
                    {"real": 0.2, "imag": 0.0},
                ],
            }
            p.write_text(json.dumps(payload), encoding="utf-8")
            result = _parse_s11_json(str(p))
            assert result is not None
            assert result["run_id"] == 1
            assert result["min_db"] < -10  # -20 dB for 0.1
            assert abs(result["best_freq"] - 10.0) < 0.1

    def test_parse_s11_json_complex_yielddata(self):
        from cst_runtime.cli.pipelines.impl import _parse_s11_json
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "s11_run2.json"
            payload = {
                "run_id": 2,
                "xdata": [9.0, 10.0],
                "ydata": [0.2, 0.05],
            }
            p.write_text(json.dumps(payload), encoding="utf-8")
            result = _parse_s11_json(str(p))
            assert result is not None
            assert abs(result["best_freq"] - 10.0) < 0.1

    def test_parse_s11_json_empty(self):
        from cst_runtime.cli.pipelines.impl import _parse_s11_json
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "empty.json"
            p.write_text("{}", encoding="utf-8")
            result = _parse_s11_json(str(p))
            assert result is None

    def test_parse_s11_json_missing_file(self):
        from cst_runtime.cli.pipelines.impl import _parse_s11_json
        result = _parse_s11_json(str(Path("/nonexistent/file.json")))
        assert result is None


class TestPipelineErrorPaths:
    def test_inspect_project_missing_path(self):
        from cst_runtime.cli.pipelines.impl import pipeline_inspect_project
        result = pipeline_inspect_project("/nonexistent/path.cst")
        assert result["status"] == "error"
        assert "pipeline_open_failed" in result.get("error_type", "")

    def test_prepare_experiment_missing_param_name(self):
        from cst_runtime.cli.pipelines.impl import pipeline_prepare_experiment
        result = pipeline_prepare_experiment(
            project_path="/nonexistent/path.cst",
            param_name="",
            param_value=23.5,
        )
        assert result["status"] == "error"
        assert result["error_type"] == "pipeline_param_missing"

    def test_prepare_experiment_missing_project(self):
        from cst_runtime.cli.pipelines.impl import pipeline_prepare_experiment
        result = pipeline_prepare_experiment(
            project_path="/nonexistent/p.cst",
            param_name="g",
            param_value=23.5,
        )
        assert result["status"] == "error"

    def test_run_experiment_missing_project(self):
        from cst_runtime.cli.pipelines.impl import pipeline_run_experiment
        result = pipeline_run_experiment(project_path="/nonexistent/p.cst")
        assert result["status"] == "error"


class TestPipelineToolRegistration:
    def test_pipeline_tools_registered(self):
        for name in ("inspect-project", "prepare-experiment", "run-experiment"):
            assert name in TOOLS, f"Missing tool: {name}"

    def test_pipeline_metadata(self):
        assert TOOLS["inspect-project"]["category"] == "project_ops"
        assert TOOLS["inspect-project"]["risk"] == "read"
        assert TOOLS["prepare-experiment"]["category"] == "project_ops"
        assert TOOLS["prepare-experiment"]["risk"] == "write"
        assert TOOLS["run-experiment"]["category"] == "simulation"
        assert TOOLS["run-experiment"]["risk"] == "long-running"

    def test_pipeline_args_templates(self):
        from cst_runtime.tools import build_args_templates
        templates = build_args_templates()
        for name in ("inspect-project", "prepare-experiment", "run-experiment"):
            assert name in templates, f"Missing args template: {name}"

    def test_pipeline_descriptions(self):
        from cst_runtime.cli.pipelines.registry import PIPELINES
        for name in ("inspect-project", "prepare-experiment", "run-experiment"):
            assert name in PIPELINES, f"Missing pipeline: {name}"
