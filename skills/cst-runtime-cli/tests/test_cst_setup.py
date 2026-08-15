"""工程级设置的真实 CST 2022 集成测试。

本文件按字母序最后运行。全部 define-* 状态类设置没有公开删除工具，
依赖会话末段的 save=False 回滚；本文件内定义顺序即执行顺序。
Z0（define-parameters）定义在最后，避免任何后续求解器交互。
"""
from __future__ import annotations

from typing import Any

import pytest

from cst_helpers import (
    assert_error_response,
    project_arguments,
)


pytestmark = [
    pytest.mark.cst_integration,
    pytest.mark.cst_destructive,
]


def test_define_units_mm_ghz_with_not_applied(cst_case: Any) -> None:
    result = cst_case.require_success(
        "define-units",
        project_arguments(
            cst_case,
            length="mm",
            frequency="GHz",
            temperature="Celsius",
        ),
    )
    not_applied = result.get("compatibility", {}).get("not_applied", {})
    for electrical in ("voltage", "resistance", "inductance", "current", "conductance", "capacitance"):
        assert electrical in not_applied, result


def test_define_background_normal_get_roundtrip(cst_case: Any) -> None:
    defined = cst_case.require_success(
        "define-background",
        project_arguments(cst_case, background_type="Normal", epsilon=1.0, mu=1.0),
    )
    assert defined.get("farfield_compatible") is True, defined
    readback = cst_case.require_success("get-background", project_arguments(cst_case))
    assert readback["background_type"] == "Normal", readback
    assert readback["source"] == "runtime_tracked", readback


def test_set_background_with_space_success(cst_case: Any) -> None:
    cst_case.require_success(
        "set-background-with-space",
        project_arguments(cst_case),
    )
    readback = cst_case.require_success("get-background", project_arguments(cst_case))
    assert readback["background_type"] == "Normal", readback


def test_define_frequency_range_success(cst_case: Any) -> None:
    cst_case.require_success(
        "define-frequency-range",
        project_arguments(cst_case, start_freq=8.0, end_freq=12.0),
    )


def test_define_boundary_open_readback(cst_case: Any) -> None:
    cst_case.require_success(
        "define-boundary",
        project_arguments(cst_case, face_type="expanded open", symmetry_type="none"),
    )
    readback = cst_case.require_success("inspect-boundary", project_arguments(cst_case))
    faces = readback["faces"]
    assert set(faces) == {"xmin", "xmax", "ymin", "ymax", "zmin", "zmax"}, readback
    for value in faces.values():
        assert value.casefold() == "expanded open", readback


def test_define_unit_cell_boundary_readback(cst_case: Any) -> None:
    cst_case.require_success(
        "define-unit-cell-boundary",
        project_arguments(
            cst_case,
            xmin="unit cell",
            xmax="unit cell",
            ymin="unit cell",
            ymax="unit cell",
            zmin="open",
            zmax="expanded open",
            theta=12.0,
            phi=23.0,
            direction="outward",
        ),
    )
    readback = cst_case.require_success("inspect-boundary", project_arguments(cst_case))
    faces = readback["faces"]
    for key in ("xmin", "xmax", "ymin", "ymax"):
        assert faces[key].casefold() == "unit cell", readback
    scan = readback["unit_cell_scan"]
    assert scan["available"] is True, readback
    assert scan["theta"] == pytest.approx(12.0), readback
    assert scan["phi"] == pytest.approx(23.0), readback


def test_define_plane_wave_readback(cst_case: Any) -> None:
    cst_case.require_success(
        "define-plane-wave",
        project_arguments(
            cst_case,
            normal=[0, 0, -1],
            e_vector=[1, 0, 0],
            polarization="Linear",
        ),
    )
    readback = cst_case.require_success("inspect-plane-wave", project_arguments(cst_case))
    wave = readback["plane_wave"]
    assert wave["normal"] == pytest.approx([0.0, 0.0, -1.0]), readback
    assert wave["e_vector"] == pytest.approx([1.0, 0.0, 0.0]), readback
    assert wave["polarization"] == "Linear", readback


def test_define_mesh_success(cst_case: Any) -> None:
    cst_case.require_success(
        "define-mesh",
        project_arguments(
            cst_case,
            steps_per_wave_near=5,
            steps_per_wave_far=5,
            steps_per_box_near=5,
            steps_per_box_far=1,
        ),
    )


def test_define_solver_and_change_type(cst_case: Any) -> None:
    cst_case.require_success(
        "define-solver",
        project_arguments(
            cst_case,
            stimulation_port="All",
            steady_state_limit=-40,
            norming_impedance=50,
        ),
    )
    cst_case.require_success(
        "change-solver-type",
        project_arguments(cst_case, solver_type="HF Time Domain"),
    )


def test_configure_frequency_domain_solver(cst_case: Any) -> None:
    result = cst_case.require_success(
        "configure-frequency-domain-solver",
        project_arguments(
            cst_case,
            mesh_method="Hexahedral",
            excitation={"strategy": "all"},
        ),
    )
    assert result.get("solver_type") == "HF Frequency Domain", result


