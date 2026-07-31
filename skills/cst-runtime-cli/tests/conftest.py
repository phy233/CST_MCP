"""Pytest fixtures for cst-runtime-cli tests."""
import sys
import json
import os
import subprocess
from pathlib import Path

SKILL_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import pytest
from unittest import mock


# 这些文件是需要人工观察 CST GUI 的脚本，不是可独立收集的单元测试。
collect_ignore = [
    "test_interactive.py",
    "test_return.py",
    "test_introspection.py",
    "test_lib_automated.py",
    "test_buffer.py",
    "test_translate_zero.py",
]


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "cst_integration: 需要真实 CST 安装和许可证的串行集成测试",
    )
    config.addinivalue_line(
        "markers",
        "cst_destructive: 会关闭会话、退出进程或不可逆修改工程的真机测试",
    )


@pytest.fixture
def mocker(monkeypatch):
    """项目内置的轻量 pytest-mock 兼容 fixture，避免额外测试依赖。"""
    class Mocker:
        MagicMock = mock.MagicMock

    active_patchers = []

    class ManagedMocker(Mocker):
        @staticmethod
        def patch(target, *args, **kwargs):
            patcher = mock.patch(target, *args, **kwargs)
            active_patchers.append(patcher)
            return patcher.start()

    yield ManagedMocker()
    for patcher in reversed(active_patchers):
        patcher.stop()


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


@pytest.fixture(scope="session")
def cst_runtime_session():
    """整批真机测试复用一个 CST 进程，并在最后统一退出。"""
    project_path = os.environ.get("CST_TEST_PROJECT")
    if not project_path:
        pytest.skip("设置 CST_TEST_PROJECT 后才运行真实 CST 集成测试")
    yield {"base_project": str(Path(project_path).expanduser().resolve())}
    from cst_runtime.lib.session import quit_cst

    quit_cst(force_global_cleanup=False)


@pytest.fixture(scope="module")
def cst_domain_project(cst_runtime_session, tmp_path_factory, request):
    """同一测试模块共享一个工程副本，只在模块边界打开和关闭。"""
    import shutil

    from cst_runtime.lib.session import close_project, open_project

    source = Path(cst_runtime_session["base_project"])
    domain_dir = tmp_path_factory.mktemp(f"cst_{request.module.__name__.split('.')[-1]}")
    working = domain_dir / source.name
    shutil.copy2(str(source), str(working))
    source_companion = source.with_suffix("")
    if source_companion.is_dir():
        shutil.copytree(str(source_companion), str(working.with_suffix("")))

    opened = open_project(str(working))
    opened.raise_for_error()
    yield str(working)
    close_project(str(working), save=False).raise_for_error()


@pytest.fixture
def temp_workspace(tmp_path, run_cli):
    """Create a temporary workspace."""
    import tempfile
    # init-workspace needs a real path
    r = run_cli("init-workspace", "--workspace", str(tmp_path))
    assert r["status"] == "success"
    return tmp_path
