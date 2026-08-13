"""modeling.py — modeling 工具定义"""
from . import _register_tool_defs


def _field_export_definition(handler: str, physical_name: str) -> dict:
    """构造按官方 Result Type 校验的场结果导出工具定义。"""
    return {
        "category": "results",
        "risk": "filesystem-write",
        "description": (
            f"导出实际 ResultTree 中的{physical_name}节点；完整 result_path 为唯一依据，"
            "支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。"
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
    "description": "Unite two solids (boolean union).",
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
    "description": "Insert one solid into another (boolean insert).",
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
    "description": "Intersect two solids (boolean intersection).",
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
        "Subtract one solid from another (boolean difference). CST may accept "
        "a subtraction between non-intersecting solids without changing the target, "
        "so confirm geometric overlap from the modeled coordinates before calling."
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
    "description": "Change the material of a geometry entity. Use list-materials to see available names.",
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
    "description": "Create a new component in the CST project.",
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
    "description": "Create a hollow loft between two rectangular profiles in active X/Y/Z or local U/V/W coordinates.",
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

"create-horn-segment": {
    "category": "modeling",
    "risk": "write",
    "description": "Create a Z-axis horn segment; Z means W when a local WCS is active.",
    "handler": "tool_create_horn_segment",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "examples": [
                    "C:\\path\\to\\tasks\\task_xxx\\runs\\run_001\\projects\\working.cst"
                ]
            },
            "segment_id": {
                "type": "integer",
                "examples": [
                    1
                ]
            },
            "bottom_radius": {
                "type": "number",
                "examples": [
                    8
                ]
            },
            "top_radius": {
                "type": "number",
                "examples": [
                    25
                ]
            },
            "z_min": {
                "type": "number",
                "description": "Lower Z or W axis bound.",
                "examples": [
                    0
                ]
            },
            "z_max": {
                "type": "number",
                "description": "Upper Z or W axis bound.",
                "examples": [
                    30
                ]
            }
        },
        "required": [
            "project_path",
            "segment_id",
            "bottom_radius",
            "top_radius",
            "z_min",
            "z_max"
        ]
    },
},

"create-loft-sweep": {
    "category": "modeling",
    "risk": "write",
    "description": "Create a loft between two rectangular profiles in active X/Y/Z or local U/V/W coordinates.",
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
    "description": "Create a mesh group and add items.",
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
    "description": "Create a parametric curve in active X/Y/Z or local U/V/W coordinates; each law must be differentiable over the parameter range.",
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
    "description": "Create a brick in active X/Y/Z or local U/V/W coordinates.",
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
        "Create a cone along an active X/U, Y/V, or Z/W axis. axis_min/axis_max set the axial range; "
        "the two transverse centers are mapped to axis-specific VBA setters. "
        "bottom_radius is at the lower bound and top_radius at the upper bound."
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
        "Create a cylinder along an active X/U, Y/V, or Z/W axis. axis_min/axis_max set the axial "
        "range; the two transverse centers are mapped to axis-specific VBA setters."
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
        "Extrude a closed planar curve. Positive thickness follows its ordered normal "
        "(CST 2022 real-machine verified); negative reverses it. Compute the normal and sign first."
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
    "description": "Connect two pre-picked surfaces; CST 2022 defines no separate plane-normal argument.",
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
    "description": "Define a CST material from .mtd file by material name. Material must exist in references/Materials/. Use list-materials to see available names.",
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
        "Create ordered points in active X/Y/Z or local U/V/W coordinates. For extrusion, "
        "close the loop, verify coplanarity, and compute its ordered normal."
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
    "description": "Create a rectangle in the active XY or local UV plane; calculate bounds in that coordinate system first.",
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
    "description": "Set the CST project unit system.",
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
                "description": "CST 温度单位；省略时使用 Celsius。"
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
    "description": "Delete a geometry entity from the CST project.",
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
    "description": "Delete a monitor by name.",
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
    "description": "Delete a probe by its ID.",
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
    "description": "使用 CST 2022 ResultTree.GetTreeResults 枚举 2D/3D 节点、官方 Result Type 和关联文件。",
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
    "description": "按实际 0D/1D ResultTree 完整路径导出电压结果，不生成固定监视器编号。",
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
    "description": "List geometry entities from the verified CST working project.",
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
    "description": "List available CST material names from the Materials library.",
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
    "description": "Select a face by ID for loft operations (zero-thickness entities only).",
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
    "description": "Rename a geometry entity.",
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
    "description": "Add distances to the global X/Y/Z bounds of the calculation volume.",
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
    "description": "设置 E-field 监视器；CST 2022 只支持单频，start_freq 必须等于 end_freq。",
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
                "description": "监视频率；CST 2022 下必须等于 end_freq。",
                "examples": [
                    8.0
                ]
            },
            "end_freq": {
                "type": "number",
                "description": "新版本 CST 的范围终点；CST 2022 下必须等于 start_freq。",
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
    "description": "Set the display color of a geometry entity.",
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
        "按 CST 2022 Monitor Object 为每个频率创建独立单频远场监视器，并读回名称、类型、"
        "域和频率验证；子体积完全可选，不含模型专用默认坐标。"
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
    "description": "Set farfield plot cut angles.",
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
    "description": "设置 E/H 场监视器；CST 2022 只支持单频。",
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
                "description": "监视频率；CST 2022 下必须等于 end_frequency。",
                "examples": [
                    "8"
                ]
            },
            "end_frequency": {
                "type": "string",
                "description": "新版本 CST 的范围终点；CST 2022 下必须等于 start_frequency。",
                "examples": [
                    "8"
                ]
            },
            "num_samples": {
                "type": "string",
                "description": "新版本 CST 的样本数；CST 2022 的 E/H 监视器只允许 1。",
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
    "description": "Set an internal E/H-field probe at a global X/Y/Z position.",
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
    "description": "Toggle bounding box display.",
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
    "description": "Mirror a curve using Center and PlaneNormal in active X/Y/Z or local U/V/W coordinates; compute both first.",
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
        "Mirror uses PlaneNormal; rotate uses Angle. Center and components use active X/Y/Z "
        "or local U/V/W coordinates. Required plane_normal fields do not define a rotate axis."
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
def tool_create_horn_segment(args: dict) -> dict: return _md.create_horn_segment(**args)
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
