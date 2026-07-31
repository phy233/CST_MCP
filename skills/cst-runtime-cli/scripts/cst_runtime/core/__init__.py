"""CST core 层初始化。

仅从显式环境变量或系统 Program Files 根目录探测 CST，不读取项目打包配置，
也不包含开发机绝对路径。
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path


def _candidate_library_paths() -> list[Path]:
    configured = os.environ.get("CST_PYTHON_LIBS", "")
    candidates = [
        Path(value).expanduser()
        for value in configured.split(os.pathsep)
        if value.strip()
    ]
    program_roots = {
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("ProgramW6432"),
    }
    for raw_root in program_roots:
        if not raw_root:
            continue
        root = Path(raw_root)
        if not root.is_dir():
            continue
        try:
            for child in root.iterdir():
                if child.is_dir() and child.name.startswith("CST Studio Suite"):
                    candidates.append(
                        child / "AMD64" / "python_cst_libraries"
                    )
        except PermissionError:
            continue
    return candidates


for _candidate in _candidate_library_paths():
    if _candidate.is_dir():
        _value = str(_candidate.resolve())
        if _value not in sys.path:
            sys.path.insert(0, _value)
        break

warnings.filterwarnings("ignore", category=DeprecationWarning)
