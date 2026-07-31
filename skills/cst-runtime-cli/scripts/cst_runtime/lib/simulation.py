"""稳定的仿真业务门面。"""
from __future__ import annotations

from ..core import simulation as _core
from ._facade import wrap_core


_PUBLIC_OPERATIONS = (
    "start_simulation",
    "start_simulation_async",
    "is_simulation_running",
    "stop_simulation",
    "pause_simulation",
    "resume_simulation",
    "set_solver_acceleration",
    "set_fdsolver_extrude_open_bc",
    "set_mesh_fpbavoid_nonreg_unite",
    "set_mesh_minimum_step_number",
)

for _name in _PUBLIC_OPERATIONS:
    globals()[_name] = wrap_core(getattr(_core, _name))

__all__ = list(_PUBLIC_OPERATIONS)
