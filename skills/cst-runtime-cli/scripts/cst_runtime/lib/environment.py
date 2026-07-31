"""CST 运行环境业务门面。"""
from ..core import environment as _core
from ._facade import wrap_core

auto_register_cst = wrap_core(_core.auto_register_cst)
install_cst_libraries = wrap_core(_core.install_cst_libraries)
health_check = wrap_core(_core.health_check)
