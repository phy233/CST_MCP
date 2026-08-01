"""跨包和 runtime 分层约束测试。"""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skills" / "cst-runtime-cli" / "scripts" / "cst_runtime"


def _imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level
            found.append((node.lineno, prefix + (node.module or "")))
    return found


def test_workflows_never_import_core() -> None:
    violations = [
        f"{path.name}:{line}"
        for path in (RUNTIME / "workflows").glob("*.py")
        for line, module in _imports(path)
        if module.startswith("..core") or module.startswith("cst_runtime.core")
    ]
    assert not violations


def test_tools_and_cli_pipelines_never_import_core() -> None:
    targets = [RUNTIME / "tools", RUNTIME / "cli" / "pipelines"]
    violations = [
        f"{path.relative_to(RUNTIME)}:{line}:{module}"
        for target in targets
        for path in target.rglob("*.py")
        for line, module in _imports(path)
        if module.startswith("..core")
        or module.startswith("...core")
        or module.startswith("cst_runtime.core")
    ]
    assert not violations


def test_lib_never_accesses_cst_objects_directly() -> None:
    forbidden_attributes = {"modeler", "model3d", "ResultTree"}
    violations: list[str] = []
    for path in (RUNTIME / "lib").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in forbidden_attributes:
                violations.append(
                    f"{path.relative_to(RUNTIME)}:{node.lineno}:{node.attr}"
                )
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                else:
                    modules = [node.module or ""]
                if any(module == "cst" or module.startswith("cst.") for module in modules):
                    violations.append(
                        f"{path.relative_to(RUNTIME)}:{node.lineno}:CST import"
                    )
    assert not violations


def test_registered_atomic_operations_use_lib_boundary() -> None:
    from cst_runtime.api.inventory import operation_inventory

    inventory = operation_inventory()
    assert inventory
    assert all(item["uses_lib_boundary"] for item in inventory)
    assert not [item for item in inventory if item["imports_core"]]


def test_lower_layers_never_import_upper_layers() -> None:
    violations: list[str] = []
    for layer, forbidden in {
        "core": ("cst_runtime.lib", "cst_runtime.workflows", "..lib", "..workflows"),
        "lib": ("cst_runtime.workflows", "..workflows", "cst_runtime.api", "..api"),
    }.items():
        for path in (RUNTIME / layer).rglob("*.py"):
            for line, module in _imports(path):
                if module.startswith(forbidden):
                    violations.append(f"{path.relative_to(RUNTIME)}:{line}:{module}")
    assert not violations


def test_removed_lib_workflow_modules_do_not_exist() -> None:
    for name in ("array.py", "sweep.py", "cross_process.py", "unit_cells.py"):
        assert not (RUNTIME / "lib" / name).exists()


def test_runtime_api_does_not_depend_on_mcp() -> None:
    violations = [
        f"{path.name}:{line}"
        for path in (RUNTIME / "api").glob("*.py")
        for line, module in _imports(path)
        if module == "mcp" or module.startswith("mcp.")
    ]
    assert not violations


def test_mcp_only_uses_runtime_registry_through_worker() -> None:
    forbidden = ("cst_runtime.core", "cst_runtime.lib", "cst_runtime.tools")
    violations = [
        f"{path.name}:{line}:{module}"
        for path in (ROOT / "mcp_server").glob("*.py")
        for line, module in _imports(path)
        if module.startswith(forbidden)
    ]
    assert not violations


def test_runtime_api_never_imports_cli_or_core() -> None:
    violations = [
        f"{path.name}:{line}:{module}"
        for path in (RUNTIME / "api").glob("*.py")
        for line, module in _imports(path)
        if module.startswith("..cli")
        or module.startswith("cst_runtime.cli")
        or module.startswith("..core")
        or module.startswith("cst_runtime.core")
    ]
    assert not violations


def test_model3d_is_only_accessed_inside_compatibility() -> None:
    """版本专用的 model3d 属性只能出现在统一兼容边界中。"""
    violations: list[str] = []
    for path in RUNTIME.rglob("*.py"):
        if (RUNTIME / "core" / "compatibility") in path.parents:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "model3d":
                violations.append(f"{path.relative_to(RUNTIME)}:{node.lineno}")
    assert not violations


def test_design_environment_version_methods_are_only_in_compatibility() -> None:
    """连接方式差异不得重新散落到 core、lib、tools 或 workflows。"""
    violations: list[str] = []
    for path in RUNTIME.rglob("*.py"):
        if (RUNTIME / "core" / "compatibility") in path.parents:
            continue
        for line, module in _imports(path):
            if module == "cst.interface" or module.endswith(".cst.interface"):
                violations.append(f"{path.relative_to(RUNTIME)}:{line}:{module}")
    assert not violations


def test_lib_contains_no_known_version_specific_vba_markers() -> None:
    """lib 只能传递语义参数，不得重新拼接已知的版本专用 VBA。"""
    forbidden = {
        "PeriodicUsePrimitive",
        "SetPeriodicShiftAngle",
        "AutoDestination",
        "SetPortType",
        "CreateFloquetPort",
        "With Polygon3D",
        "CreateUsingLinearStep",
        "FarfieldCalculator",
    }
    violations: list[str] = []
    for path in (RUNTIME / "lib").rglob("*.py"):
        source = path.read_text(encoding="utf-8-sig")
        for marker in forbidden:
            if marker in source:
                violations.append(f"{path.relative_to(RUNTIME)}:{marker}")
    assert not violations
