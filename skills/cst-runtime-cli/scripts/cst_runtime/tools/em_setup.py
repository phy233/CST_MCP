"""超表面电磁设置与验收工具定义。"""
from __future__ import annotations

from . import _register_tool_defs
from ._arguments import project_path_from_args
from ..lib import em_setup as _em


_PROJECT = {
    "type": "string",
    "description": "CST 工程绝对路径。",
    "examples": [r"C:\path\to\working.cst"],
}
_MODE = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "type": {"type": "string", "enum": ["TE", "TM", "LCP", "RCP"]},
        "order_x": {"type": "integer"},
        "order_yprime": {"type": "integer"},
    },
    "required": ["type", "order_x", "order_yprime"],
}
_PORT = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "position": {"type": "string", "enum": ["Zmin", "Zmax"]},
        "mode_strategy": {"type": "string", "enum": ["explicit", "automatic"]},
        "modes": {"type": "array", "items": _MODE, "default": []},
        "modes_considered": {"type": "integer", "minimum": 1},
        "reference_distance": {"type": "number", "default": 0.0},
    },
    "required": ["position", "mode_strategy", "modes_considered", "reference_distance"],
}
_EXCITATION_ITEM = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "port": {"type": ["integer", "string"]},
        "mode": {"type": "string", "minLength": 1},
    },
    "required": ["port", "mode"],
}
_EXCITATION = {
    "type": "object",
    "additionalProperties": False,
    "description": "激励策略。single 使用整数 port/mode；list 使用 items。",
    "properties": {
        "strategy": {
            "type": "string",
            "enum": ["all", "all_with_floquet", "plane_wave", "single", "list"],
        },
        "port": {"type": "integer", "minimum": 1},
        "mode": {"type": "integer", "minimum": 1},
        "items": {"type": "array", "items": _EXCITATION_ITEM},
    },
    "required": ["strategy"],
}


TOOL_DEFS = {
    "define-unit-cell-boundary": {
        "category": "project_ops",
        "risk": "filesystem-write",
        "description": "按 CST 2022 手册配置六面边界和 Unit Cell 扫描角；先校验 X/Y 配对，执行后再通过 getter 读回。",
        "handler": "tool_define_unit_cell_boundary",
        "json_schema": {
            "type": "object",
            "properties": {
                "project_path": _PROJECT,
                "xmin": {"type": "string"},
                "xmax": {"type": "string"},
                "ymin": {"type": "string"},
                "ymax": {"type": "string"},
                "zmin": {"type": "string", "enum": ["open", "expanded open"]},
                "zmax": {"type": "string", "enum": ["open", "expanded open"]},
                "theta": {"type": "number", "default": 0.0},
                "phi": {"type": "number", "default": 0.0},
                "direction": {"type": "string", "enum": ["outward", "inward"], "default": "outward"},
            },
            "required": ["project_path", "xmin", "xmax", "ymin", "ymax", "zmin", "zmax"],
        },
    },
    "inspect-boundary": {
        "category": "project_ops",
        "risk": "read",
        "description": "使用 Boundary 六面 getter 和 GetUnitCellScanAngle 读取实际边界状态。",
        "handler": "tool_inspect_boundary",
        "json_schema": {"type": "object", "properties": {"project_path": _PROJECT}, "required": ["project_path"]},
    },
    "define-floquet-port": {
        "category": "project_ops",
        "risk": "filesystem-write",
        "description": "配置 Zmin/Zmax Floquet 端口、显式或自动模式、参考面、极化基础和排序。仅公开 getter 可读字段会被验收。",
        "handler": "tool_define_floquet_port",
        "json_schema": {
            "type": "object",
            "properties": {
                "project_path": _PROJECT,
                "ports": {"type": "array", "minItems": 1, "maxItems": 2, "items": _PORT},
                "polarization_basis": {"type": "string", "enum": ["linear", "circular"], "default": "linear"},
                "sort_code": {"type": "string", "default": "+beta/pw"},
                "sort_frequency": {"type": ["number", "null"], "default": None},
                "sort_theta": {"type": "number", "default": 0.0},
                "sort_phi": {"type": "number", "default": 0.0},
                "max_order_x": {"type": ["integer", "null"], "minimum": 0, "default": None},
                "max_order_yprime": {"type": ["integer", "null"], "minimum": 0, "default": None},
            },
            "required": ["project_path", "ports"],
        },
    },
    "inspect-floquet-ports": {
        "category": "project_ops",
        "risk": "read",
        "description": "读取 Floquet 端口位置、模式序号/名称、模式列表及考虑模式数；不伪造无 getter 字段。",
        "handler": "tool_inspect_floquet_ports",
        "json_schema": {"type": "object", "properties": {"project_path": _PROJECT}, "required": ["project_path"]},
    },
    "define-plane-wave": {
        "category": "project_ops",
        "risk": "filesystem-write",
        "description": "创建真实 PlaneWave 源。普通平面波不产生 S 参数；无限周期单元应使用 Unit Cell 与 Floquet。",
        "handler": "tool_define_plane_wave",
        "json_schema": {
            "type": "object",
            "properties": {
                "project_path": _PROJECT,
                "normal": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "number"}},
                "e_vector": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "number"}},
                "polarization": {"type": "string", "enum": ["Linear", "Circular", "Elliptical"], "default": "Linear"},
                "reference_frequency": {"type": ["number", "null"], "default": None},
                "handedness": {"type": ["string", "null"], "enum": ["Left", "Right", None], "default": None},
                "phase_difference": {"type": ["number", "null"], "default": None},
                "axial_ratio": {"type": ["number", "null"], "default": None},
            },
            "required": ["project_path", "normal", "e_vector"],
        },
    },
    "inspect-plane-wave": {
        "category": "project_ops",
        "risk": "read",
        "description": "使用 PlaneWave 公开 getter 读取传播向量、电场向量和极化参数。",
        "handler": "tool_inspect_plane_wave",
        "json_schema": {"type": "object", "properties": {"project_path": _PROJECT}, "required": ["project_path"]},
    },
    "configure-frequency-domain-solver": {
        "category": "project_ops",
        "risk": "filesystem-write",
        "description": "仅切换 HF Frequency Domain、设置 mesh_method 和激励；不会生成 FDSolver.Reset，也不改精度、扫频或自适应设置。",
        "handler": "tool_configure_frequency_domain_solver",
        "json_schema": {
            "type": "object",
            "properties": {
                "project_path": _PROJECT,
                "mesh_method": {"type": "string", "enum": ["Hexahedral", "Tetrahedral", "Surface"]},
                "excitation": _EXCITATION,
            },
            "required": ["project_path", "mesh_method", "excitation"],
        },
    },
    "list-monitors": {
        "category": "project_ops",
        "risk": "read",
        "description": "使用 Monitor 公开 getter 返回名称、类型、域和频率；与结果树扫描工具并存。",
        "handler": "tool_list_monitors",
        "json_schema": {"type": "object", "properties": {"project_path": _PROJECT}, "required": ["project_path"]},
    },
}


