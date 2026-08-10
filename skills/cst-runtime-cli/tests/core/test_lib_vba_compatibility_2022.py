from __future__ import annotations

from cst_runtime.core.compatibility.base import CompatibilityProfile
from cst_runtime.core.compatibility.lib import (
    activate_wcs_vba,
    arc_vba,
    boundary_per_face_vba,
    floquet_port_vba,
    polygon_solid_vba,
    translate_vba,
    waveguide_port_vba,
)


CST2022 = CompatibilityProfile(major=2022, version="2022", source="test")


def _text(generated) -> str:
    return "\n".join(generated.lines)


def test_periodic_boundary_uses_2022_angle_api() -> None:
    text = _text(
        boundary_per_face_vba(
            faces=("unit cell", "unit cell", "unit cell", "unit cell", "open", "open"),
            periodic_angle=15,
            profile=CST2022,
        )
    )
    assert 'PeriodicUseConstantAngles "True"' in text
    assert 'SetPeriodicBoundaryAngles "15", "0"' in text
    assert "PeriodicUsePrimitive" not in text


def test_translate_omits_new_destination_properties() -> None:
    text = _text(
        translate_vba(
            name="component1:solid1",
            vector=(1, 2, 3),
            multiple_objects=False,
            repetitions=1,
            destination="",
            profile=CST2022,
        )
    )
    assert '.Vector "1", "2", "3"' in text
    assert "AutoDestination" not in text
    assert ".Destination" not in text


def test_wcs_uses_store_instead_of_set_name() -> None:
    text = _text(
        activate_wcs_vba(
            name="local1",
            origin=(0, 0, 2),
            normal=(0, 0, 1),
            uvector=(1, 0, 0),
            profile=CST2022,
        )
    )
    assert '.Store "local1"' in text
    assert ".SetName" not in text


def test_arc_uses_legacy_points_and_restores_wcs() -> None:
    generated = arc_vba(
        name="arc1",
        curve="curve1",
        center=(1, 2, 3),
        radius=5,
        start_angle=0,
        end_angle=90,
        segments=0,
        profile=CST2022,
    )
    text = _text(generated)
    assert 'If Not SelectTreeItem("Curves\\curve1") Then' in text
    assert 'Curve.NewCurve "curve1"' in text
    assert ".Xcenter" in text
    assert '.UseAngle "True"' in text
    assert "WCS.Restore" in text
    assert "WCS.Delete" not in text
    assert generated.not_applied["wcs_cleanup"].startswith("__CSTRuntime_")
    assert 'ReportError "Arc.Create: Curve item was not created: curve1:arc1"' in text
    assert "Err.Raise" not in text
    assert ".StartAngle" not in text


def test_polygon_builds_2d_profile_then_extrudes_without_unsafe_cleanup() -> None:
    generated = polygon_solid_vba(
        name="plate",
        component="component1",
        material="PEC",
        vertices=((0, 0), (1, 0), (0, 1)),
        z_range=(0, 1),
        profile=CST2022,
    )
    text = _text(generated)
    assert 'If Not SelectTreeItem("Curves\\__cst_runtime_plate") Then' in text
    assert 'Curve.NewCurve "__cst_runtime_plate"' in text
    assert "With Polygon\n" in text
    assert "With Polygon3D" not in text
    assert 'If Not SelectTreeItem("Curves\\__cst_runtime_plate\\profile") Then' in text
    assert 'ReportError "Polygon.Create: Curve item was not created: __cst_runtime_plate:profile"' in text
    assert "Err.Raise" not in text
    assert "With ExtrudeCurve" in text
    assert '.Curve "__cst_runtime_plate:profile"' in text
    assert "Curve.DeleteCurve" not in text
    assert ".DeleteProfile" not in text
    assert generated.not_applied == {}


def test_waveguide_port_uses_structure_box_and_legacy_ranges() -> None:
    text = _text(
        waveguide_port_vba(
            port_number=1,
            face="zmax",
            width=10,
            height=5,
            profile=CST2022,
        )
    )
    assert "Boundary.GetStructureBox" in text
    assert ".Zrange cstRtZmax, cstRtZmax" in text
    assert ".SetPortType" not in text
    assert ".Face" not in text


def test_floquet_port_uses_dedicated_2022_object() -> None:
    text = _text(
        floquet_port_vba(
            zmin_modes=2,
            zmax_modes=2,
            zmin_reference_distance=-1,
            zmax_reference_distance=-2,
            polarization_type="linear",
            profile=CST2022,
        )
    )
    assert "With FloquetPort" in text
    assert '.Port "Zmin"' in text
    assert '.AddMode "TE", "0", "0"' in text
    assert '.AddMode "TM", "0", "0"' in text
    assert '.SetDistanceToReferencePlane "-2"' in text
    assert "CreateFloquetPort" not in text
