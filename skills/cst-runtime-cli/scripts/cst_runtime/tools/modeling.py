"""modeling.py — modeling 工具定义"""
from . import _register_tool_defs


def _field_export_definition(handler: str, physical_name: str) -> dict:
    """构造按官方 Result Type 校验的场结果导出工具定义。"""
    return {
        "category": "results",
        "risk": "filesystem-write",
        "description": (
            f"Use this to export an existing {physical_name} result-tree node through CST 2022 "
            "ASCIIExport. Supply the exact full result_path; this is not a result-discovery "
            "tool and it writes the requested ASCII or CSV file."
        ),
        "handler": handler,
        "json_schema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "minLength": 1},
                "result_path": {"type": "string", "minLength": 1},
                "file_path": {"type": "string", "minLength": 1},
                "mode": {"type": "string", "enum": ["FixedNumber", "FixedWidth"], "default": "FixedNumber"},
                "step_x": {"type": ["number", "null"], "default": None},
                "step_y": {"type": ["number", "null"], "default": None},
                "step_z": {"type": ["number", "null"], "default": None},
                "point_file": {"type": "string", "default": ""},
                "subvolume": {
                    "type": ["array", "null"],
                    "items": {"type": "number"},
                    "minItems": 6,
                    "maxItems": 6,
                    "default": None,
                },
                "file_type": {"type": "string", "enum": ["ascii", "csv"], "default": "ascii"},
                "csv_separator": {"type": "string", "minLength": 1, "default": ","},
            },
            "required": ["project_path", "result_path", "file_path"],
            "additionalProperties": False,
        },
    }


TOOL_DEFS = {
"boolean-add": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to unite two existing solids into one solid when their combined volume is "
        "the intended geometry. The second solid is consumed; Curves items must be extruded "
        "before any Solid boolean operation."
    ),
    "handler": "tool_boolean_add",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "shape1": {
                "type": "string",
                "examples": [
                    "Component1:part1"
                ]
            },
            "shape2": {
                "type": "string",
                "examples": [
                    "Component1:part2"
                ]
            }
        },
        "required": [
            "project_path",
            "shape1",
            "shape2"
        ]
    },
},

"boolean-insert": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to apply CST Solid.Insert to two existing solids when the intended insert "
        "topology is explicit. Do not substitute boolean-add; navigation-tree retention follows "
        "CST Insert semantics, and Curves items are not valid inputs."
    ),
    "handler": "tool_boolean_insert",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "shape1": {
                "type": "string",
                "examples": [
                    "Component1:outer"
                ]
            },
            "shape2": {
                "type": "string",
                "examples": [
                    "Component1:insert"
                ]
            }
        },
        "required": [
            "project_path",
            "shape1",
            "shape2"
        ]
    },
},

"boolean-intersect": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to keep only the common volume of two existing solids. Do not use it for a "
        "union or a cutter subtraction, and extrude Curves items before calling."
    ),
    "handler": "tool_boolean_intersect",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "shape1": {
                "type": "string",
                "examples": [
                    "Component1:part1"
                ]
            },
            "shape2": {
                "type": "string",
                "examples": [
                    "Component1:part2"
                ]
            }
        },
        "required": [
            "project_path",
            "shape1",
            "shape2"
        ]
    },
},

"boolean-subtract": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to subtract a tool solid from a target solid when their design coordinates "
        "guarantee nonempty overlap. CST can report success for disjoint solids while leaving "
        "the target unchanged and consuming the tool, so establish overlap before calling."
    ),
    "handler": "tool_boolean_subtract",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "target": {
                "type": "string",
                "description": "Target solid that must geometrically overlap the subtraction tool.",
                "examples": [
                    "Component1:outer"
                ]
            },
            "tool": {
                "type": "string",
                "description": (
                    "Cutting solid. Ensure its coordinate ranges overlap the target; "
                    "a successful command alone does not prove that material was removed."
                ),
                "examples": [
                    "Component1:inner"
                ]
            }
        },
        "required": [
            "project_path",
            "target",
            "tool"
        ]
    },
},

"change-material": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to assign an existing CST material to an existing solid. Use list-materials "
        "only when the exact material name is unknown; this tool does not apply material to a "
        "Curves item."
    ),
    "handler": "tool_change_material",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "shape_name": {
                "type": "string",
                "examples": [
                    "Component1:my_brick"
                ]
            },
            "material": {
                "type": "string",
                "examples": [
                    "Copper (pure)"
                ]
            }
        },
        "required": [
            "project_path",
            "shape_name",
            "material"
        ]
    },
},

"create-component": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to create a component container before creating solids that require a "
        "component name. Do not call it for AnalyticalCurve, Polygon3D, or Rectangle items; "
        "those are stored under Curves."
    ),
    "handler": "tool_create_component",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "component_name": {
                "type": "string",
                "examples": [
                    "MyComponent"
                ]
            }
        },
        "required": [
            "project_path",
            "component_name"
        ]
    },
},