def test_set_solver_acceleration_and_mesh_step(cst_case: Any) -> None:
    cst_case.require_success(
        "set-solver-acceleration",
        project_arguments(cst_case, use_parallelization=False, max_threads=4),
    )
    cst_case.require_success(
        "set-mesh-minimum-step-number",
        project_arguments(cst_case, num_steps=5),
    )


def test_set_mesh_fpbavoid_nonreg_unite_unsupported(cst_case: Any) -> None:
    result = cst_case.call(
        "set-mesh-fpbavoid-nonreg-unite",
        project_arguments(cst_case),
    )
    assert_error_response(
        result,
        error_types={"unsupported_feature"},
        phase="compatibility",
    )
    assert result.get("feature") == "mesh.fpbavoid_nonreg_unite", result
    assert result.get("context", {}).get("required_capability") == "mesh.fpbavoid_nonreg_unite", result


def test_farfield_monitor_create_list_delete(cst_case: Any) -> None:
    name = cst_case.name("ff")
    result = cst_case.require_success(
        "define-farfield-monitor",
        project_arguments(cst_case, name=name, frequencies=[10.0]),
    )
    assert result.get("created_count") == 1, result
    monitor_name = f"farfield (f=10)"

    def listed_names() -> list[str]:
        listed = cst_case.require_success("list-monitors", project_arguments(cst_case))
        return [item["name"] for item in listed.get("monitors", [])]

    assert monitor_name in listed_names()
    cst_case.require_success(
        "delete-monitor",
        project_arguments(cst_case, monitor_name=monitor_name),
    )
    assert monitor_name not in listed_names()


def test_efield_and_hfield_monitor_lifecycle(cst_case: Any) -> None:
    cst_case.require_success(
        "set-efield-monitor",
        project_arguments(cst_case, start_freq=8, end_freq=8, step=1),
    )
    cst_case.require_success(
        "set-field-monitor",
        project_arguments(
            cst_case,
            field_type="H",
            start_frequency="8",
            end_frequency="8",
            num_samples="1",
        ),
    )

    def listed_names() -> list[str]:
        listed = cst_case.require_success("list-monitors", project_arguments(cst_case))
        return [item["name"] for item in listed.get("monitors", [])]

    for monitor_name in ("e-field (f=8)", "h-field (f=8)"):
        assert monitor_name in listed_names(), monitor_name
    for monitor_name in ("e-field (f=8)", "h-field (f=8)"):
        cst_case.require_success(
            "delete-monitor",
            project_arguments(cst_case, monitor_name=monitor_name),
        )
        assert monitor_name not in listed_names()


def test_create_component_leftover_rolled_back(cst_case: Any) -> None:
    """无公开 delete-component 工具：验证提交成功，残留靠会话回滚。"""
    result = cst_case.require_success(
        "create-component",
        project_arguments(cst_case, component_name=cst_case.name("extra_comp")),
    )
    assert result["status"] == "success", result


def test_create_mesh_group_leftover_rolled_back(cst_case: Any) -> None:
    name = cst_case.name("group_item")
    cst_case.require_success(
        "define-brick",
        project_arguments(
            cst_case,
            name=name,
            component="component1",
            material="PEC",
            x_min=180,
            x_max=181,
            y_min=180,
            y_max=181,
            z_min=180,
            z_max=181,
        ),
    )
    cst_case.shared.register_entity("component1", name)
    try:
        result = cst_case.require_success(
            "create-mesh-group",
            project_arguments(
                cst_case,
                group_name=cst_case.name("mesh_group"),
                items=[name],
            ),
        )
        assert result["status"] == "success", result
    finally:
        cst_case.shared.delete_entity("component1", name)


def test_define_floquet_port_readback(cst_case: Any) -> None:
    """依赖前置的 unit-cell 边界 + 频域求解器配置。"""
    result = cst_case.require_success(
        "define-floquet-port",
        project_arguments(
            cst_case,
            ports=[
                {
                    "position": "Zmin",
                    "mode_strategy": "automatic",
                    "modes": [],
                    "modes_considered": 2,
                    "reference_distance": 0,
                },
                {
                    "position": "Zmax",
                    "mode_strategy": "automatic",
                    "modes": [],
                    "modes_considered": 2,
                    "reference_distance": 0,
                },
            ],
            polarization_basis="linear",
            sort_code="+beta/pw",
        ),
    )
    assert result["status"] == "success", result
    readback = cst_case.require_success("inspect-floquet-ports", project_arguments(cst_case))
    ports = list(readback.get("ports", []))
    assert {port["position"] for port in ports} == {"Zmin", "Zmax"}, readback
    assert "reference_distance" in readback.get("unavailable_fields", []), readback


def test_define_parameters_batch_then_visible(cst_case: Any) -> None:
    """批量参数写入与回读；无 delete-parameter，参数残留靠会话回滚。"""
    result = cst_case.require_success(
        "define-parameters",
        project_arguments(cst_case, names=["pytest_p1", "pytest_p2"], values=["10", "2*pytest_p1"]),
    )
    assert result.get("count") == 2, result
    listed = cst_case.require_success("list-parameters", project_arguments(cst_case))
    parameters = listed.get("parameters", {})
    assert float(parameters["pytest_p1"]) == pytest.approx(10.0), listed
    assert parameters["pytest_p2"] == "2*pytest_p1", listed
