import os
import sys
import inspect
import importlib.util

# Add cst_runtime path to sys.path
cst_runtime_path = r"D:\My_Program\Python\CST_MCP\skills\cst-runtime-cli\scripts"
if cst_runtime_path not in sys.path:
    sys.path.insert(0, cst_runtime_path)

MODULES_TO_EXPOSE = {
    "array": ["build_array"],
    "boundary": ["set_all", "set_per_face", "set_unit_cell"],
    "farfield": ["export_grid", "export_cut", "list_monitors"],
    "geometry": [
        "brick", "cylinder", "cone", "rectangle",
        "boolean_add", "boolean_subtract", "boolean_intersect",
        "delete_entity", "delete_component",
        "rotate", "mirror", "translate",
        "activate_wcs", "deactivate_wcs",
        "arc", "polygon"
    ],
    "materials": ["define", "define_from_mtd", "list_materials", "exists", "set_material"],
    "mesh": ["settings", "acceleration", "set_fpbavoid_nonreg_unite", "set_minimum_step_number"],
    "monitors": ["set_farfield", "set_efield", "set_field", "set_probe", "delete_probe", "delete_monitor"],
    "optimization": ["create_study", "ask", "tell", "best"],
    "parameters": ["list_params", "get_param", "set_param", "set_params", "param_exists"],
    "port": ["define_waveguide", "define_floquet"],
    "results": ["get_sparam", "get_sparam_at_freq", "get_2d_field", "list_items", "list_sparams", "sparam_exists", "list_runs", "get_param_combo", "export_all"],
    "session": ["open_project", "close_project", "create_blank_project", "save_project", "quit_cst"],
    "solver": ["start", "wait", "is_running", "stop", "rebuild", "delete_results", "set_frequency_range"],
    "sweep": ["quick_sweep"]
}

TOOLS_DIR = r"D:\My_Program\Python\CST_MCP\mcp_server\tools"

# Map python types to strings for code generation
def get_type_hint_str(type_hint):
    if type_hint == inspect.Signature.empty:
        return "Any"
    if hasattr(type_hint, '__name__'):
        return type_hint.__name__
    if hasattr(type_hint, '_name') and type_hint._name:
        # e.g. Tuple, List
        s = type_hint._name
        if hasattr(type_hint, '__args__') and type_hint.__args__:
            args_str = ", ".join([get_type_hint_str(a) for a in type_hint.__args__])
            return f"{s}[{args_str}]"
        return s
    
    # Generic representation
    s = str(type_hint)
    s = s.replace("typing.", "")
    if s == "NoneType":
        return "None"
    return s

def generate_tool_file(module_name, functions):
    try:
        mod = importlib.import_module(f"cst_runtime.lib.{module_name}")
    except ImportError as e:
        print(f"Failed to import {module_name}: {e}")
        return

    content = [
        f'"""MCP Tool definitions: CST {module_name.capitalize()} operations."""',
        "from typing import Any, Sequence, Tuple, List, Dict, Optional, Union",
        "",
        "from ..proxy import call_cst",
        ""
    ]

    tool_entries = []

    for func_name in functions:
        if not hasattr(mod, func_name):
            print(f"Warning: Function {func_name} not found in {module_name}")
            continue

        func = getattr(mod, func_name)
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        full_doc = doc if doc else f"Call {module_name}.{func_name}."
        # Indent the docstring properly for the generated function
        doc_lines = full_doc.split("\n")
        indented_doc = "\n".join([f"    {line}" if line else "" for line in doc_lines])
        
        # Add return type explicitly for the MCP client
        if "Returns:" not in indented_doc:
            indented_doc += "\n\n    Returns:\n        dict[str, Any]: The execution result from CST."

        args = []
        call_args = []
        for name, param in sig.parameters.items():
            type_str = get_type_hint_str(param.annotation)
            
            # special case Callable, Any
            if "Callable" in type_str:
                type_str = "Any"
            if "Sequence" in type_str:
                type_str = type_str.replace("Sequence", "list")
            
            if param.default == inspect.Parameter.empty:
                args.append(f"{name}: {type_str}")
            else:
                default_repr = repr(param.default)
                args.append(f"{name}: {type_str} = {default_repr}")
            
            call_args.append(f"{name}={name}")
        
        # We enforce dict[str, Any] as return type for all wrapper tools 
        # so FastMCP can properly marshal it, and since call_cst returns dict
        args_joined = ", ".join(args)
        call_args_joined = ", ".join(call_args)
        
        wrapper_name = func_name
        tool_name = func_name.replace("_", "-")
        
        func_content = [
            f"def {wrapper_name}({args_joined}) -> dict[str, Any]:",
            f'    """\n{indented_doc}\n    """',
            f'    return call_cst("lib.{module_name}", "{func_name}", {call_args_joined})',
            ""
        ]
        content.extend(func_content)
        tool_entries.append(f'    {{"name": "{tool_name}", "handler": {wrapper_name}}},')
    
    # Generate tools list
    list_name = f"{module_name.upper()}_TOOLS"
    content.append(f"{list_name} = [")
    content.extend(tool_entries)
    content.append("]")
    content.append("")
    
    filepath = os.path.join(TOOLS_DIR, f"{module_name}.py")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
    print(f"Generated {filepath}")

def generate_all():
    os.makedirs(TOOLS_DIR, exist_ok=True)
    
    for mod_name, funcs in MODULES_TO_EXPOSE.items():
        generate_tool_file(mod_name, funcs)
    
    # Generate __init__.py
    init_content = []
    all_tools_list = []
    for mod_name in MODULES_TO_EXPOSE.keys():
        list_name = f"{mod_name.upper()}_TOOLS"
        init_content.append(f"from .{mod_name} import {list_name}")
        all_tools_list.append(list_name)
    
    init_content.append("")
    init_content.append("# Aggregate all tools into a single list to be imported by the adapter")
    init_content.append(f"ALL_TOOLS = {' + '.join(all_tools_list)}")
    init_content.append("")
    
    init_path = os.path.join(TOOLS_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("\n".join(init_content))
    print(f"Generated {init_path}")

if __name__ == "__main__":
    generate_all()
