"""cst_runtime.core — CST path auto-detection at import time."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Any

_CST_SEARCH_PATHS: list[str] = [
    r"C:\Program Files\CST Studio Suite 2026\AMD64\python_cst_libraries",
    r"C:\Program Files\CST Studio Suite 2025\AMD64\python_cst_libraries",
    r"C:\Program Files (x86)\CST Studio Suite 2026\AMD64\python_cst_libraries",
]

_cst_found = False
try:
    _pp = Path.cwd().resolve() / "pyproject.toml"
    if _pp.exists():
        import tomllib
        _src = tomllib.loads(_pp.read_text(encoding="utf-8")).get("tool", {}).get("uv", {}).get("sources", {}).get("cst-studio-suite-link", {})
        if isinstance(_src, dict) and _src.get("path"):
            _p = Path(_src["path"]).resolve()
            if str(_p) not in sys.path:
                sys.path.insert(0, str(_p))
                _cst_found = True
except Exception:
    pass

if not _cst_found:
    for _p in _CST_SEARCH_PATHS:
        if Path(_p).is_dir() and str(_p) not in sys.path:
            sys.path.insert(0, _p)
            break

warnings.filterwarnings("ignore", category=DeprecationWarning)
