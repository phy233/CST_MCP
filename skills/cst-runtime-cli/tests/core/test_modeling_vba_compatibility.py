from __future__ import annotations

import pytest

from cst_runtime.core import modeling as core_modeling
from cst_runtime.core import session as core_session
from cst_runtime.core.compatibility.base import CompatibilityProfile
from cst_runtime.core.compatibility.modeling import (
    analytical_curve_vba,
    background_vba,
    change_solver_type_vba,
    cone_vba,
    cylinder_vba,
    extrude_curve_vba,
    loft_vba,
    mesh_vba,
    mesh_fpbavoid_nonreg_unite_vba,
    monitor_vba,
    plot_export_vba,
    polygon3d_vba,
    postprocess_activation_vba,
    port_vba,
    rectangle_vba,
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
    assert '.TemperatureUnit "celsius"' in text
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
        ("degC", "celsius"),
        ("K", "kelvin"),
        ("degF", "fahrenheit"),
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
    assert '.MinimumStepNumber "5"' in text
    assert ".MinimumLineNumber" not in text
    assert generated.not_applied["steps_per_box_far"] == 1
    for marker in ("MeshSettings", "PBAVersion", "TSTVersion", "SetCADProcessingMethod"):
        assert marker not in text


def test_2022_mesh_rejects_nondefault_unmappable_far_box_setting() -> None:
    with pytest.raises(UnsupportedFeatureError) as caught:
        mesh_vba(
            steps_per_wave_near=5,
            steps_per_wave_far=5,
            steps_per_box_near=5,
            steps_per_box_far=2,
            edge_refinement_ratio=2,
            edge_refinement_buffer_lines=3,
            ratio_limit_geometry=10,
            equilibrate_value=1.5,
            use_gpu=True,
            profile=CST2022,
        )

    assert "steps_per_box_far" in caught.value.context["unsupported_arguments"]


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
            name="farfield (f=1-3)",
            profile=CST2022,
        )
    )
    assert '.Name "farfield (f=1-3)"' in text
    assert '.FrequencySamples "5"' in text
    assert "CreateUsingLinearStep" not in text


def test_2022_efield_monitor_rejects_frequency_range() -> None:
    with pytest.raises(UnsupportedFeatureError, match="只支持单频"):
        monitor_vba(
            field_type="Efield",
            start=1,
            end=2,
            step=0.3,
            name="e-field (f=1-2)",
            profile=CST2022,
        )


def test_2022_efield_monitor_uses_single_frequency_method() -> None:
    generated = monitor_vba(
        field_type="Efield",
        start=8,
        end=8,
        step=1,
        name="e-field (f=8)",
        profile=CST2022,
    )
    text = _text(generated)

    assert '.Name "e-field (f=8)"' in text
    assert '.Frequency "8"' in text
    assert ".FrequencyRange" not in text
    assert ".FrequencySamples" not in text
    assert generated.not_applied["step"] == 1


def test_2022_hfield_monitor_rejects_multiple_samples() -> None:
    with pytest.raises(UnsupportedFeatureError, match="FrequencySamples"):
        monitor_vba(
            field_type="Hfield",
            start=8,
            end=8,
            samples=5,
            name="h-field (f=8)",
            profile=CST2022,
        )


def test_monitor_rejects_empty_name_before_generating_vba() -> None:
    with pytest.raises(ValidationError, match="监视器名称不能为空"):
        monitor_vba(
            field_type="Farfield",
            start=2.35,
            end=2.55,
            step=0.05,
            name="  ",
            profile=CST2022,
        )


def test_2022_farfield_monitor_generates_valid_name_and_five_samples() -> None:
    text = _text(
        monitor_vba(
            field_type="Farfield",
            start=2.35,
            end=2.55,
            step=0.05,
            name="farfield (f=2.35-2.55)",
            enable_nearfield=True,
            profile=CST2022,
        )
    )

    assert '.Name "farfield (f=2.35-2.55)"' in text
    assert '.FrequencyRange "2.35", "2.55"' in text
    assert '.FrequencySamples "5"' in text
    assert '.EnableNearfieldCalculation "True"' in text


def test_2022_broadband_farfield_omits_subvolume_methods_when_disabled() -> None:
    text = _text(
        monitor_vba(
            field_type="Farfield",
            start=2.35,
            end=2.55,
            step=0.05,
            name="farfield (f=2.35-2.55)",
            subvolume=(-105, 105, -105, 105, 0, 445),
            use_subvolume=False,
            profile=CST2022,
        )
    )

    assert ".UseSubvolume" not in text
    assert ".SetSubvolume" not in text


