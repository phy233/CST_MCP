"""工作区与运行上下文业务门面。"""
from ..core import workspace as _core
from ._facade import wrap_core

init_workspace = wrap_core(_core.init_workspace)
init_task = wrap_core(_core.init_task)
prepare_new_run = wrap_core(_core.prepare_new_run)
get_run_context = wrap_core(_core.get_run_context)
workspace_status = wrap_core(_core.workspace_status)


def find_workspace_marker(path):
    """查找工作区标记；仅供协议适配层定位上下文。"""
    return _core.find_workspace_marker(path)
