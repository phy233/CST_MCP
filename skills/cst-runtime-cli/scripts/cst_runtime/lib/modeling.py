"""稳定的建模业务门面；具体 VBA、History 和 CST 对象位于 core。"""
from __future__ import annotations

from ..core import modeling as _core
from ._facade import wrap_core


_PUBLIC_OPERATIONS = (
    "define_material_from_mtd",
    "define_brick",
    "define_cylinder",
    "define_cone",
    "define_rectangle",
    "boolean_subtract",
    "boolean_add",
    "boolean_intersect",
    "boolean_insert",
    "delete_entity",
    "create_component",
    "change_material",
    "rename_entity",
    "set_entity_color",
    "define_units",
    "set_farfield_monitor",
    "set_efield_monitor",
    "set_field_monitor",
    "set_probe",
    "delete_probe_by_id",
    "delete_monitor",
    "set_background_with_space",
    "set_farfield_plot_cuts",
    "show_bounding_box",
    "activate_post_process_operation",
    "create_mesh_group",
    "define_polygon_3d",
    "define_analytical_curve",
    "define_extrude_curve",
    "transform_shape",
    "transform_curve",
    "create_horn_segment",
    "create_loft_sweep",
    "create_hollow_sweep",
    "add_to_history",
    "pick_face",
    "define_loft",
    "export_e_field",
    "export_surface_current",
    "export_voltage",
    "define_frequency_range",
    "change_solver_type",
    "define_background",
    "define_boundary",
    "define_mesh",
    "define_solver",
    "define_port",
    "define_monitor",
    "capture_3d_view",
)

for _name in _PUBLIC_OPERATIONS:
    globals()[_name] = wrap_core(getattr(_core, _name))

__all__ = list(_PUBLIC_OPERATIONS)
