"""仓库根级 Pytest 配置：Windows 沙箱下的临时目录模式位适配。

沙箱会把 POSIX 模式位 0o700 翻译成限制性 ACL，导致 pytest 的
tmp_path/tmpdir 与 tempfile.TemporaryDirectory 创建的目录在同一进程内
都无法枚举、写入或删除（PermissionError）。Windows 本就不使用 POSIX
权限位，这里在测试进程内把 0o700 恢复为默认模式；仅影响 pytest 测试
进程，生产代码与 cst_runtime 运行时不加载本 conftest，不受影响。
"""
from __future__ import annotations

import os
import sys
from typing import Any

if sys.platform == "win32":
    import pathlib

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