def tool_define_unit_cell_boundary(args: dict) -> dict:
    return _em.define_unit_cell_boundary(
        project_path_from_args(args),
        xmin=args["xmin"], xmax=args["xmax"], ymin=args["ymin"], ymax=args["ymax"],
        zmin=args["zmin"], zmax=args["zmax"], theta=args.get("theta", 0.0),
        phi=args.get("phi", 0.0), direction=args.get("direction", "outward"),
    )


def tool_inspect_boundary(args: dict) -> dict:
    return _em.inspect_boundary(project_path_from_args(args))


def tool_define_floquet_port(args: dict) -> dict:
    return _em.define_floquet_port(
        project_path_from_args(args),
        ports=args["ports"],
        polarization_basis=args.get("polarization_basis", "linear"),
        sort_code=args.get("sort_code", "+beta/pw"),
        sort_frequency=args.get("sort_frequency"),
        sort_theta=args.get("sort_theta", 0.0),
        sort_phi=args.get("sort_phi", 0.0),
        max_order_x=args.get("max_order_x"),
        max_order_yprime=args.get("max_order_yprime"),
    )


def tool_inspect_floquet_ports(args: dict) -> dict:
    return _em.inspect_floquet_ports(project_path_from_args(args))


def tool_define_plane_wave(args: dict) -> dict:
    return _em.define_plane_wave(
        project_path_from_args(args),
        normal=args["normal"], e_vector=args["e_vector"],
        polarization=args.get("polarization", "Linear"),
        reference_frequency=args.get("reference_frequency"),
        handedness=args.get("handedness"),
        phase_difference=args.get("phase_difference"),
        axial_ratio=args.get("axial_ratio"),
    )


def tool_inspect_plane_wave(args: dict) -> dict:
    return _em.inspect_plane_wave(project_path_from_args(args))


def tool_configure_frequency_domain_solver(args: dict) -> dict:
    return _em.configure_frequency_domain_solver(
        project_path_from_args(args),
        mesh_method=args["mesh_method"],
        excitation=args["excitation"],
    )


def tool_list_monitors(args: dict) -> dict:
    return _em.list_monitors(project_path_from_args(args))


_register_tool_defs(TOOL_DEFS)
