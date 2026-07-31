"""Pytest fixtures for cst-runtime-cli tests."""
import sys
import json
import os
import subprocess
from pathlib import Path

SKILL_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import pytest


@pytest.fixture(autouse=True)
def clear_gateway_registry():
    from cst_runtime.core.gateway import _registry, _dirty_marker_path, _farfield_marker_path
    for st in list(_registry.values()):
        for mk_path_func in (_dirty_marker_path, _farfield_marker_path):
            mk = mk_path_func(st.path)
            if mk.exists():
                try: mk.unlink()
                except Exception: pass
    _registry.clear()
    yield
    _registry.clear()


@pytest.fixture
def run_cli():
    """Run cst_runtime CLI via subprocess, return parsed JSON."""
    python = sys.executable
    skill_scripts = str(SKILL_SCRIPTS)
    inherited_pythonpath = os.environ.get("PYTHONPATH", "")
    pythonpath = (
        skill_scripts
        if not inherited_pythonpath
        else os.pathsep.join([skill_scripts, inherited_pythonpath])
    )

    def _run(*args):
        r = subprocess.run(
            [python, "-m", "cst_runtime", *args],
            capture_output=True, text=True, cwd=str(Path.cwd()),
            env={**os.environ, "PYTHONPATH": pythonpath},
        )
        return json.loads(r.stdout) if r.stdout.strip() else {"raw": r.stdout, "returncode": r.returncode}
    return _run


@pytest.fixture
def pp():
    """真实 CST 批处理测试使用的项目路径。"""
    project_path = os.environ.get("CST_TEST_PROJECT")
    if not project_path:
        pytest.skip("设置 CST_TEST_PROJECT 后才运行真实 CST 批处理测试")
    return project_path


@pytest.fixture
def temp_workspace(tmp_path, run_cli):
    """Create a temporary workspace."""
    import tempfile
    # init-workspace needs a real path
    r = run_cli("init-workspace", "--workspace", str(tmp_path))
    assert r["status"] == "success"
    return tmp_path
