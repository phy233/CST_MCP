"""超表面电磁设置的稳定 facade。"""
from __future__ import annotations

from ..core import em_setup as _core
from ._facade import wrap_core


define_unit_cell_boundary = wrap_core(_core.define_unit_cell_boundary)
inspect_boundary = wrap_core(_core.inspect_boundary)
define_floquet_port = wrap_core(_core.define_floquet_port)
inspect_floquet_ports = wrap_core(_core.inspect_floquet_ports)
define_plane_wave = wrap_core(_core.define_plane_wave)
inspect_plane_wave = wrap_core(_core.inspect_plane_wave)
configure_frequency_domain_solver = wrap_core(_core.configure_frequency_domain_solver)
list_monitors = wrap_core(_core.list_monitors)


__all__ = [
    "configure_frequency_domain_solver",
    "define_floquet_port",
    "define_plane_wave",
    "define_unit_cell_boundary",
    "inspect_boundary",
    "inspect_floquet_ports",
    "inspect_plane_wave",
    "list_monitors",
]
