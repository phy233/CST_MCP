from __future__ import annotations

import pytest

from cst_runtime.core.compatibility.base import CompatibilityProfile
from cst_runtime.core.compatibility.modeling import (
    analytical_curve_vba,
    background_vba,
    cone_vba,
    cylinder_vba,
    extrude_curve_vba,
    mesh_vba,
    mesh_fpbavoid_nonreg_unite_vba,
    monitor_vba,
    polygon3d_vba,
    postprocess_activation_vba,
    port_vba,
    solver_acceleration_vba,
    solver_vba,
    transform_vba,
    units_vba,
)
from cst_runtime.core.errors import UnsupportedFeatureError, ValidationError


CST2022 = CompatibilityProfile(major=2022, version="2022", source="test")
CST2026 = CompatibilityProfile(major=2026, version="2026", source="test")


def _text(generated) -> str:
    return "\n".join(generated.lines)


def _unit_arguments(**overrides):
    values = {
        "length": "mm",
        "frequency": "GHz",
        "voltage": "V",
        "resistance": "Ohm",
        "inductance": "nH",
        "temperature": "Celsius",
        "time": "ns",
        "current": "A",
        "conductance": "S",
        "capacitance": "pF",
    }
    values.update(overrides)
    return values


def test_2022_units_use_legacy_methods_and_report_not_applied() -> None:
    generated = units_vba(profile=CST2022, **_unit_arguments())
    text = _text(generated)

    assert '.Geometry "mm"' in text
    assert '.TemperatureUnit "Celsius"' in text
    assert "SetUnit" not in text
    assert generated.not_applied["voltage"] == "V"


def test_2022_units_reject_nondefault_electrical_unit() -> None:
    with pytest.raises(UnsupportedFeatureError) as caught:
        units_vba(profile=CST2022, **_unit_arguments(voltage="mV"))

    assert caught.value.context["unsupported_arguments"] == ["voltage"]


def test_2026_units_keep_set_unit_temperature_token() -> None:
    generated = units_vba(profile=CST2026, **_unit_arguments())

    assert '.SetUnit "Temperature", "degC"' in _text(generated)


@pytest.mark.parametrize(
    ("supplied", "expected"),
    [
        ("degC", "Celsius"),
        ("K", "Kelvin"),
        ("degF", "Fahrenheit"),
    ],
)
def test_units_normalize_legacy_temperature_aliases(
    supplied: str,
    expected: str,
) -> None:
    generated = units_vba(
        profile=CST2022,
        **_unit_arguments(temperature=supplied),
    )

    assert f'.TemperatureUnit "{expected}"' in _text(generated)


def test_units_reject_unknown_temperature_unit() -> None:
    with pytest.raises(ValidationError, match="temperature"):
        units_vba(profile=CST2022, **_unit_arguments(temperature="Rankine"))


def test_background_reset_is_versioned() -> None:
    assert ".Reset\n" in _text(background_vba(background_type="Normal", profile=CST2022))
    assert "ResetBackground" not in _text(background_vba(background_type="Normal", profile=CST2022))
    assert ".ResetBackground" in _text(background_vba(background_type="Normal", profile=CST2026))


def test_2022_mesh_snapshot_excludes_modern_markers() -> None:
    generated = mesh_vba(
        steps_per_wave_near=5,
        steps_per_wave_far=5,
        steps_per_box_near=5,
        steps_per_box_far=1,
        edge_refinement_ratio=2,
        edge_refinement_buffer_lines=3,
        ratio_limit_geometry=10,
        equilibrate_value=1.5,
        use_gpu=True,
        profile=CST2022,
    )
    text = _text(generated)

    assert ".LinesPerWavelength" in text
    assert ".MinimumLineNumber" in text
    for marker in ("MeshSettings", "PBAVersion", "TSTVersion", "SetCADProcessingMethod"):
        assert marker not in text