"create-hollow-sweep": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to create a hollow tapered solid between two rectangular profiles with an "
        "explicit wall thickness in active X/Y/Z or WCS U/V/W coordinates. Use "
        "create-loft-sweep for a filled rectangular loft."
    ),
    "handler": "tool_create_hollow_sweep",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "horn"
                ]
            },
            "component": {
                "type": "string",
                "examples": [
                    "HornAntenna"
                ]
            },
            "material": {
                "type": "string",
                "examples": [
                    "PEC"
                ]
            },
            "x_min1": {
                "type": "number",
                "description": "Lower X or U bound of profile 1.",
                "examples": [
                    -10
                ]
            },
            "x_max1": {
                "type": "number",
                "description": "Upper X or U bound of profile 1.",
                "examples": [
                    10
                ]
            },
            "y_min1": {
                "type": "number",
                "description": "Lower Y or V bound of profile 1.",
                "examples": [
                    -10
                ]
            },
            "y_max1": {
                "type": "number",
                "description": "Upper Y or V bound of profile 1.",
                "examples": [
                    10
                ]
            },
            "z1": {
                "type": "number",
                "description": "Z or W position of profile 1.",
                "examples": [
                    0
                ]
            },
            "x_min2": {
                "type": "number",
                "description": "Lower X or U bound of profile 2.",
                "examples": [
                    -35
                ]
            },
            "x_max2": {
                "type": "number",
                "description": "Upper X or U bound of profile 2.",
                "examples": [
                    35
                ]
            },
            "y_min2": {
                "type": "number",
                "description": "Lower Y or V bound of profile 2.",
                "examples": [
                    -35
                ]
            },
            "y_max2": {
                "type": "number",
                "description": "Upper Y or V bound of profile 2.",
                "examples": [
                    35
                ]
            },
            "z2": {
                "type": "number",
                "description": "Z or W position of profile 2.",
                "examples": [
                    50
                ]
            },
            "wall_thickness": {
                "type": "number",
                "examples": [
                    2.0
                ]
            }
        },
        "required": [
            "project_path",
            "name",
            "component",
            "material",
            "x_min1",
            "x_max1",
            "y_min1",
            "y_max1",
            "z1",
            "x_min2",
            "x_max2",
            "y_min2",
            "y_max2",
            "z2",
            "wall_thickness"
        ]
    },
},

"create-loft-sweep": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to create a filled tapered solid between two rectangular profiles in active "
        "X/Y/Z or WCS U/V/W coordinates. Use create-hollow-sweep when an explicit wall "
        "thickness is required."
    ),
    "handler": "tool_create_loft_sweep",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "horn_shell"
                ]
            },
            "component": {
                "type": "string",
                "examples": [
                    "HornAntenna"
                ]
            },
            "material": {
                "type": "string",
                "examples": [
                    "PEC"
                ]
            },
            "x_min1": {
                "type": "number",
                "description": "Lower X or U bound of profile 1.",
                "examples": [
                    -10
                ]
            },
            "x_max1": {
                "type": "number",
                "description": "Upper X or U bound of profile 1.",
                "examples": [
                    10
                ]
            },
            "y_min1": {
                "type": "number",
                "description": "Lower Y or V bound of profile 1.",
                "examples": [
                    -10
                ]
            },
            "y_max1": {
                "type": "number",
                "description": "Upper Y or V bound of profile 1.",
                "examples": [
                    10
                ]
            },
            "z1": {
                "type": "number",
                "description": "Z or W position of profile 1.",
                "examples": [
                    0
                ]
            },
            "x_min2": {
                "type": "number",
                "description": "Lower X or U bound of profile 2.",
                "examples": [
                    -35
                ]
            },
            "x_max2": {
                "type": "number",
                "description": "Upper X or U bound of profile 2.",
                "examples": [
                    35
                ]
            },
            "y_min2": {
                "type": "number",
                "description": "Lower Y or V bound of profile 2.",
                "examples": [
                    -35
                ]
            },
            "y_max2": {
                "type": "number",
                "description": "Upper Y or V bound of profile 2.",
                "examples": [
                    35
                ]
            },
            "z2": {
                "type": "number",
                "description": "Z or W position of profile 2.",
                "examples": [
                    50
                ]
            }
        },
        "required": [
            "project_path",
            "name",
            "component",
            "material",
            "x_min1",
            "x_max1",
            "y_min1",
            "y_max1",
            "z1",
            "x_min2",
            "x_max2",
            "y_min2",
            "y_max2",
            "z2"
        ]
    },
},

"create-mesh-group": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to group existing geometry items for later local mesh treatment. It does not "
        "configure the global mesh or solver; use the matching mesh and solver tools before "
        "simulation."
    ),
    "handler": "tool_create_mesh_group",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "group_name": {
                "type": "string",
                "examples": [
                    "fine_mesh"
                ]
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "examples": [
                    [
                        "solid1",
                        "solid2"
                    ]
                ]
            }
        },
        "required": [
            "project_path",
            "group_name",
            "items"
        ]
    },
},

