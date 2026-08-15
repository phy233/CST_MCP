"""CLI error-path tests: missing workspace, missing source, bad calls."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from helpers import run_cli

pytestmark = pytest.mark.subprocess


def _run_in_workspace(args: list[str]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        init = run_cli("init-workspace", "--workspace", str(ws))
        assert init.returncode == 0
        return run_cli(*args, "--workspace", str(ws))


class TestCliErrors:
    """Error-handling paths for the CLI."""

    def test_prepare_run_missing_source_reports_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            run_cli("init-workspace", "--workspace", str(ws))
            run_cli("init-task", "--workspace", str(ws), "--task-id", "task_test", "--source-project", str(ws / "missing.cst"), "--goal", "test")
            task_path = ws / "tasks" / "task_test"
            r = run_cli("prepare-run", "--args-json", json.dumps({"task_path": str(task_path)}), "--workspace", str(ws))
            assert r.returncode == 1
            p = json.loads(r.stdout)
            assert p["status"] == "error"
            assert p["error_type"] == "source_project_missing"

    def test_production_tool_requires_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            r = run_cli("prepare-run", "--workspace", tmpdir, "--args-json", json.dumps({"task_path": str(Path(tmpdir) / "tasks" / "task_001")}))
            assert r.returncode == 1
            p = json.loads(r.stdout)
            assert p["status"] == "error"
            assert p["error_type"] == "workspace_not_initialized"

    def test_error_outputs_have_error_type(self) -> None:
        r = run_cli("prepare-run")
        assert r.returncode in {1, 2}
        p = json.loads(r.stdout)
        assert "error_type" in p
        assert "adapter" in p

    def test_direct_tool_call_without_workspace(self) -> None:
        r = run_cli("prepare-run")
        assert r.returncode in {1, 2}
        p = json.loads(r.stdout)
        assert p["status"] == "error"
        assert "error_type" in p
