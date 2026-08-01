from __future__ import annotations

from .base import (
    CompatibilityProfile,
    compatibility_metadata,
    detect_compatibility_profile,
    get_model3d,
    profile_for,
    reset_profile_cache,
    unsupported_feature,
)
from .session import (
    activate_project,
    active_project,
    connect_design_environment,
    connect_to_any_design_environment,
    create_design_environment,
    design_environment_pid,
    get_open_project,
    has_active_project,
    list_open_project_paths,
    running_design_environment_pids,
)
from .parameters import supports_parameter_api
from .parameters import list_parameter_values
from .farfield import (
    supports_farfield_calculator,
    get_farfield_calculator,
    legacy_farfield_query_vba,
    read_legacy_farfield_list,
)
from .tree import get_tree_items, result_item_exists, select_tree_item
from .materials import list_material_names
from .results import (
    supports_2d_results,
    get_result2d_item,
    get_colormap_items,
    list_all_result_items,
)
from .queries import delete_project_results, get_project_solver_type
from .modeling import CompatibleVBA

__all__ = [
    "get_model3d",
    "CompatibilityProfile",
    "compatibility_metadata",
    "detect_compatibility_profile",
    "profile_for",
    "reset_profile_cache",
    "unsupported_feature",
    "activate_project",
    "active_project",
    "connect_design_environment",
    "connect_to_any_design_environment",
    "create_design_environment",
    "design_environment_pid",
    "get_open_project",
    "has_active_project",
    "list_open_project_paths",
    "list_material_names",
    "running_design_environment_pids",
    "supports_parameter_api",
    "list_parameter_values",
    "supports_farfield_calculator",
    "get_farfield_calculator",
    "legacy_farfield_query_vba",
    "read_legacy_farfield_list",
    "get_tree_items",
    "result_item_exists",
    "select_tree_item",
    "supports_2d_results",
    "get_result2d_item",
    "get_colormap_items",
    "list_all_result_items",
    "delete_project_results",
    "get_project_solver_type",
    "CompatibleVBA",
]