"define-analytical-curve": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to create a parametric Curves item from differentiable coordinate laws over "
        "a parameter range in active X/Y/Z or WCS U/V/W coordinates. It creates no component, "
        "material, or solid; only a closed coplanar profile can later be extruded."
    ),
    "handler": "tool_define_analytical_curve",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "exp_curve"
                ]
            },
            "curve": {
                "type": "string",
                "examples": [
                    "curve1"
                ]
            },
            "law_x": {
                "type": "string",
                "description": "X(t), or U(t) with a local WCS.",
                "examples": [
                    "C1*exp(R*t)+C2"
                ]
            },
            "law_y": {
                "type": "string",
                "description": "Y(t), or V(t) with a local WCS.",
                "examples": [
                    "0"
                ]
            },
            "law_z": {
                "type": "string",
                "description": "Z(t), or W(t) with a local WCS.",
                "examples": [
                    "t"
                ]
            },
            "param_start": {
                "type": "string",
                "examples": [
                    "0"
                ]
            },
            "param_end": {
                "type": "string",
                "examples": [
                    "10"
                ]
            }
        },
        "required": [
            "project_path",
            "name",
            "curve",
            "law_x",
            "law_y",
            "law_z",
            "param_start",
            "param_end"
        ]
    },
},

"define-brick": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to create one axis-aligned solid brick with a user-selected component, "
        "material, and bounds in active X/Y/Z or WCS U/V/W coordinates. The tool does not "
        "choose dimensions, material, or topology for the user."
    ),
    "handler": "tool_define_brick",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "my_brick"
                ]
            },
            "component": {
                "type": "string",
                "examples": [
                    "Component1"
                ]
            },
            "material": {
                "type": "string",
                "examples": [
                    "PEC"
                ]
            },
            "x_min": {
                "type": ["number", "string"],
                "description": "Lower X or U bound.",
                "examples": [
                    -10
                ]
            },
            "x_max": {
                "type": ["number", "string"],
                "description": "Upper X or U bound.",
                "examples": [
                    10
                ]
            },
            "y_min": {
                "type": ["number", "string"],
                "description": "Lower Y or V bound.",
                "examples": [
                    -10
                ]
            },
            "y_max": {
                "type": ["number", "string"],
                "description": "Upper Y or V bound.",
                "examples": [
                    10
                ]
            },
            "z_min": {
                "type": ["number", "string"],
                "description": "Lower Z or W bound.",
                "examples": [
                    0
                ]
            },
            "z_max": {
                "type": ["number", "string"],
                "description": "Upper Z or W bound.",
                "examples": [
                    20
                ]
            }
        },
        "required": [
            "project_path",
            "name",
            "component",
            "material",
            "x_min",
            "x_max",
            "y_min",
            "y_max",
            "z_min",
            "z_max"
        ]
    },
},

"define-cone": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to create a cone or conical frustum along an active X/U, Y/V, or Z/W axis. "
        "bottom_radius is at axis_min, top_radius is at axis_max, and the two center inputs map "
        "to the transverse coordinates for the selected axis."
    ),
    "handler": "tool_define_cone",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "my_cone"
                ]
            },
            "component": {
                "type": "string",
                "examples": [
                    "Component1"
                ]
            },
            "material": {
                "type": "string",
                "examples": [
                    "PEC"
                ]
            },
            "bottom_radius": {
                "type": ["number", "string"],
                "examples": [
                    5
                ]
            },
            "top_radius": {
                "type": ["number", "string"],
                "examples": [
                    15
                ]
            },
            "axis": {
                "type": "string",
                "description": "Axis X/U, Y/V, or Z/W in the active coordinate system.",
                "examples": [
                    "z"
                ]
            },
            "axis_min": {
                "type": ["number", "string"],
                "description": "Lower bound along the selected axis.",
                "examples": [
                    0
                ]
            },
            "axis_max": {
                "type": ["number", "string"],
                "description": "Upper bound along the selected axis.",
                "examples": [
                    30
                ]
            },
            "x_center": {
                "type": ["number", "string"],
                "description": "First transverse center: Ycenter for axis x; Xcenter for axis y/z.",
                "examples": [
                    0
                ]
            },
            "y_center": {
                "type": ["number", "string"],
                "description": "Second transverse center: Zcenter for axis x/y; Ycenter for axis z.",
                "examples": [
                    0
                ]
            }
        },
        "required": [
            "project_path",
            "name",
            "component",
            "material",
            "bottom_radius",
            "top_radius",
            "axis",
            "axis_min",
            "axis_max",
            "x_center",
            "y_center"
        ]
    },
},