def test_2022_solver_omits_modern_options_and_rejects_enabled_request() -> None:
    values = {
        "stimulation_port": "All",
        "stimulation_mode": "All",
        "steady_state_limit": -40,
        "mesh_adaption": False,
        "auto_norm_impedance": True,
        "norming_impedance": 50,
        "calculate_modes_only": False,
        "s_para_symmetry": False,
        "store_td_results": False,
        "run_discretizer_only": False,
        "full_deembedding": False,
        "superimpose_plw": False,
        "use_sensitivity": False,
    }
    text = _text(solver_vba(profile=CST2022, **values))
    assert ".Method" not in text
    assert "RunDiscretizerOnly" not in text

    values["use_sensitivity"] = True
    with pytest.raises(UnsupportedFeatureError):
        solver_vba(profile=CST2022, **values)


def test_2022_acceleration_contains_only_legacy_controls() -> None:
    generated = solver_acceleration_vba(
        use_parallelization=True,
        max_threads=1024,
        max_cpu_devices=2,
        remote_calc=False,
        use_distributed=False,
        max_distributed_ports=64,
        distribute_matrix=True,
        mpi_parallel=False,
        auto_mpi=False,
        hardware_accel=True,
        max_gpus=4,
        profile=CST2022,
    )
    text = _text(generated)
    assert "MaximumNumberOfThreads" in text
    assert "AutomaticMPI" not in text
    assert "MaximumNumberOfGPUs" not in text


def test_2022_port_removes_new_properties() -> None:
    text = _text(
        port_vba(
            port_number="1",
            ranges=(0, 1, 0, 1, 0, 0),
            orientation="zmax",
            profile=CST2022,
        )
    )
    assert ".Xrange 0, 1" in text
    assert ".Folder" not in text
    assert ".WaveguideMonitor" not in text


def test_2022_monitor_converts_step_to_sample_count() -> None:
    text = _text(
        monitor_vba(
            field_type="Farfield",
            start=1,
            end=3,
            step=0.5,
            profile=CST2022,
        )
    )
    assert '.FrequencySamples "5"' in text
    assert "CreateUsingLinearStep" not in text


def test_2022_monitor_rejects_nondivisible_range() -> None:
    with pytest.raises(ValidationError):
        monitor_vba(field_type="Efield", start=1, end=2, step=0.3, profile=CST2022)


def test_cylinder_uses_version_specific_radius_properties() -> None:
    arguments = {
        "name": "tube",
        "component": "component1",
        "material": "PEC",
        "outer_radius": 2,
        "inner_radius": 1,
        "axis": "z",
        "range_min": 0,
        "range_max": 5,
        "center1": 0,
        "center2": 0,
        "segments": 0,
    }
    legacy = _text(cylinder_vba(profile=CST2022, **arguments))
    modern = _text(cylinder_vba(profile=CST2026, **arguments))

    assert '.Outerradius "2"' in legacy
    assert '.Innerradius "1"' in legacy
    assert ".Xradius" not in legacy
    assert '.Xradius "2"' in modern
    assert '.Yradius "2"' in modern
    assert ".Innerradius" not in modern
    assert 'Solid.Subtract "component1:tube"' in modern


def test_solid_axis_is_validated_in_compatibility_layer() -> None:
    with pytest.raises(ValidationError, match="axis"):
        cylinder_vba(
            name="bad",
            component="component1",
            material="PEC",
            outer_radius=1,
            inner_radius=0,
            axis="q",
            range_min=0,
            range_max=1,
            center1=0,
            center2=0,
            segments=0,
            profile=CST2022,
        )


def test_cone_uses_version_specific_radius_properties() -> None:
    arguments = {
        "name": "cone",
        "component": "component1",
        "material": "PEC",
        "bottom_radius": 2,
        "top_radius": 0,
        "axis": "z",
        "range_min": 0,
        "range_max": 4,
        "center1": 0,
        "center2": 0,
        "segments": 0,
    }
    legacy = _text(cone_vba(profile=CST2022, **arguments))
    modern = _text(cone_vba(profile=CST2026, **arguments))

    assert '.Bottomradius "2"' in legacy
    assert '.Topradius "0"' in legacy
    assert ".XradiusTop" not in legacy
    assert '.Xradius "2"' in modern
    assert '.YradiusTop "0"' in modern
    assert ".Bottomradius" not in modern


