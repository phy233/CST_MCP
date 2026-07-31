"""稳定的 CST 工程业务门面。"""
from __future__ import annotations

from ..core import project as _core
from ._facade import wrap_core


save_project = wrap_core(_core.save_project)
list_parameters = wrap_core(_core.list_parameters)
list_entities = wrap_core(_core.list_entities)
change_parameter = wrap_core(_core.change_parameter)
define_parameters = wrap_core(_core.define_parameters)

__all__ = [
    "save_project",
    "list_parameters",
    "list_entities",
    "change_parameter",
    "define_parameters",
]