"define-cylinder": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to create a solid or hollow cylinder along an active X/U, Y/V, or Z/W axis; "
        "inner_radius=0 creates a solid cylinder. axis_min/axis_max set its length, and the "
        "center inputs map to the transverse coordinates for the selected axis."
    ),
    "handler": "tool_define_cylinder",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "my_cylinder"
                ]
            },
            "component": {
                "type": "string",
                "examples": [
                    "Component1"
                ]
            },
            "material": {
                "type": "string",
                "examples": [
                    "PEC"
                ]
            },
            "outer_radius": {
                "type": ["number", "string"],
                "examples": [
                    5
                ]
            },
            "inner_radius": {
                "type": ["number", "string"],
                "examples": [
                    0
                ]
            },
            "axis": {
                "type": "string",
                "description": "Axis X/U, Y/V, or Z/W in the active coordinate system.",
                "examples": [
                    "z"
                ]
            },
            "axis_min": {
                "type": ["number", "string"],
                "description": "Lower bound along the selected axis.",
                "examples": [
                    0
                ]
            },
            "axis_max": {
                "type": ["number", "string"],
                "description": "Upper bound along the selected axis.",
                "examples": [
                    20
                ]
            },
            "x_center": {
                "type": ["number", "string"],
                "description": "First transverse center: Ycenter for axis x; Xcenter for axis y/z.",
                "examples": [
                    0
                ]
            },
            "y_center": {
                "type": ["number", "string"],
                "description": "Second transverse center: Zcenter for axis x/y; Ycenter for axis z.",
                "examples": [
                    0
                ]
            }
        },
        "required": [
            "project_path",
            "name",
            "component",
            "material",
            "outer_radius",
            "inner_radius",
            "axis",
            "axis_min",
            "axis_max",
            "x_center",
            "y_center"
        ]
    },
},

"define-extrude-curve": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to convert one closed coplanar Curves item into a solid in an existing "
        "component and material; the source curve is consumed. Positive thickness follows the "
        "profile's ordered normal and negative thickness reverses it, so determine the sign first."
    ),
    "handler": "tool_define_extrude_curve",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "extruded_part"
                ]
            },
            "component": {
                "type": "string",
                "examples": [
                    "Component1"
                ]
            },
            "material": {
                "type": "string",
                "examples": [
                    "PEC"
                ]
            },
            "curve": {
                "type": "string",
                "description": "Full 'curve:item' name of a closed planar curve; CST 2022 consumes it on success.",
                "examples": [
                    "curve1:my_polygon"
                ]
            },
            "thickness": {
                "type": ["number", "string"],
                "description": "Signed distance: positive along n=(P2-P1) cross (P3-P1), negative along -n; compare directions in one coordinate system.",
                "examples": [
                    5
                ]
            }
        },
        "required": [
            "project_path",
            "name",
            "component",
            "material",
            "curve",
            "thickness"
        ]
    },
},

"define-loft": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this after pick-face has selected two surfaces in order to create a loft between "
        "them with explicit tangency and twist settings. CST 2022 defines no separate plane-normal "
        "input for this Loft operation."
    ),
    "handler": "tool_define_loft",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "loft_result"
                ]
            },
            "component": {
                "type": "string",
                "examples": [
                    "Component1"
                ]
            },
            "material": {
                "type": "string",
                "examples": [
                    "PEC"
                ]
            },
            "tangency": {
                "type": "integer",
                "examples": [
                    0
                ]
            },
            "minimize_twist": {
                "type": "boolean",
                "examples": [
                    True
                ]
            }
        },
        "required": [
            "project_path",
            "name",
            "component",
            "material",
            "tangency",
            "minimize_twist"
        ]
    },
},

"define-material-from-mtd": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to import a user-selected material by name from the Runtime "
        "references/Materials library into the CST project. Use list-materials only when the "
        "exact .mtd material name is unknown; this tool does not assign it to geometry."
    ),
    "handler": "tool_define_material_from_mtd",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "material_name": {
                "type": "string",
                "examples": [
                    "Copper (pure)"
                ]
            }
        },
        "required": [
            "project_path",
            "material_name"
        ]
    },
},

"define-polygon-3d": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to create an ordered Polygon3D item under Curves in active X/Y/Z or WCS U/V/W "
        "coordinates. It creates no component, material, or solid; close the point loop and keep "
        "it coplanar before extrusion."
    ),
    "handler": "tool_define_polygon_3d",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "my_polygon"
                ]
            },
            "curve": {
                "type": "string",
                "examples": [
                    "curve1"
                ]
            },
            "points": {
                "type": "array",
                "description": "Ordered active-coordinate points. Repeat the first point to close; verify n dot (Pi-P1)=0 before extrusion.",
                "items": {
                    "type": "array",
                    "items": {
                        "type": ["number", "string"]
                    },
                    "minItems": 3,
                    "maxItems": 3
                },
                "examples": [
                    [
                        [
                            "-10",
                            "0",
                            "0"
                        ],
                        [
                            "10",
                            "0",
                            "0"
                        ],
                        [
                            "10",
                            "0",
                            "10"
                        ],
                        [
                            "-10",
                            "0",
                            "10"
                        ],
                        [
                            "-10",
                            "0",
                            "0"
                        ]
                    ]
                ]
            }
        },
        "required": [
            "project_path",
            "name",
            "curve",
            "points"
        ]
    },
},

