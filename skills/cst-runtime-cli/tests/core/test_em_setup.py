"""超表面电磁设置的离线契约测试。"""
from __future__ import annotations

from pathlib import Path

import pytest

from cst_runtime.core import em_setup
from cst_runtime.core.compatibility.base import CompatibilityProfile
from cst_runtime.core.compatibility.em_setup import (
    floquet_port_setup_vba,
    frequency_domain_solver_vba,
    plane_wave_vba,
    unit_cell_boundary_vba,
)


PROFILE = CompatibilityProfile(major=2022, version="2022", source="test")


@pytest.mark.parametrize(
    "faces",
    [
        ("unit cell", "unit cell", "unit cell", "unit cell"),
        ("periodic", "periodic", "open", "open"),
        ("open", "open", "periodic", "periodic"),
    ],
)
def test_boundary_valid_pairing_reaches_submission(monkeypatch, tmp_path: Path, faces) -> None:
    captured = {}

    def fake_submit(project_path, history_name, builder, **arguments):
        captured.update(arguments)
        return {"status": "success", "submission": "buffered"}

    monkeypatch.setattr(em_setup, "_submit_versioned_vba", fake_submit)
    result = em_setup.define_unit_cell_boundary(
        str(tmp_path / "model.cst"),
        xmin=faces[0], xmax=faces[1], ymin=faces[2], ymax=faces[3],
        zmin="open", zmax="expanded open", theta=12.0, phi=23.0, direction="inward",
    )
    assert result["status"] == "success"
    assert captured["theta"] == 12.0
    assert captured["phi"] == 23.0
    assert captured["direction"] == "inward"


@pytest.mark.parametrize(
    "faces",
    [
        # 一个代表（X 向 periodic 与 X 向 open 冲突）+ 一个边界（unit cell 与 open 混配）
        ("periodic", "open", "open", "open"),
        ("unit cell", "unit cell", "unit cell", "open"),
    ],
)
def test_invalid_boundary_pairing_never_calls_builder_history_or_cst(monkeypatch, tmp_path: Path, faces) -> None:
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("非法边界不应到达提交层")

    monkeypatch.setattr(em_setup, "_submit_versioned_vba", forbidden)
    monkeypatch.setattr(em_setup, "attach_expected_project", forbidden)
    result = em_setup.define_unit_cell_boundary(
        str(tmp_path / "model.cst"),
        xmin=faces[0], xmax=faces[1], ymin=faces[2], ymax=faces[3],
        zmin="open", zmax="open",
    )
    assert result["status"] == "error"
    assert result["error_type"] == "invalid_boundary_pairing"
    assert calls == []


def test_boundary_builder_uses_angles_and_direction() -> None:
    generated = unit_cell_boundary_vba(
        faces=("Unit Cell", "Unit Cell", "Unit Cell", "Unit Cell", "Open", "Expanded Open"),
        theta=10.0, phi=20.0, direction="outward", profile=PROFILE,
    )
    script = "\n".join(generated.lines)
    assert '.PeriodicUseConstantAngles "True"' in script
    assert '.SetPeriodicBoundaryAngles "10", "20"' in script
    assert '.SetPeriodicBoundaryAnglesDirection "outward"' in script


