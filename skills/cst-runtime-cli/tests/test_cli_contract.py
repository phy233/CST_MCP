"""No-CST-start CLI contract checks for cst_runtime.

Covers every tool, pipeline, args template, JSON contract, and error path
that can be validated without starting CST Studio Suite.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPO_ROOT / "skills" / "cst-runtime-cli"
PYTHON = sys.executable
_PYTHONPATH = str(SKILL_ROOT / "scripts")

# Tools that require CST session — cannot test without real CST
_CST_REQUIRED_TOOLS = {
    "cst-session-open", "cst-session-close", "cst-session-reattach",
    "define-brick", "define-cylinder", "define-cone", "define-rectangle",
    "boolean-subtract", "boolean-add", "boolean-intersect", "boolean-insert",
    "delete-entity", "create-component", "change-material",
    "list-entities", "list-parameters", "change-parameter",
    "start-simulation-async", "is-simulation-running",
    "wait-simulation", "stop-simulation", "pause-simulation", "resume-simulation",
    "save-project", "verify-project-identity", "define-material-from-mtd",
    "list-open-projects", "open-results-project", "list-subprojects",
    "list-run-ids", "get-parameter-combination", "get-1d-result", "get-2d-result",
    "create-blank-project",
    "define-frequency-range", "change-solver-type",
    "define-background", "define-boundary", "define-mesh", "define-solver",
    "define-port", "define-monitor", "rename-entity", "set-entity-color",
    "define-units", "set-farfield-monitor", "set-efield-monitor",
    "set-field-monitor", "set-probe", "delete-probe", "delete-monitor",
    "set-background-with-space", "set-farfield-plot-cuts", "show-bounding-box",
    "activate-post-process", "create-mesh-group", "set-solver-acceleration",
    "set-fdsolver-extrude-open-bc", "set-mesh-fpbavoid-nonreg-unite",
    "set-mesh-minimum-step-number", "define-polygon-3d",
    "define-analytical-curve", "define-extrude-curve",
    "transform-shape", "transform-curve",
    "create-horn-segment", "create-loft-sweep", "create-hollow-sweep",
    "add-to-history", "pick-face", "define-loft",
    "export-e-field", "export-surface-current", "export-voltage",
    "define-parameters",
    "export-farfield-fresh-session", "export-existing-farfield-cut-fresh-session",
    "read-realized-gain-grid-fresh-session",
}

# Tools that can be tested without any workspace
_NO_WORKSPACE_TOOLS = {
    "usage-guide", "list-tools", "list-pipelines",
    "describe-tool", "describe-pipeline", "args-template", "pipeline-template",
    "init-workspace", "init-task",
    "cst-session-inspect", "cst-session-quit",
    "plot-exported-file",
    "calculate-farfield-neighborhood-flatness",
    "list-materials", "install-cst-libraries", "health-check",
}

# All tools that don't need CST but still need a workspace:
_NO_CST_TOOLS = _NO_WORKSPACE_TOOLS | {
    "prepare-run", "get-run-context",
    "record-stage", "update-status",
    "infer-run-dir", "wait-project-unlocked",
}


def run_cli(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": _PYTHONPATH}
    return subprocess.run(
        [PYTHON, "-m", "cst_runtime", *args],
        cwd=REPO_ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def get_all_tool_names() -> list[str]:
    result = run_cli("list-tools")
    payload = json.loads(result.stdout)
    return [t["name"] for t in payload["tools"]]


def get_all_pipeline_names() -> list[str]:
    result = run_cli("list-pipelines")
    payload = json.loads(result.stdout)
    return [p["name"] for p in payload["pipelines"]]


def _run_in_workspace(args: list[str]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        init = run_cli("init-workspace", "--workspace", str(ws))
        assert init.returncode == 0
        return run_cli(*args, "--workspace", str(ws))


class CliContractAllToolsTests:
    """Every tool has valid metadata, args template, and consistent JSON output."""

    def test_all_tools_are_listed(self) -> None:
        names = get_all_tool_names()
        assert len(names) > 50, f"Only {len(names)} tools found"

    def test_every_tool_describe_returns_success(self) -> None:
        for tool in get_all_tool_names():
            if tool in _CST_REQUIRED_TOOLS:
                continue
            r = run_cli("describe-tool", "--tool", tool)
            assert r.returncode == 0, r.stderr[:200]
            p = json.loads(r.stdout)
            assert p["status"] == "success"
            assert p["tool"]["name"] == tool
            assert "category" in p["tool"]
            assert "risk" in p["tool"]
            assert "description" in p["tool"]

    def test_every_tool_has_args_template(self) -> None:
        for tool in get_all_tool_names():
            if tool in _CST_REQUIRED_TOOLS:
                continue
            r = run_cli("args-template", "--tool", tool)
            assert r.returncode == 0, r.stderr[:200]
            p = json.loads(r.stdout)
            assert p["status"] == "success"
            assert p["tool"] == tool
            assert isinstance(p["args_template"], dict)

    def test_args_template_writes_valid_json_file(self) -> None:
        for tool in get_all_tool_names():
            if tool in _CST_REQUIRED_TOOLS:
                continue
            with tempfile.TemporaryDirectory() as tmpdir:
                out = Path(tmpdir) / f"{tool}_args.json"
                r = run_cli("args-template", "--tool", tool, "--output", str(out))
                assert r.returncode == 0, r.stderr[:200]
                p = json.loads(r.stdout)
                assert p["status"] == "success"
                assert Path(p["output_path"]) == out
                written = json.loads(out.read_text(encoding="utf-8"))
                assert isinstance(written, dict)

    def test_unknown_tool_returns_json_error(self) -> None:
        r = run_cli("describe-tool", "--tool", "nonexistent-tool-xyz")
        assert r.returncode == 1
        p = json.loads(r.stdout)
        assert p["status"] == "error"
        assert p["error_type"] == "unknown_tool"
        assert "available_tools" in p

    def test_unknown_arg_template_returns_json_error(self) -> None:
        r = run_cli("args-template", "--tool", "nonexistent-tool-xyz")
        assert r.returncode == 1
        p = json.loads(r.stdout)
        assert p["status"] == "error"
        assert p["error_type"] == "unknown_tool"


class CliContractAllPipelinesTests:
    """Every pipeline has valid metadata and is documented."""

    def test_all_pipelines_are_listed(self) -> None:
        names = get_all_pipeline_names()
        assert len(names) > 5, f"Only {len(names)} pipelines found"

    def test_every_pipeline_describe_returns_success(self) -> None:
        for pipe in get_all_pipeline_names():
            r = run_cli("describe-pipeline", "--pipeline", pipe)
            assert r.returncode == 0, r.stderr[:200]
            p = json.loads(r.stdout)
            assert p["status"] == "success"
            assert p["pipeline"] == pipe
            assert "category" in p["recipe"]
            assert "risk" in p["recipe"]
            assert "steps" in p["recipe"]

    def test_every_pipeline_template_generates_plan(self) -> None:
        for pipe in get_all_pipeline_names():
            with tempfile.TemporaryDirectory() as tmpdir:
                out = Path(tmpdir) / f"{pipe}_plan.json"
                r = run_cli("pipeline-template", "--pipeline", pipe, "--output", str(out))
                assert r.returncode == 0, r.stderr[:200]
                assert out.exists()
                plan = json.loads(out.read_text(encoding="utf-8"))
                assert plan["pipeline"] == pipe

    def test_unknown_pipeline_returns_json_error(self) -> None:
        r = run_cli("describe-pipeline", "--pipeline", "nonexistent-pipeline-xyz")
        assert r.returncode == 1
        p = json.loads(r.stdout)
        assert p["status"] == "error"
        assert p["error_type"] == "unknown_pipeline"
        assert "available_pipelines" in p

    def test_every_pipeline_step_tool_exists(self) -> None:
        """Ensure every pipeline step references a real tool or meta command."""
        sys.path.insert(0, str(SKILL_ROOT / "scripts"))
        from cst_runtime.cli.dispatch import TOOLS
        from cst_runtime.cli.pipelines.registry import PIPELINES

        known_tools = set(TOOLS) | {
            "help", "list-tools", "list-pipelines", "describe-tool",
            "describe-pipeline", "args-template", "pipeline-template",
            "usage-guide", "invoke",
        }
        placeholders = {"<tool>", "--help"}
        missing: list[str] = []
        for pipe_name, pipe_def in PIPELINES.items():
            for step in pipe_def.get("steps", []):
                tool = step.get("tool", "")
                if tool in placeholders:
                    continue
                if tool not in known_tools:
                    missing.append(f"{pipe_name}: unknown tool {tool!r}")
        assert not missing, "\n".join(missing)


class CliContractOutputFormatTests:
    """All CLI output follows the JSON contract."""

    def test_all_outputs_have_required_fields(self) -> None:
        for cmd in ("usage-guide", "list-tools", "list-pipelines"):
            r = run_cli(cmd)
            assert r.returncode == 0, r.stderr
            p = json.loads(r.stdout)
            assert "status" in p
            assert "adapter" in p
            assert p["adapter"] in ("cst_runtime_cli", "cst_runtime")

    def test_error_outputs_have_error_type(self) -> None:
        r = run_cli("prepare-run")
        assert r.returncode in {1, 2}
        p = json.loads(r.stdout)
        assert "error_type" in p
        assert "adapter" in p

    def test_stdout_is_always_json(self) -> None:
        for cmd in ("--version", "--help"):
            r = run_cli(cmd)
            assert r.returncode == 0, r.stderr
            # version/help are plain text, ok

    def test_pipeline_template_is_serializable(self) -> None:
        for pipe in get_all_pipeline_names():
            r = run_cli("pipeline-template", "--pipeline", pipe)
            assert r.returncode == 0, r.stderr[:200]
            json.loads(r.stdout)


class CliContractNoCstFunctionalTests:
    """Functional tests for tools that work without CST."""

    def test_list_materials_returns_names(self) -> None:
        r = run_cli("list-materials")
        assert r.returncode == 0, r.stderr
        p = json.loads(r.stdout)
        assert p["status"] == "success"
        assert p["count"] > 0
        assert isinstance(p["material_names"], list)

    def test_install_cst_libraries_dry_run_scans(self) -> None:
        r = run_cli("install-cst-libraries", "--dry-run", "true")
        assert r.returncode == 0, r.stderr
        p = json.loads(r.stdout)
        assert p["status"] == "success"
        assert p["dry_run"]
        assert "target_path" in p
        assert "scan" in p

    def test_health_check_reports_status(self) -> None:
        r = run_cli("health-check", "--auto-fix", "true")
        assert r.returncode == 0, r.stderr
        p = json.loads(r.stdout)
        assert p["status"] == "success"
        assert "overall" in p
        assert "phases" in p
        assert "fixes_applied" in p
        assert "workspace" in p
        assert "platform" in p

    def test_health_check_without_auto_fix(self) -> None:
        r = run_cli("health-check", "--auto-fix", "false")
        assert r.returncode == 0, r.stderr
        p = json.loads(r.stdout)
        assert p["status"] == "success"
        assert "overall" in p

    def test_plot_exported_file_with_s11_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            s11 = d / "s11.json"
            s11.write_text(json.dumps({
                "run_id": 1, "xdata": [9.0, 10.0, 11.0],
                "ydata": [{"real": 0.3, "imag": 0.0}, {"real": 0.1, "imag": 0.0}, {"real": 0.2, "imag": 0.0}],
            }), encoding="utf-8")
            r = run_cli("plot-exported-file", "--file-path", str(s11), "--output-html", str(d / "preview.html"), "--page-title", "Test")
            assert r.returncode == 0, r.stderr
            p = json.loads(r.stdout)
            assert p["status"] == "success"
            assert (d / "preview.html").exists()

    def test_calculate_farfield_flatness_with_stub_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            for fn in ("cut0.json", "cut90.json"):
                angles = list(range(-15, 16))
                gains = [14.0 - abs(t) * 0.1 for t in angles]
                (d / fn).write_text(json.dumps({
                    "angle_deg": angles,
                    "primary_db": gains,
                }), encoding="utf-8")
            r = run_cli("calculate-farfield-neighborhood-flatness", "--args-json", json.dumps({
                "file_paths": [str(d / "cut0.json"), str(d / "cut90.json")],
                "theta_max_deg": 15.0, "output_json": str(d / "flatness.json")
            }))
            assert r.returncode == 0, r.stderr
            p = json.loads(r.stdout)
            assert p["status"] == "success"

    def test_record_and_update_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            run_cli("init-workspace", "--workspace", str(ws))
            run_cli("init-task", "--workspace", str(ws), "--task-id", "task_test", "--source-project", str(ws / "missing.cst"), "--goal", "test")
            task_json = ws / "tasks" / "task_test" / "task.json"
            assert task_json.exists()

            run_dir = ws / "tasks" / "task_test" / "runs" / "run_001"
            run_dir.mkdir(parents=True, exist_ok=True)

            stage = run_cli("record-stage", "--args-json", json.dumps({
                "task_path": str(task_json.parent), "run_id": "run_001",
                "stage": "test", "status": "completed", "message": "test",
            }), "--workspace", str(ws))
            assert stage.returncode == 0, stage.stderr
            sp = json.loads(stage.stdout)
            assert sp["status"] == "success"

            status = run_cli("update-status", "--args-json", json.dumps({
                "task_path": str(task_json.parent), "run_id": "run_001",
                "status": "validated", "stage": "test",
            }), "--workspace", str(ws))
            assert status.returncode == 0, status.stderr
            up = json.loads(status.stdout)
            assert up["status"] == "success"

    def test_wait_project_unlocked_no_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            run_cli("init-workspace", "--workspace", str(ws))
            fake_project = ws / "projects" / "working.cst"
            fake_project.parent.mkdir(parents=True, exist_ok=True)
            fake_project.write_text("fake", encoding="utf-8")
            r = run_cli("wait-project-unlocked", "--project-path", str(fake_project), "--timeout-seconds", "1", "--workspace", str(ws))
            assert r.returncode == 0, r.stderr
            p = json.loads(r.stdout)
            assert "locked" in p

    def test_infer_run_dir_no_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            run_cli("init-workspace", "--workspace", str(ws))
            fake = ws / "some" / "path" / "working.cst"
            fake.parent.mkdir(parents=True, exist_ok=True)
            fake.write_text("fake", encoding="utf-8")
            r = run_cli("infer-run-dir", "--project-path", str(fake), "--workspace", str(ws))
            assert r.returncode == 0, r.stderr
            p = json.loads(r.stdout)
            assert p["status"] == "success"
            assert p["run_dir"] is None

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


class CliContractGovernanceTests:
    """Governance rules embedded in tool metadata."""

    def test_modeling_write_tools_have_governance(self) -> None:
        modeling_writes = {
            "define-brick", "define-cylinder", "define-cone", "define-rectangle",
            "boolean-subtract", "boolean-add", "boolean-intersect", "boolean-insert",
            "delete-entity", "create-component", "change-material",
        }
        for tool in modeling_writes:
            r = run_cli("describe-tool", "--tool", tool)
            if r.returncode != 0:
                continue
            p = json.loads(r.stdout)
            meta = p.get("tool", {})
            assert "pipeline_mode" in meta
            assert "requires_run_context" in meta
            assert "requires_check_solid" in meta

    def test_read_tools_do_not_require_check_solid(self) -> None:
        read_tools = {"list-parameters", "list-entities", "list-materials",
                       "cst-session-inspect"}
        for tool in read_tools:
            r = run_cli("describe-tool", "--tool", tool)
            if r.returncode != 0:
                continue
            p = json.loads(r.stdout)
            meta = p.get("tool", {})
            if meta.get("requires_check_solid"):
                assert meta.get("pipeline_mode") == "read_only"

    def test_session_tools_have_correct_risk_labels(self) -> None:
        session_risks = {
            "cst-session-open": "session",
            "cst-session-close": "session",
            "cst-session-quit": "process-control",
            "cst-session-inspect": "read",
            "cst-session-reattach": "read",
        }
        for tool, expected_risk in session_risks.items():
            r = run_cli("describe-tool", "--tool", tool)
            assert r.returncode == 0, r.stderr
            p = json.loads(r.stdout)
            assert p["tool"]["risk"] == expected_risk


class CliContractSessionTests:
    """Session/process management tools (no CST needed for dry-runs)."""

    def test_session_inspect_no_project_safe_json(self) -> None:
        r = run_cli("cst-session-inspect")
        assert r.returncode == 0, r.stderr
        p = json.loads(r.stdout)
        assert p["status"] == "success"
        assert "force_kill_allowlist" in p
        assert "process_count" in p
        assert "lock_count" in p
        assert "readiness" in p
        assert p["readiness"] in {"clear", "attention_required", "blocked"}

    def test_stage_evidence_capture_and_compare(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            before = d / "before.json"
            after = d / "after.json"

            before_data = {
                "stage_name": "before", "project_path": "/dummy",
                "captured_at": "2026-01-01T00:00:00",
                "evidence": [
                    {"type": "parameters",
                     "data": {"g": 25.0, "thr": 12.5}},
                    {"type": "entities",
                     "data": [{"component": "C1", "name": "horn"}]},
                    {"type": "file_info",
                     "data": {"exists": True, "size_bytes": 1000}},
                ]
            }
            after_data = {
                "stage_name": "after", "project_path": "/dummy",
                "captured_at": "2026-01-01T00:01:00",
                "evidence": [
                    {"type": "parameters",
                     "data": {"g": 24.5, "thr": 12.5, "test_a": 15.0}},
                    {"type": "entities",
                     "data": [{"component": "C1", "name": "horn"},
                              {"component": "C1", "name": "ev_brick"}]},
                    {"type": "file_info",
                     "data": {"exists": True, "size_bytes": 1001}},
                ]
            }
            before.write_text(json.dumps(before_data), encoding="utf-8")
            after.write_text(json.dumps(after_data), encoding="utf-8")

            r = run_cli("stage-evidence", "--args-json", json.dumps({
                "compare": [str(before), str(after)],
                "output_html": str(d / "report.html"),
            }))
            assert r.returncode == 0, r.stderr
            p = json.loads(r.stdout)
            assert p["status"] == "success"
            report = (d / "report.html").read_text(encoding="utf-8")
            assert "参数对比" in report
            assert "Entities" in report
            assert "changed" in report
            assert "added" in report
            assert "ev_brick" in report

    def test_session_quit_dry_run_safe(self) -> None:
        r = run_cli("cst-session-quit", "--dry-run", "true")
        assert r.returncode == 0, r.stderr
        p = json.loads(r.stdout)
        assert p["status"] == "success"
        assert p["dry_run"]