"define-rectangle": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to create a closed rectangular item under Curves in the active XY or WCS UV "
        "plane. It creates no component, material, or solid; use define-extrude-curve when a "
        "solid rectangle is required."
    ),
    "handler": "tool_define_rectangle",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "my_rect"
                ]
            },
            "curve": {
                "type": "string",
                "examples": [
                    "curve1"
                ]
            },
            "x_min": {
                "type": ["number", "string"],
                "description": "Minimum x bound, or minimum u bound when a local coordinate system is active.",
                "examples": [
                    -10
                ]
            },
            "x_max": {
                "type": ["number", "string"],
                "description": "Maximum x bound, or maximum u bound when a local coordinate system is active.",
                "examples": [
                    10
                ]
            },
            "y_min": {
                "type": ["number", "string"],
                "description": "Minimum y bound, or minimum v bound when a local coordinate system is active.",
                "examples": [
                    -5
                ]
            },
            "y_max": {
                "type": ["number", "string"],
                "description": "Maximum y bound, or maximum v bound when a local coordinate system is active.",
                "examples": [
                    5
                ]
            }
        },
        "required": [
            "project_path",
            "name",
            "curve",
            "x_min",
            "x_max",
            "y_min",
            "y_max"
        ]
    },
},

"define-units": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to set the CST project's length, frequency, and optional temperature units "
        "before entering dependent dimensions or frequencies. The units must come from the user "
        "or design specification."
    ),
    "handler": "tool_define_units",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "length": {
                "type": "string",
                "examples": [
                    "mm"
                ]
            },
            "frequency": {
                "type": "string",
                "examples": [
                    "GHz"
                ]
            },
            "temperature": {
                "type": "string",
                "enum": [
                    "Celsius",
                    "Kelvin",
                    "Fahrenheit"
                ],
                "default": "Celsius",
                "description": "CST temperature unit; omit it to keep Celsius."
            }
        },
        "required": [
            "project_path",
            "length",
            "frequency"
        ]
    },
},

"delete-entity": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this only for an explicit modeling correction to delete one known geometry entity. "
        "This is destructive; resolve the exact entity name first and do not repeat the call "
        "after success."
    ),
    "handler": "tool_delete_entity",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "component": {
                "type": "string",
                "examples": [
                    "Component1"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "temp_shape"
                ]
            }
        },
        "required": [
            "project_path",
            "component",
            "name"
        ]
    },
},

"delete-monitor": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this only for an explicit correction to delete one configured monitor by its exact "
        "name. It removes the monitor definition, not a saved result-tree item, and must not be "
        "repeated after success."
    ),
    "handler": "tool_delete_monitor",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "monitor_name": {
                "type": "string",
                "examples": [
                    "farfield (f=10)"
                ]
            }
        },
        "required": [
            "project_path",
            "monitor_name"
        ]
    },
},

"delete-probe": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this only for an explicit correction to delete one configured field probe by its "
        "exact ID. It removes the probe definition and must not be repeated after success."
    ),
    "handler": "tool_delete_probe",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "probe_id": {
                "type": "string",
                "examples": [
                    "1"
                ]
            }
        },
        "required": [
            "project_path",
            "probe_id"
        ]
    },
},

"list-field-results": {
    "category": "results",
    "risk": "read",
    "description": (
        "Use this to enumerate saved 2D or 3D field-result nodes with CST 2022 "
        "ResultTree.GetTreeResults, including official result types and backing files. Use "
        "list-monitors instead to inspect configured Monitor objects before solving."
    ),
    "handler": "tool_list_field_results",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string", "minLength": 1}
        },
        "required": ["project_path"],
        "additionalProperties": False
    },
},

"export-e-field": _field_export_definition("tool_export_e_field", "电场"),
"export-h-field": _field_export_definition("tool_export_h_field", "磁场"),
"export-surface-current": _field_export_definition("tool_export_surface_current", "表面电流"),
"export-power-flow": _field_export_definition("tool_export_power_flow", "功率流"),
"export-current-density": _field_export_definition("tool_export_current_density", "电流密度"),
"export-power-loss-density": _field_export_definition("tool_export_power_loss_density", "功率损耗密度"),

"export-voltage-result": {
    "category": "results",
    "risk": "filesystem-write",
    "description": (
        "Use this to export an existing voltage result by its exact full 0D or 1D ResultTree "
        "path. It does not invent a fixed monitor number or discover result paths, and it writes "
        "the requested output file."
    ),
    "handler": "tool_export_voltage_result",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string", "minLength": 1},
            "result_path": {"type": "string", "minLength": 1},
            "file_path": {"type": "string", "minLength": 1}
        },
        "required": ["project_path", "result_path", "file_path"],
        "additionalProperties": False
    },
},

"list-entities": {
    "category": "modeling",
    "risk": "read",
    "description": (
        "Use this to obtain exact component or solid names when a later boolean, transform, "
        "rename, material, or delete call needs them. It is not a routine post-check after a "
        "successful CST write."
    ),
    "handler": "tool_list_entities",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "component": {
                "type": "string",
                "examples": [
                    ""
                ]
            }
        },
        "required": [
            "project_path",
            "component"
        ]
    },
},

"list-materials": {
    "category": "modeling",
    "risk": "read",
    "description": (
        "Use this to discover exact material names available in the Runtime Materials library "
        "before importing or assigning one. It does not inspect materials already assigned to "
        "project geometry."
    ),
    "handler": "tool_list_materials",
    "json_schema": {
        "type": "object",
        "properties": {},
        "required": []
    },
},

