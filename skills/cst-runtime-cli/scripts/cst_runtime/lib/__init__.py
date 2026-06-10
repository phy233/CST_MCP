"""cst_runtime.lib — CST 控制公开 API

标准库风格，每个模块可独立 import:

    from cst_runtime.lib.parameters import list_params, set_param
    from cst_runtime.lib.geometry import brick, boolean_subtract
    from cst_runtime.lib.results import get_sparam
    from cst_runtime.lib.solver import start, wait, is_running

或统一导入:

    from cst_runtime import lib
    lib.parameters.list_params("C:\\path\\to\\model.cst")
"""
from . import (
    session,
    parameters,
    geometry,
    materials,
    mesh,
    boundary,
    port,
    solver,
    monitors,
    results,
    farfield,
    optimization,
    array,
    unit_cells,
    sweep,
    cross_process,
)

__all__ = [
    "session", "parameters", "geometry", "materials", "mesh",
    "boundary", "port", "solver", "monitors", "results",
    "farfield", "optimization", "array", "unit_cells", "sweep",
    "cross_process",
]
