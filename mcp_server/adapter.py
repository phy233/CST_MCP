"""Adapter: auto-register cst_runtime.lib functions as MCP tools.

This module scans cst_runtime.lib and registers each public function
as an MCP tool with proper description and risk tagging.
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable

from .config import get_config

# Ensure cst_runtime is importable
_config = get_config()
_crt_scripts = str(_config.cst_runtime_root)
if _crt_scripts not in sys.path:
    sys.path.insert(0, _crt_scripts)


def _make_json_serializable(obj: Any) -> Any:
    """Convert object to JSON-serializable format."""
    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_json_serializable(item) for item in obj]
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "__dict__"):
        return _make_json_serializable(vars(obj))
    return obj


def _wrap_lib_function(
    fn: Callable,
    tool_name: str,
    description: str,
    risk: str = "read",
) -> Callable:
    """Wrap a lib function as an MCP tool handler.

    Args:
        fn: The lib function to wrap
        tool_name: MCP tool name (kebab-case)
        description: Human-readable description
        risk: Risk level (read/write/session/long-running)

    Returns:
        Async handler function for MCP
    """
    # Get function signature for documentation
    try:
        sig = inspect.signature(fn)
        params_doc = []
        for name, param in sig.parameters.items():
            if param.default is inspect.Parameter.empty:
                params_doc.append(f"  {name}: required")
            else:
                params_doc.append(f"  {name}: optional (default={param.default})")
        params_section = "\n".join(params_doc) if params_doc else "  (no parameters)"
    except (ValueError, TypeError):
        params_section = "  (signature unavailable)"

    risk_tag = {
        "read": "[READ]",
        "write": "[WRITE]",
        "session": "[SESSION]",
        "long-running": "[LONG-RUNNING]",
    }.get(risk, f"[{risk.upper()}]")

    full_doc = f"{risk_tag} {description}\n\nParameters:\n{params_section}"

    async def handler(**kwargs: Any) -> str:
        try:
            # Call the lib function
            result = fn(**kwargs)

            # Handle different return types
            if result is None:
                return json.dumps({"status": "success"}, ensure_ascii=False, indent=2)

            if isinstance(result, str):
                return result

            if isinstance(result, dict):
                result = _make_json_serializable(result)
                return json.dumps(result, ensure_ascii=False, indent=2, default=str)

            if isinstance(result, (list, tuple)):
                result = _make_json_serializable(result)
                return json.dumps(result, ensure_ascii=False, indent=2, default=str)

            # For other types (bool, int, float)
            return json.dumps({"value": result}, ensure_ascii=False, indent=2)

        except KeyError as e:
            return json.dumps(
                {"status": "error", "error_type": "KeyError", "message": str(e)},
                ensure_ascii=False,
                indent=2,
            )
        except RuntimeError as e:
            return json.dumps(
                {"status": "error", "error_type": "RuntimeError", "message": str(e)},
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            return json.dumps(
                {"status": "error", "error_type": type(e).__name__, "message": str(e)},
                ensure_ascii=False,
                indent=2,
            )

    handler.__name__ = tool_name.replace("-", "_")
    handler.__doc__ = full_doc
    return handler


# Tool specifications: (lib_module_name, func_name, mcp_tool_name, description, risk)
TOOL_SPECS: list[tuple[str, str, str, str, str]] = [
    # Session management
    ("session", "open_project", "open-project", "Open a CST project", "session"),
    ("session", "close_project", "close-project", "Close a CST project", "session"),
    ("session", "inspect", "inspect-session", "Inspect CST environment state", "read"),
    ("session", "quit_cst", "quit-cst", "Quit CST Design Environment", "session"),
    ("session", "list_open", "list-open-projects", "List all open CST projects", "read"),
    ("session", "is_locked", "is-project-locked", "Check if a CST project is locked", "read"),

    # Parameters
    ("parameters", "list_params", "list-parameters", "List all parameters with values", "read"),
    ("parameters", "get_param", "get-parameter", "Get a single parameter value", "read"),
    ("parameters", "set_param", "set-parameter", "Set a parameter value", "write"),
    ("parameters", "set_params", "set-parameters", "Set multiple parameters at once", "write"),
    ("parameters", "param_exists", "parameter-exists", "Check if a parameter exists", "read"),

    # Geometry
    ("geometry", "brick", "define-brick", "Create a brick solid", "write"),
    ("geometry", "cylinder", "define-cylinder", "Create a cylinder solid", "write"),
    ("geometry", "cone", "define-cone", "Create a cone solid", "write"),
    ("geometry", "rectangle", "define-rectangle", "Create a rectangle curve", "write"),
    ("geometry", "boolean_add", "boolean-add", "Boolean add two solids", "write"),
    ("geometry", "boolean_subtract", "boolean-subtract", "Boolean subtract two solids", "write"),
    ("geometry", "boolean_intersect", "boolean-intersect", "Boolean intersect two solids", "write"),
    ("geometry", "delete_entity", "delete-entity", "Delete a solid entity", "write"),
    ("geometry", "delete_component", "delete-component", "Delete entire component folder", "write"),
    ("geometry", "rotate", "rotate-shape", "Rotate a solid", "write"),
    ("geometry", "translate", "translate-shape", "Translate (move) a solid", "write"),
    ("geometry", "mirror", "mirror-shape", "Mirror a solid", "write"),
    ("geometry", "activate_wcs", "activate-wcs", "Activate local working coordinate system", "write"),
    ("geometry", "deactivate_wcs", "deactivate-wcs", "Switch back to global WCS", "write"),
    ("geometry", "arc", "define-arc", "Create an arc curve", "write"),
    ("geometry", "polygon", "define-polygon", "Create a polygon solid from vertices", "write"),

    # Materials
    ("materials", "define", "define-material", "Create material with inline properties", "write"),
    ("materials", "define_from_mtd", "define-material-from-mtd", "Load material from .mtd file", "write"),
    ("materials", "list_materials", "list-materials", "List available materials", "read"),
    ("materials", "exists", "material-exists", "Check if material exists", "read"),
    ("materials", "set_material", "set-material", "Modify entity material", "write"),

    # Mesh
    ("mesh", "settings", "set-mesh-settings", "Configure mesh settings", "write"),
    ("mesh", "acceleration", "set-mesh-acceleration", "Configure mesh acceleration", "write"),
    ("mesh", "set_minimum_step_number", "set-mesh-min-step", "Set minimum mesh step number", "write"),
    ("mesh", "set_fpbavoid_nonreg_unite", "set-mesh-fpb-avoid", "Set FPB avoid non-regular unite", "write"),

    # Boundary
    ("boundary", "set_all", "define-boundary", "Set all faces to same boundary type", "write"),
    ("boundary", "set_per_face", "define-boundary-per-face", "Set boundary per face", "write"),
    ("boundary", "set_unit_cell", "define-unit-cell-boundary", "Set unit cell boundary", "write"),

    # Port
    ("port", "define_waveguide", "define-waveguide-port", "Define a waveguide port", "write"),
    ("port", "define_floquet", "define-floquet-port", "Define Floquet port for periodic simulation", "write"),

    # Solver
    ("solver", "set_frequency_range", "define-frequency-range", "Set solver frequency range", "write"),
    ("solver", "start_async", "start-simulation", "Start solver (non-blocking)", "session"),
    ("solver", "is_running", "sim-status", "Check if solver is running", "read"),
    ("solver", "stop", "stop-simulation", "Stop the solver", "session"),
    ("solver", "rebuild", "rebuild-structure", "Rebuild geometry from parameters", "write"),
    ("solver", "delete_results", "delete-results", "Delete all simulation results", "write"),
    ("solver", "get_solver_type", "get-solver-type", "Get solver type", "read"),

    # Results
    ("results", "get_sparam", "get-1d-result", "Read S-parameter data", "read"),
    ("results", "get_sparam_at_freq", "get-sparam-at-freq", "Read S-param at specific frequency", "read"),
    ("results", "get_2d_field", "get-2d-result", "Read 2D field data", "read"),
    ("results", "list_items", "list-result-items", "List available result items", "read"),
    ("results", "list_sparams", "list-sparams", "List available S-parameters", "read"),
    ("results", "sparam_exists", "sparam-exists", "Check if S-parameter exists", "read"),
    ("results", "list_runs", "list-run-ids", "List simulation run IDs", "read"),
    ("results", "get_param_combo", "get-parameter-combination", "Get parameter combination for a run", "read"),
    ("results", "export_all", "export-run-results", "Export all results for a run", "read"),

    # Farfield
    ("farfield", "export_grid", "export-farfield-grid", "Export farfield grid data", "read"),
    ("farfield", "export_cut", "export-farfield-cut", "Export farfield cut data", "read"),
    ("farfield", "list_monitors", "inspect-farfield-monitors", "List farfield monitors", "read"),

    # Monitors
    ("monitors", "set_farfield", "set-farfield-monitor", "Set farfield monitor", "write"),
    ("monitors", "set_efield", "set-efield-monitor", "Set E-field monitor", "write"),
    ("monitors", "set_field", "set-field-monitor", "Set generic field monitor", "write"),
    ("monitors", "set_probe", "set-probe", "Set a probe", "write"),
    ("monitors", "delete_probe", "delete-probe", "Delete a probe", "write"),
    ("monitors", "delete_monitor", "delete-monitor", "Delete a monitor", "write"),

    # Optimization
    ("optimization", "create_study", "optuna-create-study", "Create an Optuna optimization study", "write"),
    ("optimization", "ask", "optuna-ask", "Get next parameter suggestion from Optuna", "read"),
    ("optimization", "tell", "optuna-tell", "Report result to Optuna study", "write"),
    ("optimization", "best", "optuna-best", "Get best parameters from Optuna study", "read"),

    # Array
    ("array", "build_coding_array", "build-coding-array", "Build coding metasurface array from matrix", "write"),
    ("array", "build_rectangular_array", "build-rectangular-array", "Build rectangular array of elements", "write"),
    ("array", "fast_array", "fast-array-modeling", "Fast array modeling via template copy", "write"),

    # Sweep (utility functions)
    ("sweep", "quick_sweep", "parameter-sweep", "Run parameter sweep and collect results", "long-running"),
]


def _import_lib_module(module_name: str):
    """Import a cst_runtime.lib module by name."""
    try:
        from cst_runtime import lib
        return getattr(lib, module_name, None)
    except ImportError as e:
        print(f"Warning: Could not import cst_runtime.lib.{module_name}: {e}", file=sys.stderr)
        return None


def register_all_tools(mcp) -> int:
    """Register all lib functions as MCP tools.

    Args:
        mcp: FastMCP server instance

    Returns:
        Number of tools registered
    """
    registered = 0
    config = get_config()

    for spec in TOOL_SPECS:
        module_name, func_name, tool_name, description, risk = spec

        # Skip write/session tools if disabled
        if risk == "write" and not config.enable_write_tools:
            continue
        if risk == "session" and not config.enable_session_tools:
            continue

        # Import module and get function
        module = _import_lib_module(module_name)
        if module is None:
            continue

        fn = getattr(module, func_name, None)
        if fn is None:
            print(
                f"Warning: Function '{func_name}' not found in cst_runtime.lib.{module_name}",
                file=sys.stderr,
            )
            continue

        # Create handler and register
        handler = _wrap_lib_function(fn, tool_name, description, risk)
        mcp.tool(name=tool_name, description=handler.__doc__)(handler)
        registered += 1

    return registered


def list_available_tools() -> list[dict[str, str]]:
    """List all available MCP tools without registering.

    Returns:
        List of tool info dicts
    """
    tools = []
    for spec in TOOL_SPECS:
        module_name, func_name, tool_name, description, risk = spec
        tools.append({
            "name": tool_name,
            "module": module_name,
            "function": func_name,
            "description": description,
            "risk": risk,
        })
    return tools