"pick-face": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to pick a known face ID on a zero-thickness entity as one ordered input to "
        "define-loft. Pick the two intended surfaces in order; this tool does not create a loft "
        "by itself."
    ),
    "handler": "tool_pick_face",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "component": {
                "type": "string",
                "examples": [
                    "Component1"
                ]
            },
            "name": {
                "type": "string",
                "examples": [
                    "profile_wall"
                ]
            },
            "face_id": {
                "type": "string",
                "examples": [
                    "1"
                ]
            }
        },
        "required": [
            "project_path",
            "component",
            "name",
            "face_id"
        ]
    },
},

"rename-entity": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to rename one existing geometry entity when both the current full name and new "
        "name are explicit. Use list-entities only when the current name is unknown."
    ),
    "handler": "tool_rename_entity",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "old_name": {
                "type": "string",
                "examples": [
                    "Component1:old_name"
                ]
            },
            "new_name": {
                "type": "string",
                "examples": [
                    "Component1:new_name"
                ]
            }
        },
        "required": [
            "project_path",
            "old_name",
            "new_name"
        ]
    },
},

"set-background-with-space": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to set extra distances from the global X/Y/Z model bounds to the calculation "
        "volume. It does not choose face boundary types or background material; use "
        "define-boundary and define-background for those settings."
    ),
    "handler": "tool_set_background_with_space",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": ["C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"]
            },
            "x_min_space": {"type": "number", "default": 30,  "description": "X- direction space distance."},
            "x_max_space": {"type": "number", "default": 30,  "description": "X+ direction space distance."},
            "y_min_space": {"type": "number", "default": 30,  "description": "Y- direction space distance."},
            "y_max_space": {"type": "number", "default": 30,  "description": "Y+ direction space distance."},
            "z_min_space": {"type": "number", "default": 50,  "description": "Z- direction space distance."},
            "z_max_space": {"type": "number", "default": 100, "description": "Z+ direction space distance."}
        },
        "required": ["project_path"]
    },
},

"set-efield-monitor": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this before solving to define a single-frequency E-field monitor; CST 2022 requires "
        "start_freq to equal end_freq. It has no geometry, component, or material prerequisite; "
        "use set-field-monitor for the generic E/H interface."
    ),
    "handler": "tool_set_efield_monitor",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "start_freq": {
                "type": "number",
                "description": "Monitor frequency; CST 2022 requires it to equal end_freq.",
                "examples": [
                    8.0
                ]
            },
            "end_freq": {
                "type": "number",
                "description": "Range end for newer CST versions; CST 2022 requires it to equal start_freq.",
                "examples": [
                    8.0
                ]
            },
            "step": {
                "type": "number",
                "examples": [
                    1
                ]
            }
        },
        "required": [
            "project_path",
            "start_freq",
            "end_freq",
            "step"
        ]
    },
},

"set-entity-color": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to change the display RGB color of one known geometry entity. It is a visual "
        "setting only and does not change the entity's material or topology."
    ),
    "handler": "tool_set_entity_color",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "shape_name": {
                "type": "string",
                "examples": [
                    "Component1:my_brick"
                ]
            },
            "r": {
                "type": "integer",
                "examples": [
                    255
                ]
            },
            "g": {
                "type": "integer",
                "examples": [
                    0
                ]
            },
            "b": {
                "type": "integer",
                "examples": [
                    0
                ]
            }
        },
        "required": [
            "project_path",
            "shape_name",
            "r",
            "g",
            "b"
        ]
    },
},

"define-farfield-monitor": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this before solving to create one single-frequency farfield monitor per requested "
        "frequency, with optional near-field data and subvolume. It has no geometry, component, "
        "or material prerequisite; farfield results require a compatible Normal/Vacuum background."
    ),
    "handler": "tool_define_farfield_monitor",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string", "minLength": 1},
            "name": {"type": "string", "minLength": 1},
            "frequencies": {
                "type": "array",
                "items": {"type": "number", "exclusiveMinimum": 0},
                "minItems": 1,
                "uniqueItems": True
            },
            "enable_nearfield": {"type": "boolean", "default": True},
            "subvolume": {
                "type": ["array", "null"],
                "items": {"type": "number"},
                "minItems": 6,
                "maxItems": 6,
                "default": None
            }
        },
        "required": ["project_path", "name", "frequencies"],
        "additionalProperties": False
    },
},

"set-farfield-plot-cuts": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this before solving to replace the automatic FarfieldPlot theta/phi cuts that CST "
        "will evaluate for all farfield monitors after the solve. No result is required at call "
        "time, but at least one farfield monitor must exist before simulation."
    ),
    "handler": "tool_set_farfield_plot_cuts",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"set-field-monitor": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this before solving to define a single-frequency E-field or H-field monitor. It has "
        "no geometry, component, or material prerequisite and does not create a farfield monitor "
        "or point probe."
    ),
    "handler": "tool_set_field_monitor",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "field_type": {
                "type": "string",
                "enum": ["E", "H"],
                "examples": [
                    "H"
                ]
            },
            "start_frequency": {
                "type": "string",
                "description": "Monitor frequency; CST 2022 requires it to equal end_frequency.",
                "examples": [
                    "8"
                ]
            },
            "end_frequency": {
                "type": "string",
                "description": "Range end for newer CST versions; CST 2022 requires it to equal start_frequency.",
                "examples": [
                    "8"
                ]
            },
            "num_samples": {
                "type": "string",
                "description": "Sample count for newer CST versions; CST 2022 E/H monitors require 1.",
                "examples": [
                    "1"
                ]
            }
        },
        "required": [
            "project_path",
            "field_type",
            "start_frequency",
            "end_frequency",
            "num_samples"
        ]
    },
},

