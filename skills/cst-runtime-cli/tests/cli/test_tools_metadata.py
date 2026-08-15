"""Tool metadata: listing, sampled describe/args-template, and error paths.

全量「每个工具都有合法 schema/模板/处理器」的不变量由进程内的
test_arch_invariants.py 与 test_schema_type_consistency.py 承担；本文件只保留
子进程 CLI 边界的抽样冒烟，避免每工具一次子进程的 ~60s 开销。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from helpers import run_cli

pytestmark = pytest.mark.subprocess

_SAMPLE_TOOLS = [
    "health-check",
    "list-materials",
    "init-workspace",
    "record-stage",
    "update-status",
    "wait-project-unlocked",
    "infer-run-dir",
    "plot-exported-file",
    "calculate-farfield-neighborhood-flatness",
    "stage-evidence",
    "create-study",
    "analyze-metasurface-sparameters",
]


def get_all_tool_names() -> list[str]:
    result = run_cli("list-tools")
    payload = json.loads(result.stdout)
    return [t["name"] for t in payload["tools"]]


class TestToolsMetadata:
    """Every tool has valid metadata, args template, and consistent JSON output."""

    def test_all_tools_are_listed(self) -> None:
        names = get_all_tool_names()
        assert len(names) > 50, f"Only {len(names)} tools found"
        assert "add-to-history" not in names
        assert "activate-post-process" not in names

    def test_sampled_tools_describe_returns_success(self) -> None:
        for tool in _SAMPLE_TOOLS:
            r = run_cli("describe-tool", "--tool", tool)
            assert r.returncode == 0, r.stderr[:200]
            p = json.loads(r.stdout)
            assert p["status"] == "success"
            assert p["tool"]["name"] == tool
            assert "category" in p["tool"]
            assert "risk" in p["tool"]
            assert "description" in p["tool"]

    def test_sampled_tools_have_args_template(self) -> None:
        for tool in _SAMPLE_TOOLS:
            r = run_cli("args-template", "--tool", tool)
            assert r.returncode == 0, r.stderr[:200]
            p = json.loads(r.stdout)
            assert p["status"] == "success"
            assert p["tool"] == tool
            assert isinstance(p["args_template"], dict)

    def test_args_template_writes_valid_json_file(self) -> None:
        for tool in _SAMPLE_TOOLS[:6]:
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
