"""仓库根级 Pytest 配置：分层门控 + Windows 沙箱临时目录适配。

本文件是全仓唯一登记 --run-cst / --run-cst-solver 选项与真机跳过的位置；
标记名称本身以 pyproject.toml 的 markers 声明为唯一事实源。

另外，Windows 沙箱会把 POSIX 模式位 0o700 翻译成限制性 ACL，导致 pytest 的
tmp_path/tmpdir 与 tempfile.TemporaryDirectory 创建的目录在同一进程内
都无法枚举、写入或删除（PermissionError）。Windows 本就不使用 POSIX
权限位，这里在测试进程内把 0o700 恢复为默认模式；仅影响 pytest 测试
进程，生产代码与 cst_runtime 运行时不加载本 conftest，不受影响。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest


def _install_sandbox_safe_mode_shim() -> None:
    """把 0o700 目录模式位恢复为默认；带重入保护，可安全重复加载。"""
    if sys.platform != "win32":
        return
    import pathlib

    if getattr(pathlib.Path, "_cst_mcp_sandbox_shim", False):
        return
    pathlib.Path._cst_mcp_sandbox_shim = True  # type: ignore[attr-defined]

    _original_pathlib_mkdir = pathlib.Path.mkdir

    def _sandbox_safe_mkdir(
        self: pathlib.Path,
        mode: int = 0o777,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        if mode == 0o700:
            mode = 0o777
        return _original_pathlib_mkdir(
            self, mode=mode, parents=parents, exist_ok=exist_ok
        )

    pathlib.Path.mkdir = _sandbox_safe_mkdir  # type: ignore[method-assign]

    _original_os_chmod = os.chmod

    def _sandbox_safe_chmod(path: Any, mode: int, *args: Any, **kwargs: Any) -> None:
        if mode == 0o700:
            mode = 0o777
        return _original_os_chmod(path, mode, *args, **kwargs)

    os.chmod = _sandbox_safe_chmod  # type: ignore[method-assign]

    # tempfile.mkdtemp/TemporaryDirectory 直接以 mode=0o700 调用 os.mkdir，
    # 同样需要把模式位恢复为默认，否则沙箱会施加限制性 ACL。
    _original_os_mkdir = os.mkdir

    def _sandbox_safe_os_mkdir(
        path: Any, mode: int = 0o777, *args: Any, **kwargs: Any
    ) -> None:
        if mode == 0o700:
            mode = 0o777
        return _original_os_mkdir(path, mode, *args, **kwargs)

    os.mkdir = _sandbox_safe_os_mkdir  # type: ignore[method-assign]

    _original_os_makedirs = os.makedirs

    def _sandbox_safe_os_makedirs(
        path: Any, mode: int = 0o777, exist_ok: bool = False
    ) -> None:
        if mode == 0o700:
            mode = 0o777
        return _original_os_makedirs(path, mode, exist_ok=exist_ok)

    os.makedirs = _sandbox_safe_os_makedirs  # type: ignore[method-assign]


_install_sandbox_safe_mode_shim()


def _worker_python_available() -> bool:
    """判断 py39 Worker 解释器是否存在（worker_proxy 分层自动跳过的依据）。"""
    configured = os.environ.get("CST_WORKER_PYTHON")
    if configured and Path(configured).expanduser().is_file():
        return True
    user_home = Path.home()
    for candidate in (
        user_home / "miniconda3" / "envs" / "cst39" / "python.exe",
        user_home / "anaconda3" / "envs" / "cst39" / "python.exe",
    ):
        if candidate.is_file():
            return True
    return False


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-cst",
        action="store_true",
        default=False,
        help="显式运行需要真实 CST 2022 和许可证的串行集成测试",
    )
    parser.addoption(
        "--run-cst-solver",
        action="store_true",
        default=False,
        help="在 --run-cst 前提下额外运行会短暂启停求解器的 cst_solver 测试",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """分层门控：默认绝不启动 CST；求解器用例还需二次显式开启。"""
    run_cst = config.getoption("--run-cst")
    run_solver = config.getoption("--run-cst-solver")
    skip_cst = pytest.mark.skip(reason="使用 --run-cst 后才运行真实 CST 集成测试")
    skip_solver = pytest.mark.skip(
        reason="使用 --run-cst --run-cst-solver 后才运行求解器测试"
    )
    skip_worker = pytest.mark.skip(reason="未找到 Python 3.9 Worker 解释器（CST_WORKER_PYTHON）")
    for item in items:
        if "cst_integration" in item.keywords:
            if not run_cst:
                item.add_marker(skip_cst)
            elif "cst_solver" in item.keywords and not run_solver:
                item.add_marker(skip_solver)
        if "worker_proxy" in item.keywords and not _worker_python_available():
            item.add_marker(skip_worker)