"set-probe": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this before solving to create an internal E-field or H-field point probe at an "
        "explicit global X/Y/Z position. It has no geometry, component, or material prerequisite "
        "and is not a volume or surface field monitor."
    ),
    "handler": "tool_set_probe",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "field_type": {
                "type": "string",
                "enum": ["E", "H"],
                "examples": [
                    "E"
                ]
            },
            "x_pos": {
                "type": "string",
                "description": "Global X position.",
                "examples": [
                    "0"
                ]
            },
            "y_pos": {
                "type": "string",
                "description": "Global Y position.",
                "examples": [
                    "0"
                ]
            },
            "z_pos": {
                "type": "string",
                "description": "Global Z position.",
                "examples": [
                    "5"
                ]
            }
        },
        "required": [
            "project_path",
            "field_type",
            "x_pos",
            "y_pos",
            "z_pos"
        ]
    },
},

"show-bounding-box": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this only when the user needs the model bounding-box display enabled or disabled. "
        "It changes visualization state, not calculation-volume spacing or boundary conditions."
    ),
    "handler": "tool_show_bounding_box",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            }
        },
        "required": [
            "project_path"
        ]
    },
},

"transform-curve": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to mirror an existing Curves item about a plane defined by Center and "
        "PlaneNormal in active X/Y/Z or WCS U/V/W coordinates. The result remains a curve; use "
        "transform-shape for solids."
    ),
    "handler": "tool_transform_curve",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "curve_name": {
                "type": "string",
                "examples": [
                    "curve1:my_curve"
                ]
            },
            "center_x": {
                "type": "string",
                "description": "Mirror center X or U component.",
                "examples": [
                    "0"
                ]
            },
            "center_y": {
                "type": "string",
                "description": "Mirror center Y or V component.",
                "examples": [
                    "0"
                ]
            },
            "center_z": {
                "type": "string",
                "description": "Mirror center Z or W component.",
                "examples": [
                    "0"
                ]
            },
            "plane_normal_x": {
                "type": "string",
                "description": "Mirror-plane normal X or U component.",
                "examples": [
                    "0"
                ]
            },
            "plane_normal_y": {
                "type": "string",
                "description": "Mirror-plane normal Y or V component.",
                "examples": [
                    "1"
                ]
            },
            "plane_normal_z": {
                "type": "string",
                "description": "Mirror-plane normal Z or W component.",
                "examples": [
                    "0"
                ]
            }
        },
        "required": [
            "project_path",
            "curve_name",
            "center_x",
            "center_y",
            "center_z",
            "plane_normal_x",
            "plane_normal_y",
            "plane_normal_z"
        ]
    },
},

"transform-shape": {
    "category": "modeling",
    "risk": "write",
    "description": (
        "Use this to mirror or rotate an existing solid in active X/Y/Z or WCS U/V/W coordinates. "
        "Mirror uses PlaneNormal, while rotate uses angle_x/y/z; the required plane_normal fields "
        "do not define the rotation axis. Use transform-curve for Curves items."
    ),
    "handler": "tool_transform_shape",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "shape_name": {
                "type": "string",
                "examples": [
                    "Component1:my_shape"
                ]
            },
            "transform_type": {
                "type": "string",
                "description": "Use 'mirror' for plane reflection or 'rotate' for angle-based rotation.",
                "examples": [
                    "mirror"
                ]
            },
            "center_x": {
                "type": "string",
                "description": "Free center X or U component.",
                "examples": [
                    "0"
                ]
            },
            "center_y": {
                "type": "string",
                "description": "Free center Y or V component.",
                "examples": [
                    "0"
                ]
            },
            "center_z": {
                "type": "string",
                "description": "Free center Z or W component.",
                "examples": [
                    "0"
                ]
            },
            "plane_normal_x": {
                "type": "string",
                "description": "Mirror normal X or U component; unused for rotate.",
                "examples": [
                    "0"
                ]
            },
            "plane_normal_y": {
                "type": "string",
                "description": "Mirror normal Y or V component; unused for rotate.",
                "examples": [
                    "1"
                ]
            },
            "plane_normal_z": {
                "type": "string",
                "default": "0",
                "description": "Mirror normal Z or W component; unused for rotate.",
                "examples": ["0"]
            },
            "angle_x": {
                "type": "string",
                "default": "0",
                "description": "Rotation angle in degrees around x, or u when a WCS is active; use for rotate only."
            },
            "angle_y": {
                "type": "string",
                "default": "0",
                "description": "Rotation angle in degrees around y, or v when a WCS is active; use for rotate only."
            },
            "angle_z": {
                "type": "string",
                "default": "0",
                "description": "Rotation angle in degrees around z, or w when a WCS is active; use for rotate only."
            },
            "multiple_objects": {
                "type": "boolean",
                "default": True,
                "description": "Apply to multiple objects."
            },
            "group_objects": {
                "type": "boolean",
                "default": False,
                "description": "Group resulting objects."
            },
            "repetitions": {
                "type": "integer",
                "default": 1,
                "description": "Number of repetitions."
            },
            "destination": {
                "type": "string",
                "default": "",
                "description": "Destination component for result."
            }
        },
        "required": [
            "project_path",
            "shape_name",
            "transform_type",
            "center_x", "center_y", "center_z",
            "plane_normal_x", "plane_normal_y", "plane_normal_z"
        ]
    },
},
}