def test_inspect_boundary_parses_public_getters(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(em_setup, "attach_expected_project", lambda path: (object(), {"status": "success"}))
    monkeypatch.setattr(
        em_setup,
        "execute_text_query",
        lambda project, lines: [
            "FACE\txmin\tUnit Cell", "FACE\txmax\tUnit Cell",
            "FACE\tymin\tUnit Cell", "FACE\tymax\tUnit Cell",
            "FACE\tzmin\tOpen", "FACE\tzmax\tExpanded Open",
            "SCAN\tTrue\t10\t20\t-1",
        ],
    )
    result = em_setup.inspect_boundary(str(tmp_path / "model.cst"))
    assert result["status"] == "success"
    assert result["faces"]["xmin"] == "Unit Cell"
    assert result["unit_cell_scan"] == {"available": True, "theta": 10.0, "phi": 20.0, "direction": "inward"}


def test_boundary_write_does_not_run_post_execution_readback(monkeypatch, tmp_path: Path) -> None:
    submitted = {
        "status": "success",
        "submission": "accepted",
        "execution": "reported_ok",
    }
    monkeypatch.setattr(em_setup, "_submit_versioned_vba", lambda *a, **k: dict(submitted))
    monkeypatch.setattr(
        em_setup,
        "inspect_boundary",
        lambda _path: pytest.fail("写操作成功后不得自动读回 Boundary"),
    )
    result = em_setup.define_unit_cell_boundary(
        str(tmp_path / "model.cst"), xmin="unit cell", xmax="unit cell",
        ymin="unit cell", ymax="unit cell", zmin="open", zmax="open",
    )
    assert result == submitted


def _explicit_ports() -> list[dict]:
    return [
        {
            "position": "Zmin", "mode_strategy": "explicit",
            "modes": [
                {"type": "TE", "order_x": 0, "order_yprime": 0},
                {"type": "TM", "order_x": 0, "order_yprime": 0},
            ],
            "modes_considered": 2, "reference_distance": 1.25,
        }
    ]


def test_floquet_explicit_builder_adds_modes_and_reference_plane() -> None:
    generated = floquet_port_setup_vba(
        ports=_explicit_ports(), polarization_basis="linear", sort_code="+beta/pw",
        sort_frequency=10.0, sort_theta=5.0, sort_phi=6.0,
        max_order_x=2, max_order_yprime=3, profile=PROFILE,
    )
    script = "\n".join(generated.lines)
    assert '.SetCustomizedListFlag "True"' in script
    assert '.AddMode "TE", "0", "0"' in script
    assert '.AddMode "TM", "0", "0"' in script
    assert '.SetDistanceToReferencePlane "1.25"' in script
    assert '.SetSortCode "+beta/pw"' in script


def test_floquet_automatic_does_not_guess_mode_table() -> None:
    generated = floquet_port_setup_vba(
        ports=[{"position": "Zmax", "mode_strategy": "automatic", "modes": [], "modes_considered": 4, "reference_distance": 0}],
        polarization_basis="circular", sort_code="+beta", sort_frequency=None,
        sort_theta=0, sort_phi=0, max_order_x=2, max_order_yprime=2, profile=PROFILE,
    )
    script = "\n".join(generated.lines)
    assert '.SetCustomizedListFlag "False"' in script
    assert ".AddMode" not in script
    assert '.SetDialogMaxOrderX "2"' in script
    assert '.SetUseCircularPolarization "True"' in script


def test_floquet_omits_unset_optional_dialogs() -> None:
    """未提供的可选数值对话框不得生成空字符串 setter（CST 2022 会报 VBA 运行时错误）。"""
    generated = floquet_port_setup_vba(
        ports=[{"position": "Zmin", "mode_strategy": "automatic", "modes": [], "modes_considered": 2, "reference_distance": 0}],
        polarization_basis="linear", sort_code="+beta/pw", sort_frequency=None,
        sort_theta=0, sort_phi=0, max_order_x=None, max_order_yprime=None, profile=PROFILE,
    )
    script = "\n".join(generated.lines)
    assert "SetDialogFrequency" not in script
    assert "SetDialogMaxOrderX" not in script
    assert "SetDialogMaxOrderYPrime" not in script
    assert '""' not in script
    assert '.SetSortCode "+beta/pw"' in script


@pytest.mark.parametrize(
    "ports,basis",
    [
        # 空端口 / 显式策略缺模式表 / 线极化配圆极化模式，各命中一个不同校验分支
        ([], "linear"),
        ([{"position": "Zmin", "mode_strategy": "explicit", "modes": [], "modes_considered": 1, "reference_distance": 0}], "linear"),
        ([{"position": "Zmin", "mode_strategy": "explicit", "modes": [{"type": "LCP", "order_x": 1, "order_yprime": 0}], "modes_considered": 1, "reference_distance": 0}], "circular"),
    ],
)
def test_invalid_floquet_combinations_are_rejected(monkeypatch, tmp_path: Path, ports, basis) -> None:
    monkeypatch.setattr(em_setup, "_submit_versioned_vba", lambda *a, **k: pytest.fail("不得提交"))
    result = em_setup.define_floquet_port(str(tmp_path / "model.cst"), ports=ports, polarization_basis=basis)
    assert result["status"] == "error"
    assert result["error_type"] == "invalid_floquet_configuration"


def test_inspect_floquet_returns_only_publicly_readable_fields(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(em_setup, "attach_expected_project", lambda path: (object(), {"status": "success"}))
    monkeypatch.setattr(
        em_setup,
        "execute_text_query",
        lambda project, lines: [
            "PORT\tZmin\tTrue\t2\t2", "MODE\tZmin\t1\tTE(0,0)", "MODE\tZmin\t2\tTM(0,0)",
            "PORT\tZmax\tFalse\t0\t1",
        ],
    )
    result = em_setup.inspect_floquet_ports(str(tmp_path / "model.cst"))
    assert result["status"] == "success"
    assert result["ports"][0]["modes"][0]["type"] == "TE"
    assert "reference_distance" in result["unavailable_fields"]
    assert "reference_distance" not in result["ports"][0]


def test_floquet_write_does_not_run_post_execution_readback(monkeypatch, tmp_path: Path) -> None:
    submitted = {
        "status": "success",
        "submission": "accepted",
        "execution": "reported_ok",
    }
    monkeypatch.setattr(em_setup, "_submit_versioned_vba", lambda *a, **k: dict(submitted))
    monkeypatch.setattr(
        em_setup,
        "inspect_floquet_ports",
        lambda _path: pytest.fail("写操作成功后不得自动读回 FloquetPort"),
    )
    result = em_setup.define_floquet_port(str(tmp_path / "model.cst"), ports=_explicit_ports())
    assert result == submitted


@pytest.mark.parametrize(
    "polarization,extra,expected",
    [
        ("Linear", {}, '.Polarization "Linear"'),
        ("Circular", {"reference_frequency": 10, "handedness": "Left"}, '.CircularDirection "Left"'),
        ("Elliptical", {"reference_frequency": 10, "handedness": "Right", "phase_difference": 90, "axial_ratio": 2}, '.AxialRatio "2"'),
    ],
)
def test_plane_wave_builders_cover_three_polarizations(polarization, extra, expected) -> None:
    normalized = em_setup._normalize_plane_wave([0, 0, -1], [1, 0, 0], polarization, extra.get("reference_frequency"), extra.get("handedness"), extra.get("phase_difference"), extra.get("axial_ratio"))
    generated = plane_wave_vba(
        normal=normalized[0], e_vector=normalized[1], polarization=normalized[2],
        reference_frequency=normalized[3], handedness=normalized[4],
        phase_difference=normalized[5], axial_ratio=normalized[6], profile=PROFILE,
    )
    script = "\n".join(generated.lines)
    assert "PlaneWave" in script
    assert ".Reset" in script and ".Store" in script
    assert expected in script


def test_plane_wave_parallel_vectors_are_rejected(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(em_setup, "_submit_versioned_vba", lambda *a, **k: pytest.fail("不得提交"))
    result = em_setup.define_plane_wave(
        str(tmp_path / "model.cst"), normal=[0, 0, 1], e_vector=[0, 0, -2]
    )
    assert result["status"] == "error"
    assert result["error_type"] == "invalid_plane_wave"


def test_inspect_plane_wave_parses_all_getters(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(em_setup, "attach_expected_project", lambda path: (object(), {"status": "success"}))
    captured = {}

    def fake_query(project, lines):
        captured["script"] = "\n".join(lines)
        return [
            "NORMAL\t0\t0\t-1", "EVECTOR\t1\t0\t0", "VALUE\tpolarization\tCircular",
            "VALUE\treference_frequency\t10", "VALUE\tcircular_direction\tRight",
            "VALUE\tphase_difference\t90", "VALUE\taxial_ratio\t1",
        ]

    monkeypatch.setattr(em_setup, "execute_text_query", fake_query)
    result = em_setup.inspect_plane_wave(str(tmp_path / "model.cst"))
    assert result["status"] == "success"
    assert result["plane_wave"]["normal"] == [0.0, 0.0, -1.0]
    assert result["plane_wave"]["circular_direction"] == "Right"
    assert "GetPolarizationType" in captured["script"]
    assert "GetPolarization\n" not in captured["script"] + "\n"


def test_plane_wave_write_does_not_run_post_execution_readback(monkeypatch, tmp_path: Path) -> None:
    submitted = {
        "status": "success",
        "submission": "accepted",
        "execution": "reported_ok",
    }
    monkeypatch.setattr(em_setup, "_submit_versioned_vba", lambda *a, **k: dict(submitted))
    monkeypatch.setattr(
        em_setup,
        "inspect_plane_wave",
        lambda _path: pytest.fail("写操作成功后不得自动读回 PlaneWave"),
    )
    result = em_setup.define_plane_wave(str(tmp_path / "model.cst"), normal=[0, 0, -1], e_vector=[1, 0, 0])
    assert result == submitted


@pytest.mark.parametrize(
    "excitation,expected",
    [
        ({"strategy": "all"}, 'Stimulation "All", "All"'),
        ({"strategy": "all_with_floquet"}, 'Stimulation "All+Floquet", "All+Floquet"'),
        ({"strategy": "plane_wave"}, 'Stimulation "Plane Wave", 1'),
        ({"strategy": "single", "port": 2, "mode": 3}, "Stimulation 2, 3"),
        ({"strategy": "list", "items": [{"port": "1", "mode": "2"}]}, 'AddToExcitationList "1", "2"'),
    ],
)
def test_fdsolver_only_sets_method_and_excitation(excitation, expected) -> None:
    generated = frequency_domain_solver_vba(mesh_method="Tetrahedral", excitation=excitation, profile=PROFILE)
    script = "\n".join(generated.lines)
    assert 'ChangeSolverType "HF Frequency Domain"' in script
    assert 'SetMethod "Tetrahedral", ""' in script
    assert expected in script
    assert "FDSolver.Reset\n" not in script + "\n"
    assert "Accuracy" not in script
    assert "Adaptive" not in script
    assert "Sweep" not in script
    if excitation["strategy"] != "list":
        assert "ResetExcitationList" not in script


def test_list_monitors_parses_monitor_getters(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(em_setup, "attach_expected_project", lambda path: (object(), {"status": "success"}))
    monkeypatch.setattr(em_setup, "execute_text_query", lambda project, lines: ["MONITOR\tff10\tFarfield\tFrequency\t10"])
    result = em_setup.list_monitors(str(tmp_path / "model.cst"))
    assert result["status"] == "success"
    assert result["monitors"] == [{"name": "ff10", "type": "Farfield", "domain": "Frequency", "frequency": 10.0}]
