"""将 cst_runtime 部署到供 Python 3.9 worker 使用的目录。

Usage:
  <Python 3.9 worker> bootstrap.py --skill-path <skill-root>\\scripts

Agent flow:
  1. Read this file from skill -> Write as bootstrap.py at workspace root
  2. <Python 3.9 worker> bootstrap.py --skill-path <skill-root>\\scripts
  3. If status=need_fallback: agent writes files manually -> retry
  4. On status=ready: delete bootstrap.py

After success:
  由 cst-mcp 使用配置的 worker executable 启动 cst_runtime。
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> int:
    if sys.version_info[:2] != (3, 9):
        print("status=error")
        print("message=cst-runtime 必须由 CST 兼容的 Python 3.9 worker 部署；请设置 CST_WORKER_PYTHON 后重试。")
        return 1
    ws = Path.cwd().resolve()
    dst = ws / ".cst_runtime"

    skill_scripts = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--skill-path" and i + 1 < len(sys.argv):
            skill_scripts = Path(sys.argv[i + 1]).resolve()
            break

    if skill_scripts:
        src_mod = skill_scripts / "cst_runtime"
        if not src_mod.is_dir():
            print("status=error")
            print("message=--skill-path must point to scripts/ dir containing cst_runtime/")
            return 1
        dst.mkdir(parents=True, exist_ok=True)
        dst_mod = dst / "cst_runtime"
        if dst_mod.exists():
            shutil.rmtree(dst_mod)
        try:
            shutil.copytree(src_mod, dst_mod, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        except PermissionError:
            print("status=need_fallback")
            print(f"message=Permission denied. Agent: read cst_runtime/ files from skill and write to {dst_mod}")
            return 1

        ref_src = skill_scripts.parent / "references"
        if ref_src.exists():
            dst_ref = dst / "references"
            if dst_ref.exists():
                shutil.rmtree(dst_ref)
            shutil.copytree(ref_src, dst_ref, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

        (dst / "pyproject.toml").write_text(
            "[project]\n"
            'name = "cst-runtime"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.9,<3.10"\n'
            "\n"
            "[build-system]\n"
            'requires = ["setuptools"]\n'
            'build-backend = "setuptools.build_meta"\n'
            "\n"
            "[tool.setuptools.packages.find]\n"
            'where = ["."]\n',
            encoding="utf-8",
        )

    if not (dst / "cst_runtime").is_dir():
        print("status=error")
        print("message=.cst_runtime/cst_runtime/ not found. Provide --skill-path or run fallback first.")
        return 1

    print("status=ready")
    print(f"runtime_source={dst.resolve()}")
    print("message=已部署 cst-runtime；在 cst-mcp 的 .cst_config.json 中设置 runtime.source_path，并由 Python 3.9 worker 启动。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