# --- Handlers ---

from ..lib import modeling as _md
from ._arguments import project_path_from_args


def tool_define_material_from_mtd(args: dict) -> dict:
    return _md.define_material_from_mtd(
        project_path=project_path_from_args(args),
        material_name=str(args.get("material_name", "")),
    )


def tool_define_brick(args: dict) -> dict: return _md.define_brick(**args)
def tool_define_cylinder(args: dict) -> dict: return _md.define_cylinder(**args)
def tool_define_cone(args: dict) -> dict: return _md.define_cone(**args)
def tool_define_rectangle(args: dict) -> dict: return _md.define_rectangle(**args)
def tool_boolean_subtract(args: dict) -> dict: return _md.boolean_subtract(**args)
def tool_boolean_add(args: dict) -> dict: return _md.boolean_add(**args)
def tool_boolean_intersect(args: dict) -> dict: return _md.boolean_intersect(**args)
def tool_boolean_insert(args: dict) -> dict: return _md.boolean_insert(**args)
def tool_delete_entity(args: dict) -> dict: return _md.delete_entity(**args)
def tool_create_component(args: dict) -> dict: return _md.create_component(**args)
def tool_change_material(args: dict) -> dict: return _md.change_material(**args)
def tool_rename_entity(args: dict) -> dict: return _md.rename_entity(**args)
def tool_set_entity_color(args: dict) -> dict: return _md.set_entity_color(**args)
def tool_define_units(args: dict) -> dict: return _md.define_units(**args)
def tool_define_farfield_monitor(args: dict) -> dict: return _md.define_farfield_monitor(**args)
def tool_set_efield_monitor(args: dict) -> dict: return _md.set_efield_monitor(**args)
def tool_set_field_monitor(args: dict) -> dict: return _md.set_field_monitor(**args)
def tool_set_probe(args: dict) -> dict: return _md.set_probe(**args)
def tool_delete_probe(args: dict) -> dict: return _md.delete_probe_by_id(**args)
def tool_delete_monitor(args: dict) -> dict: return _md.delete_monitor(**args)
def tool_set_background_with_space(args: dict) -> dict: return _md.set_background_with_space(**args)
def tool_set_farfield_plot_cuts(args: dict) -> dict: return _md.set_farfield_plot_cuts(**args)
def tool_show_bounding_box(args: dict) -> dict: return _md.show_bounding_box(**args)
def tool_create_mesh_group(args: dict) -> dict: return _md.create_mesh_group(**args)
def tool_define_polygon_3d(args: dict) -> dict: return _md.define_polygon_3d(**args)
def tool_define_analytical_curve(args: dict) -> dict: return _md.define_analytical_curve(**args)
def tool_define_extrude_curve(args: dict) -> dict: return _md.define_extrude_curve(**args)
def tool_transform_shape(args: dict) -> dict: return _md.transform_shape(**args)
def tool_transform_curve(args: dict) -> dict: return _md.transform_curve(**args)
def tool_create_loft_sweep(args: dict) -> dict: return _md.create_loft_sweep(**args)
def tool_create_hollow_sweep(args: dict) -> dict: return _md.create_hollow_sweep(**args)
def tool_pick_face(args: dict) -> dict: return _md.pick_face(**args)
def tool_define_loft(args: dict) -> dict: return _md.define_loft(**args)
def tool_list_field_results(args: dict) -> dict:
    return _md.list_field_results(str(args.get("project_path", "")))


def _export_field(args: dict, field_kind: str) -> dict:
    return _md.export_field_result(field_kind=field_kind, **args)


def tool_export_e_field(args: dict) -> dict: return _export_field(args, "e_field")
def tool_export_h_field(args: dict) -> dict: return _export_field(args, "h_field")
def tool_export_surface_current(args: dict) -> dict: return _export_field(args, "surface_current")
def tool_export_power_flow(args: dict) -> dict: return _export_field(args, "power_flow")
def tool_export_current_density(args: dict) -> dict: return _export_field(args, "current_density")
def tool_export_power_loss_density(args: dict) -> dict: return _export_field(args, "power_loss_density")
def tool_export_voltage_result(args: dict) -> dict: return _md.export_voltage_result(**args)


_register_tool_defs(TOOL_DEFS)
