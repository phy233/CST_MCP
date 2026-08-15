"""Contract tests for capture-3d-view tool (no CST required)."""
from __future__ import annotations

import json

import pytest

from helpers import REPO_ROOT, run_cli

pytestmark = pytest.mark.subprocess

_VALID_PROJECT = str(REPO_ROOT / "test_array.cst")


class TestCapture3DViewSchema:
    """Test tool schema and parameter validation."""
    
    def test_tool_exists(self):
        """Verify capture-3d-view is registered."""
        r = run_cli("describe-tool", "--tool", "capture-3d-view")
        assert r.returncode == 0, r.stderr
        assert "capture-3d-view" in r.stdout
    
    def test_project_path_required(self):
        """Verify error when project_path is missing."""
        r = run_cli("capture-3d-view")
        assert r.returncode != 0 or '"status": "error"' in r.stdout
        # CLI should error or return error JSON
        if r.returncode == 0:
            result = json.loads(r.stdout)
            assert result["status"] == "error"
            assert "project_path" in result.get("error_type", "") or "required" in result.get("message", "").lower()
    
    def test_project_not_found(self):
        """Verify error when project file doesn't exist."""
        r = run_cli("capture-3d-view", "--project-path", "C:/nonexistent/path.cst")
        assert r.returncode == 1, r.stderr
        result = json.loads(r.stdout)
        assert result["status"] == "error"
        assert "not_found" in result.get("error_type", "").lower() or "not found" in result.get("message", "").lower()
    
    def test_schema_exposes_only_documented_view_controls(self):
        """公开 schema 只暴露 CST 2022 手册记录的视图控制。"""
        r = run_cli("describe-tool", "--tool", "capture-3d-view")
        assert r.returncode == 0, r.stderr
        schema = json.loads(r.stdout)["json_schema"]
        properties = schema["properties"]
        assert "horizontal_rotation_deg" in properties
        assert "vertical_rotation_deg" in properties
        assert "azimuth" not in properties
        assert "elevation" not in properties
        assert "zoom" not in properties
        assert "Perspective" in properties["preset_name"]["enum"]
    
    def test_invalid_preset_name(self):
        """Verify error for unknown preset name."""
        r = run_cli(
            "capture-3d-view",
            "--project-path",
            _VALID_PROJECT,
            "--preset-name",
            "InvalidPreset",
        )
        assert r.returncode == 1, r.stderr
        result = json.loads(r.stdout)
        assert result["status"] == "error"
        assert "preset" in result.get("error_type", "").lower() or "preset" in result.get("message", "").lower()
    
    def test_invalid_view_type(self):
        """Verify error for invalid view_type."""
        r = run_cli(
            "capture-3d-view",
            "--project-path",
            _VALID_PROJECT,
            "--view-type",
            "invalid",
        )
        assert r.returncode == 1, r.stderr
        result = json.loads(r.stdout)
        assert result["status"] == "error"