def test_analytical_curve_uses_version_specific_properties() -> None:
    arguments = {
        "name": "curve1",
        "curve": "curves",
        "law_x": "cos(t)",
        "law_y": "sin(t)",
        "law_z": "0",
        "param_start": "0",
        "param_end": "2*pi",
    }
    legacy = _text(analytical_curve_vba(profile=CST2022, **arguments))
    modern = _text(analytical_curve_vba(profile=CST2026, **arguments))

    assert '.LawX "cos(t)"' in legacy
    assert '.ParameterRange "0", "2*pi"' in legacy
    assert ".CurveExpression" not in legacy
    assert '.CurveExpression "cos(t)", "sin(t)"' in modern
    assert '.ParameterName "t"' in modern
    assert '.Minvalue "0"' in modern
    assert ".LawZ" not in modern


def test_2026_analytical_curve_rejects_nonplanar_law() -> None:
    with pytest.raises(UnsupportedFeatureError) as caught:
        analytical_curve_vba(
            name="helix",
            curve="curves",
            law_x="cos(t)",
            law_y="sin(t)",
            law_z="t",
            param_start="0",
            param_end="2*pi",
            profile=CST2026,
        )

    assert caught.value.context["unsupported_arguments"] == ["law_z"]


def test_postprocess_activation_rejects_2022_without_target() -> None:
    with pytest.raises(UnsupportedFeatureError) as caught:
        postprocess_activation_vba(
            operation="renormalize",
            enable=True,
            profile=CST2022,
        )

    assert caught.value.context["unsupported_arguments"] == ["operation", "enable"]
    assert "ApplyTo" in str(caught.value.next_action)


def test_2026_postprocess_activation_rejects_undocumented_command() -> None:
    with pytest.raises(UnsupportedFeatureError) as caught:
        postprocess_activation_vba(
            operation="renormalize",
            enable=True,
            profile=CST2026,
        )

    assert "未记录 ActivateOperation" in str(caught.value.next_action)


def test_mesh_fpbavoid_nonreg_unite_is_version_guarded() -> None:
    with pytest.raises(UnsupportedFeatureError):
        mesh_fpbavoid_nonreg_unite_vba(enable=True, profile=CST2022)

    assert _text(
        mesh_fpbavoid_nonreg_unite_vba(enable=True, profile=CST2026)
    ) == "Mesh.FPBAAvoidNonRegUnite True"


def test_polygon3d_uses_version_specific_point_signatures() -> None:
    points = [(0, 0, 0), (1, 2, 0), (2, 0, 0)]
    legacy = _text(polygon3d_vba("p", "c", points, profile=CST2022))
    modern = _text(polygon3d_vba("p", "c", points, profile=CST2026))

    assert '.Point "0", "0", "0"' in legacy
    assert '.Point "0:0:0", "1:2:0", "2:0:0"' in modern
    assert '.Closed "False"' in modern
    assert ".Version" not in modern


def test_2022_polygon_extrude_and_transform_snapshots() -> None:
    polygon = _text(polygon3d_vba("p", "c", [(0, 0, 0), (1, 0, 0)], profile=CST2022))
    extrude = _text(
        extrude_curve_vba(
            name="solid",
            component="component1",
            material="PEC",
            curve="profile",
            thickness=1,
            twist_angle=0,
            taper_angle=0,
            delete_profile=True,
            profile=CST2022,
        )
    )
    transform = _text(
        transform_vba(
            target_kind="Shape",
            name="component1:solid",
            transform_type="Rotate",
            center=("0", "0", "0"),
            plane_normal=("0", "0", "1"),
            profile=CST2022,
        )
    )

    assert ".Version" not in polygon
    assert ".DeleteProfile" not in extrude
    assert 'Curve.DeleteCurve "profile"' in extrude
    assert "AutoDestination" not in transform
    assert ".Destination" not in transform


def test_2022_transform_rejects_destination() -> None:
    with pytest.raises(UnsupportedFeatureError):
        transform_vba(
            target_kind="Shape",
            name="component1:solid",
            transform_type="Rotate",
            center=("0", "0", "0"),
            plane_normal=("0", "0", "1"),
            destination="component2",
            profile=CST2022,
        )
