"""稳定的工程身份和锁管理门面。"""
from __future__ import annotations

from ..core import identity as _core
from ._facade import wrap_core


list_open_projects = wrap_core(_core.list_open_projects)
verify_project_identity = wrap_core(_core.verify_project_identity)
wait_project_unlocked = wrap_core(_core.wait_project_unlocked)


def infer_run_dir_from_project(project_path: str):
    """返回运行目录；该值仅供 lib 和协议适配层组织响应。"""
    return _core.infer_run_dir_from_project(project_path)


__all__ = [
    "list_open_projects",
    "verify_project_identity",
    "wait_project_unlocked",
    "infer_run_dir_from_project",
]