def test_2022_monitor_sets_coordinates_when_subvolume_is_enabled() -> None:
    text = _text(
        monitor_vba(
            field_type="Efield",
            start=8,
            end=8,
            name="e-field (f=8)",
            subvolume=(-1, 1, -2, 2, 0, 10),
            use_subvolume=True,
            profile=CST2022,
        )
    )

    assert '.UseSubvolume "True"' in text
    assert '.SetSubvolume "-1", "1", "-2", "2", "0", "10"' in text


def test_set_farfield_monitor_passes_nonempty_generated_name(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_submit(project_path, history_name, builder, **arguments):
        captured.update(arguments)
        return {"status": "success"}

    monkeypatch.setattr(core_modeling, "_submit_versioned_vba", fake_submit)

    result = core_modeling.set_farfield_monitor(
        "D:/project.cst",
        start_freq=2.35,
        end_freq=2.55,
        step=0.05,
    )

    assert result["status"] == "success"
    assert captured["name"] == "farfield (f=2.35-2.55)"
    assert captured["use_subvolume"] is False
    assert captured["subvolume"] is None


def test_other_monitor_entrypoints_pass_nonempty_generated_names(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_submit(project_path, history_name, builder, **arguments):
        captured.clear()
        captured.update(arguments)
        return {"status": "success"}

    monkeypatch.setattr(core_modeling, "_submit_versioned_vba", fake_submit)
    monkeypatch.setattr(core_modeling, "detect_compatibility_profile", lambda: CST2022)

    core_modeling.set_efield_monitor(
        "D:/project.cst",
        start_freq=2.35,
        end_freq=2.35,
        step=0.05,
    )
    assert captured["name"] == "e-field (f=2.35)"
    assert captured["use_subvolume"] is False
    assert captured["subvolume"] is None

    core_modeling.set_field_monitor(
        "D:/project.cst",
        field_type="H",
        start_frequency="2.35",
        end_frequency="2.35",
        num_samples="1",
    )
    assert captured["name"] == "h-field (f=2.35)"
    assert captured["field_type"] == "Hfield"


def test_2026_efield_entrypoint_keeps_range_name(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_submit(project_path, history_name, builder, **arguments):
        captured.update(arguments)
        return {"status": "success"}

    monkeypatch.setattr(core_modeling, "_submit_versioned_vba", fake_submit)
    monkeypatch.setattr(core_modeling, "detect_compatibility_profile", lambda: CST2026)

    core_modeling.set_efield_monitor("D:/project.cst", 2.35, 2.55, 0.05)

    assert captured["name"] == "e-field (f=2.35-2.55)"


def test_define_monitor_name_reflects_requested_range_without_fake_suffix(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_submit(project_path, history_name, builder, **arguments):
        captured.update(arguments)
        captured["generated"] = builder(profile=CST2022, **arguments)
        return {"status": "success"}

    monkeypatch.setattr(core_modeling, "_submit_versioned_vba", fake_submit)

    core_modeling.define_monitor("D:/project.cst", 8, 12, 1)

    assert captured["name"] == "farfield (f=8-12)"
    generated = captured["generated"]
    text = _text(generated)
    assert ".UseSubvolume" not in text
    assert ".SetSubvolume" not in text
    assert generated.not_applied == {
        "use_subvolume": True,
        "subvolume": (-105, 105, -105, 105, 0, 445),
    }


def test_set_probe_normalizes_documented_eh_values(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_single(project_path, history_name, vba, project=None):
        captured["history_name"] = history_name
        captured["vba"] = vba
        return {"status": "success"}

    monkeypatch.setattr(core_modeling, "_single_vba", fake_single)

    result = core_modeling.set_probe("D:/project.cst", "H", "1", "2", "3")

    assert result["status"] == "success"
    assert 'Probe.Field "hfield"' in captured["vba"]
    assert "hfieldfield" not in captured["vba"]


def test_set_probe_rejects_non_eh_field_before_vba(monkeypatch) -> None:
    monkeypatch.setattr(
        core_modeling,
        "_single_vba",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("不得提交 VBA")),
    )

    result = core_modeling.set_probe("D:/project.cst", "e-field", "1", "2", "3")

    assert result["status"] == "error"
    assert result["error_type"] == "validation_error"


def test_export_paths_follow_2022_documented_result_names(monkeypatch) -> None:
    captured: list[str] = []

    def fake_export(project_path, tree_path, file_path, history_name):
        captured.append(tree_path)
        return {"status": "success"}

    monkeypatch.setattr(core_modeling, "_ascii_export", fake_export)

    core_modeling.export_e_field("D:/project.cst", "8", "D:/exports")
    core_modeling.export_voltage("D:/project.cst", "1", "D:/exports")

    assert captured == [
        "2D/3D Results\\E-Field\\e-field (f=8) [1]",
        "1D Results\\Voltage Monitors\\voltage1",
    ]


def test_ascii_export_checks_tree_selection_before_export(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_single(project_path, history_name, vba, project=None):
        captured["vba"] = vba
        return {"status": "success"}

    monkeypatch.setattr(core_modeling, "_single_vba", fake_single)

    core_modeling._ascii_export(
        "D:/project.cst",
        "2D/3D Results\\E-Field\\e-field (f=8) [1]",
        'D:/exports/e-field "8".txt',
        "ExportEField",
    )

    assert "If Not SelectTreeItem" in captured["vba"]
    assert "ReportError" in captured["vba"]
    assert 'ASCIIExport.FileName "D:/exports/e-field ""8"".txt"' in captured["vba"]


def test_2022_plot_export_uses_vba_global_object() -> None:
    text = _text(
        plot_export_vba(
            preset_name="Isometric",
            output_path='D:/exports/model "view".png',
            profile=CST2022,
        )
    )

    assert 'Plot.RestoreView "Perspective"' in text
    assert "Plot.ZoomToStructure" in text
    assert 'Plot.ExportImage "D:/exports/model ""view"".png", 1920, 1080' in text
    assert "modeler.Plot" not in text


def test_capture_3d_view_submits_plot_vba_through_history_gateway(
    tmp_path, monkeypatch
) -> None:
    project_path = tmp_path / "model.cst"
    output_dir = tmp_path / "screenshots"
    project_path.write_bytes(b"cst")
    fake_project = object()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        core_session,
        "open_project",
        lambda project_path: {"status": "success", "already_open": True},
    )
    monkeypatch.setattr(
        core_session,
        "get_attached_project",
        lambda project_path: fake_project,
    )
    monkeypatch.setattr(core_modeling, "detect_compatibility_profile", lambda: CST2022)

    def fake_history(project_path, history_name, vba_lines, project=None):
        captured["history_name"] = history_name
        captured["vba_lines"] = list(vba_lines)
        export_line = next(line for line in vba_lines if line.startswith("Plot.ExportImage"))
        image_path = export_line.split('"', 2)[1].replace('""', '"')
        output = core_modeling.Path(image_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"png")
        return {"status": "success"}

    monkeypatch.setattr(core_modeling, "_add_vba_history", fake_history)

    result = core_modeling.capture_3d_view(
        project_path=str(project_path),
        output_dir=str(output_dir),
        preset_name="Isometric",
    )

    assert result["status"] == "success"
    assert captured["history_name"] == "Capture 3D View:Isometric"
    assert any(
        line.startswith("Plot.ExportImage") for line in captured["vba_lines"]
    )
    assert core_modeling.Path(result["image_path"]).is_file()


def test_separate_cleanup_failure_preserves_main_success(monkeypatch) -> None:
    result = {"status": "success", "execution": "completed"}
    monkeypatch.setattr(
        core_modeling,
        "_single_vba",
        lambda *args, **kwargs: {
            "status": "error",
            "error_type": "vba_runtime_error",
            "message": "cleanup failed",
        },
    )

    core_modeling._run_separate_cleanup(
        "D:/project.cst",
        result,
        "Cleanup temporary object",
        'WCS.Delete "temporary"',
        target="temporary",
    )

    assert result["status"] == "success"
    assert result["cleanup"]["status"] == "warning"
    assert result["cleanup"]["result"]["error_type"] == "vba_runtime_error"


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

    assert 'If Not SelectTreeItem("Curves\\c") Then' in legacy
    assert 'Curve.NewCurve "c"' in legacy
    assert '.Point "0", "0", "0"' in legacy
    assert legacy.count('.Point "0", "0", "0"') == 1
    assert '.Point "0:0:0", "1:2:0", "2:0:0"' in modern
    assert '.Closed "False"' in modern
    assert 'If Not SelectTreeItem("Curves\\c\\p") Then' in modern
    assert 'ReportError "Polygon3D.Create: Curve item was not created: c:p"' in modern
    assert "Err.Raise" not in modern
    assert "Curve item was not created: c:p" in modern
    assert ".Version" not in modern


def test_polygon3d_preserves_explicit_closing_point() -> None:
    modern = _text(
        polygon3d_vba(
            "profile",
            "cut_profiles",
            [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 0)],
            profile=CST2026,
        )
    )

    assert '.Point "0:0:0", "1:0:0", "0:1:0", "0:0:0"' in modern
    assert '.Closed "False"' in modern


def test_polygon3d_rejects_fewer_than_three_points() -> None:
    with pytest.raises(ValidationError, match="至少需要三个"):
        polygon3d_vba("p", "c", [(0, 0, 0), (1, 0, 0)], profile=CST2022)


def test_analytical_curve_creates_container_and_uses_status_gateway_error() -> None:
    text = _text(
        analytical_curve_vba(
            name="helix",
            curve="curves1",
            law_x="cos(t)",
            law_y="sin(t)",
            law_z="t",
            param_start="0",
            param_end="2*pi",
            profile=CST2022,
        )
    )

    assert 'If Not SelectTreeItem("Curves\\curves1") Then' in text
    assert 'Curve.NewCurve "curves1"' in text
    assert 'If Not SelectTreeItem("Curves\\curves1\\helix") Then' in text
    assert 'ReportError "AnalyticalCurve.Create: Curve item was not created: curves1:helix"' in text
    assert "Err.Raise" not in text


def test_2022_polygon_extrude_and_transform_snapshots() -> None:
    polygon = _text(
        polygon3d_vba(
            "p",
            "c",
            [(0, 0, 0), (1, 0, 0), (0, 1, 0)],
            profile=CST2022,
        )
    )
    extrude = _text(
        extrude_curve_vba(
            name="solid",
            component="component1",
            material="PEC",
            curve="curve1:profile",
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
    assert '.Curve "curve1:profile"' in extrude
    assert "Curve.DeleteCurve" not in extrude
    assert "AutoDestination" not in transform
    assert ".Destination" not in transform


def test_2022_extrude_requires_full_curve_item_name() -> None:
    with pytest.raises(ValidationError, match="container:item"):
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


def test_2022_extrude_relies_on_automatic_profile_consumption() -> None:
    generated = extrude_curve_vba(
        name="cut",
        component="antenna",
        material="PEC",
        curve="cut_profiles:cut_profile",
        thickness=1,
        twist_angle=0,
        taper_angle=0,
        delete_profile=True,
        profile=CST2022,
    )

    assert "Curve.DeleteCurve" not in _text(generated)
    assert generated.not_applied == {}


def test_2022_extrude_cannot_preserve_profile() -> None:
    generated = extrude_curve_vba(
        name="cut",
        component="antenna",
        material="PEC",
        curve="cut_profiles:cut_profile",
        thickness=1,
        twist_angle=0,
        taper_angle=0,
        delete_profile=False,
        profile=CST2022,
    )

    assert generated.not_applied == {"delete_profile": False}


def test_2022_rectangle_creates_container_and_reports_through_gateway() -> None:
    text = _text(
        rectangle_vba(
            name="outline",
            curve="profiles",
            x_min="xmin",
            x_max="xmax",
            y_min=-1,
            y_max=1,
            profile=CST2022,
        )
    )

    assert 'Curve.NewCurve "profiles"' in text
    assert '.Xrange "xmin", "xmax"' in text
    assert 'ReportError "Rectangle.Create: Curve item was not created: profiles:outline"' in text
    assert "Err.Raise" not in text


def test_2022_loft_omits_undocumented_minimize_twist() -> None:
    legacy = loft_vba(
        name="loft1",
        component="component1",
        material="PEC",
        tangency=0,
        minimize_twist=True,
        profile=CST2022,
    )
    modern = loft_vba(
        name="loft1",
        component="component1",
        material="PEC",
        tangency=0,
        minimize_twist=True,
        profile=CST2026,
    )

    assert ".Minimizetwist" not in _text(legacy)
    assert legacy.not_applied == {"minimize_twist": True}
    assert '.Minimizetwist "True"' in _text(modern)


def test_change_solver_type_uses_vba_sub_syntax_without_parentheses() -> None:
    text = _text(
        change_solver_type_vba(
            solver_type="HF Time Domain",
            profile=CST2022,
        )
    )

    assert text == 'ChangeSolverType "HF Time Domain"'
    assert "ChangeSolverType(" not in text


def test_change_solver_type_rejects_value_outside_2022_manual() -> None:
    with pytest.raises(ValidationError, match="ChangeSolverType 文档列出的合法值"):
        change_solver_type_vba(
            solver_type="HF Unknown Solver",
            profile=CST2022,
        )


def test_change_solver_type_returns_validation_error_before_history_submission(monkeypatch) -> None:
    monkeypatch.setattr(core_modeling, "detect_compatibility_profile", lambda: CST2022)
    monkeypatch.setattr(
        core_modeling,
        "_add_vba_history",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("非法求解器类型不得提交 History")
        ),
    )

    result = core_modeling.change_solver_type("D:/project.cst", "HF Unknown Solver")

    assert result["status"] == "error"
    assert result["error_type"] == "validation_error"
    assert result["error"]["phase"] == "validation"


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
