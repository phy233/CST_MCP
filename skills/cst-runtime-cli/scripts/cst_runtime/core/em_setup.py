"""超表面电磁设置、读回验收与监视器查询。"""
from __future__ import annotations

import math
import re
from typing import Any, Iterable, Sequence

from .compatibility.em_setup import (
    FLOQUET_SORT_CODES,
    floquet_port_setup_vba,
    frequency_domain_solver_vba,
    plane_wave_vba,
    unit_cell_boundary_vba,
)
from .compatibility.execution import execute_text_query
from .errors import CSTRuntimeError, error_response, success_response
from .identity import attach_expected_project
from .modeling import _submit_versioned_vba
from .utils import abs_project_path


_SIDE_BOUNDARIES = {
    "electric",
    "magnetic",
    "open",
    "expanded open",
    "periodic",
    "unit cell",
}
_Z_BOUNDARIES = {"open", "expanded open"}
_MODE_NAME = re.compile(r"^(TE|TM|LCP|RCP)\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)$", re.IGNORECASE)


def _finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} 必须是有限数值") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} 必须是有限数值")
    return number


def _integer(value: Any, name: str, *, minimum: int | None = 0) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} 必须是整数")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} 必须是整数") from exc
    if number != value:
        raise ValueError(f"{name} 必须是整数")
    if minimum is not None and number < minimum:
        raise ValueError(f"{name} 必须是不小于 {minimum} 的整数")
    return number


def _normalize_face(value: Any, name: str, allowed: set[str]) -> str:
    normalized = " ".join(str(value).strip().casefold().split())
    if normalized not in allowed:
        raise ValueError(f"{name} 不支持边界类型 {value!r}")
    return normalized.title()


def _normalize_boundaries(
    xmin: Any,
    xmax: Any,
    ymin: Any,
    ymax: Any,
    zmin: Any,
    zmax: Any,
) -> tuple[str, str, str, str, str, str]:
    sides = [
        _normalize_face(xmin, "xmin", _SIDE_BOUNDARIES),
        _normalize_face(xmax, "xmax", _SIDE_BOUNDARIES),
        _normalize_face(ymin, "ymin", _SIDE_BOUNDARIES),
        _normalize_face(ymax, "ymax", _SIDE_BOUNDARIES),
    ]
    folded = [item.casefold() for item in sides]
    if "unit cell" in folded and any(item != "unit cell" for item in folded):
        raise ValueError("X/Y 任一侧为 Unit Cell 时，四个 X/Y 侧面必须全部为 Unit Cell")
    for axis, first, second in (("X", folded[0], folded[1]), ("Y", folded[2], folded[3])):
        if (first == "periodic") != (second == "periodic"):
            raise ValueError(f"{axis} 方向的 Periodic 边界必须在两个相对面上成对设置")
    return (
        *sides,
        _normalize_face(zmin, "zmin", _Z_BOUNDARIES),
        _normalize_face(zmax, "zmax", _Z_BOUNDARIES),
    )


def _attach(project_path: str) -> tuple[Any | None, dict[str, Any], str]:
    normalized = abs_project_path(project_path)
    project, status = attach_expected_project(normalized)
    return project, status, normalized


def _query_failure(exc: Exception, project_path: str) -> dict[str, Any]:
    if isinstance(exc, CSTRuntimeError):
        return exc.to_response(project_path=project_path)
    return error_response(
        "inspection_failed",
        str(exc),
        phase="inspection",
        project_path=project_path,
    )


def inspect_boundary(project_path: str) -> dict[str, Any]:
    """读取六面边界和 Unit Cell 扫描角，不把提交结果当作读回。"""
    project, status, normalized = _attach(project_path)
    if project is None:
        return status
    lines = [
        'Print #cstRtQueryFile, "FACE" & Chr(9) & "xmin" & Chr(9) & Boundary.GetXmin',
        'Print #cstRtQueryFile, "FACE" & Chr(9) & "xmax" & Chr(9) & Boundary.GetXmax',
        'Print #cstRtQueryFile, "FACE" & Chr(9) & "ymin" & Chr(9) & Boundary.GetYmin',
        'Print #cstRtQueryFile, "FACE" & Chr(9) & "ymax" & Chr(9) & Boundary.GetYmax',
        'Print #cstRtQueryFile, "FACE" & Chr(9) & "zmin" & Chr(9) & Boundary.GetZmin',
        'Print #cstRtQueryFile, "FACE" & Chr(9) & "zmax" & Chr(9) & Boundary.GetZmax',
        "Dim cstRtTheta As Double, cstRtPhi As Double, cstRtDirection As Long",
        "Dim cstRtHasScan As Boolean",
        "cstRtHasScan = Boundary.GetUnitCellScanAngle(cstRtTheta, cstRtPhi, cstRtDirection)",
        'Print #cstRtQueryFile, "SCAN" & Chr(9) & CStr(cstRtHasScan) & Chr(9) & CStr(cstRtTheta) & Chr(9) & CStr(cstRtPhi) & Chr(9) & CStr(cstRtDirection)',
    ]
    try:
        rows = execute_text_query(project, lines)
        faces: dict[str, str] = {}
        scan: dict[str, Any] | None = None
        for row in rows:
            parts = row.split("\t")
            if len(parts) >= 3 and parts[0] == "FACE":
                faces[parts[1]] = parts[2]
            elif len(parts) >= 5 and parts[0] == "SCAN":
                available = parts[1].strip().casefold() in {"true", "1", "-1"}
                scan = {
                    "available": available,
                    "theta": float(parts[2]),
                    "phi": float(parts[3]),
                    "direction": "outward" if int(float(parts[4])) >= 0 else "inward",
                }
        if set(faces) != {"xmin", "xmax", "ymin", "ymax", "zmin", "zmax"} or scan is None:
            raise ValueError("Boundary 查询结果不完整")
        return success_response(
            project_path=normalized,
            faces=faces,
            unit_cell_scan=scan,
        )
    except Exception as exc:
        return _query_failure(exc, normalized)


def define_unit_cell_boundary(
    project_path: str,
    *,
    xmin: Any,
    xmax: Any,
    ymin: Any,
    ymax: Any,
    zmin: Any,
    zmax: Any,
    theta: Any = 0.0,
    phi: Any = 0.0,
    direction: str = "outward",
) -> dict[str, Any]:
    """校验边界配对后提交，并在实际执行后读取 CST 状态比较。"""
    normalized_project = abs_project_path(project_path)
    try:
        # 这段校验必须位于 builder 和任何 CST 调用之前。
        faces = _normalize_boundaries(xmin, xmax, ymin, ymax, zmin, zmax)
        normalized_theta = _finite(theta, "theta")
        normalized_phi = _finite(phi, "phi")
        normalized_direction = str(direction).strip().casefold()
        if normalized_direction not in {"outward", "inward"}:
            raise ValueError("direction 仅允许 outward 或 inward")
    except ValueError as exc:
        return error_response(
            "invalid_boundary_pairing",
            str(exc),
            phase="validation",
            project_path=normalized_project,
        )
    return _submit_versioned_vba(
        normalized_project,
        "Define Unit Cell Boundary",
        unit_cell_boundary_vba,
        faces=faces,
        theta=normalized_theta,
        phi=normalized_phi,
        direction=normalized_direction,
    )


def _normalize_mode(mode: dict[str, Any], basis: str) -> dict[str, Any]:
    mode_type = str(mode.get("type", "")).strip().upper()
    allowed = {"TE", "TM"} if basis == "linear" else {"LCP", "RCP"}
    if mode_type not in allowed:
        raise ValueError(f"{basis} 极化基础只允许 {sorted(allowed)} 模式")
    order_x = _integer(mode.get("order_x"), "order_x", minimum=None)
    order_y = _integer(mode.get("order_yprime"), "order_yprime", minimum=None)
    if mode_type in {"LCP", "RCP"} and (order_x, order_y) != (0, 0):
        raise ValueError("LCP/RCP 模式的阶数必须为 (0,0)")
    return {"type": mode_type, "order_x": order_x, "order_yprime": order_y}


def _normalize_floquet(
    ports: Sequence[dict[str, Any]],
    polarization_basis: str,
    sort_code: str,
    sort_frequency: Any,
    sort_theta: Any,
    sort_phi: Any,
    max_order_x: Any,
    max_order_yprime: Any,
) -> tuple[list[dict[str, Any]], str, str, float | None, float, float, int | None, int | None]:
    basis = str(polarization_basis).strip().casefold()
    if basis not in {"linear", "circular"}:
        raise ValueError("polarization_basis 仅允许 linear 或 circular")
    normalized_sort = str(sort_code).strip().casefold()
    if normalized_sort not in FLOQUET_SORT_CODES:
        raise ValueError("sort_code 不是 CST 2022 手册规定的排序方式")
    if not ports:
        raise ValueError("ports 不得为空")
    normalized_ports: list[dict[str, Any]] = []
    seen_positions: set[str] = set()
    for raw in ports:
        position_key = str(raw.get("position", "")).strip().casefold()
        if position_key not in {"zmin", "zmax"}:
            raise ValueError("端口位置仅允许 Zmin 或 Zmax")
        if position_key in seen_positions:
            raise ValueError("Floquet 端口位置不得重复")
        seen_positions.add(position_key)
        strategy = str(raw.get("mode_strategy", "")).strip().casefold()
        if strategy not in {"explicit", "automatic"}:
            raise ValueError("mode_strategy 仅允许 explicit 或 automatic")
        modes = [_normalize_mode(item, basis) for item in raw.get("modes", [])]
        if strategy == "explicit" and not modes:
            raise ValueError("explicit 模式列表不得为空")
        if strategy == "automatic" and modes:
            raise ValueError("automatic 模式不接受显式 modes 列表")
        keys = [(item["type"], item["order_x"], item["order_yprime"]) for item in modes]
        if len(keys) != len(set(keys)):
            raise ValueError("显式 Floquet 模式不得重复")
        considered = _integer(raw.get("modes_considered"), "modes_considered", minimum=1)
        if strategy == "explicit" and considered < len(modes):
            raise ValueError("modes_considered 不得小于显式模式数量")
        normalized_ports.append(
            {
                "position": "Zmin" if position_key == "zmin" else "Zmax",
                "mode_strategy": strategy,
                "modes": modes,
                "modes_considered": considered,
                "reference_distance": _finite(raw.get("reference_distance", 0.0), "reference_distance"),
            }
        )
    frequency = None if sort_frequency is None else _finite(sort_frequency, "sort_frequency")
    max_x = None if max_order_x is None else _integer(max_order_x, "max_order_x")
    max_y = None if max_order_yprime is None else _integer(max_order_yprime, "max_order_yprime")
    return (
        normalized_ports,
        basis,
        normalized_sort,
        frequency,
        _finite(sort_theta, "sort_theta"),
        _finite(sort_phi, "sort_phi"),
        max_x,
        max_y,
    )


def inspect_floquet_ports(project_path: str) -> dict[str, Any]:
    """仅返回 CST 2022 FloquetPort 对象公开 getter 可取得的字段。"""
    project, status, normalized = _attach(project_path)
    if project is None:
        return status
    lines = [
        "Dim cstRtPosition As String, cstRtIndex As Long, cstRtName As String, cstRtOk As Boolean",
        'For Each cstRtPosition In Array("Zmin", "Zmax")',
        "    FloquetPort.Port cstRtPosition",
        '    If cstRtPosition = "Zmin" Then',
        "        cstRtOk = FloquetPort.IsPortAtZmin",
        "    Else",
        "        cstRtOk = FloquetPort.IsPortAtZmax",
        "    End If",
        '    Print #cstRtQueryFile, "PORT" & Chr(9) & cstRtPosition & Chr(9) & CStr(cstRtOk) & Chr(9) & CStr(FloquetPort.GetNumberOfModes) & Chr(9) & CStr(FloquetPort.GetNumberOfModesConsidered)',
        "    For cstRtIndex = 1 To FloquetPort.GetNumberOfModes",
        "        cstRtName = \"\"",
        "        cstRtOk = FloquetPort.GetModeNameByNumber(cstRtName, cstRtIndex)",
        '        If cstRtOk Then Print #cstRtQueryFile, "MODE" & Chr(9) & cstRtPosition & Chr(9) & CStr(cstRtIndex) & Chr(9) & cstRtName',
        "    Next cstRtIndex",
        "Next cstRtPosition",
    ]
    try:
        rows = execute_text_query(project, lines)
        ports: dict[str, dict[str, Any]] = {}
        for row in rows:
            parts = row.split("\t")
            if len(parts) >= 5 and parts[0] == "PORT":
                ports[parts[1]] = {
                    "position": parts[1],
                    "exists": parts[2].strip().casefold() in {"true", "1", "-1"},
                    "mode_count": int(parts[3]),
                    "modes_considered": int(parts[4]),
                    "modes": [],
                }
            elif len(parts) >= 4 and parts[0] == "MODE" and parts[1] in ports:
                match = _MODE_NAME.match(parts[3].strip())
                mode = {"number": int(parts[2]), "name": parts[3]}
                if match:
                    mode.update(type=match.group(1).upper(), order_x=int(match.group(2)), order_yprime=int(match.group(3)))
                ports[parts[1]]["modes"].append(mode)
        if set(ports) != {"Zmin", "Zmax"}:
            raise ValueError("FloquetPort 查询结果不完整")
        return success_response(
            project_path=normalized,
            ports=[ports["Zmin"], ports["Zmax"]],
            readable_fields=["position", "modes", "mode number/name", "modes_considered"],
            unavailable_fields=["reference_distance", "sort settings", "polarization basis"],
        )
    except Exception as exc:
        return _query_failure(exc, normalized)


def define_floquet_port(
    project_path: str,
    *,
    ports: Sequence[dict[str, Any]],
    polarization_basis: str = "linear",
    sort_code: str = "+beta/pw",
    sort_frequency: Any = None,
    sort_theta: Any = 0.0,
    sort_phi: Any = 0.0,
    max_order_x: Any = None,
    max_order_yprime: Any = None,
) -> dict[str, Any]:
    normalized_project = abs_project_path(project_path)
    try:
        normalized = _normalize_floquet(
            ports, polarization_basis, sort_code, sort_frequency,
            sort_theta, sort_phi, max_order_x, max_order_yprime,
        )
    except (TypeError, ValueError) as exc:
        return error_response("invalid_floquet_configuration", str(exc), phase="validation", project_path=normalized_project)
    normalized_ports, basis, sort, frequency, theta, phi, max_x, max_y = normalized
    return _submit_versioned_vba(
        normalized_project,
        "Define Floquet Ports",
        floquet_port_setup_vba,
        ports=normalized_ports,
        polarization_basis=basis,
        sort_code=sort,
        sort_frequency=frequency,
        sort_theta=theta,
        sort_phi=phi,
        max_order_x=max_x,
        max_order_yprime=max_y,
    )


def _vector(value: Sequence[Any], name: str) -> tuple[float, float, float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 3:
        raise ValueError(f"{name} 必须是包含三个有限数值的向量")
    result = tuple(_finite(item, f"{name}[{index}]") for index, item in enumerate(value))
    if math.sqrt(sum(item * item for item in result)) <= 1e-15:
        raise ValueError(f"{name} 不得为零向量")
    return result  # type: ignore[return-value]


def _normalize_plane_wave(
    normal: Sequence[Any],
    e_vector: Sequence[Any],
    polarization: str,
    reference_frequency: Any,
    handedness: Any,
    phase_difference: Any,
    axial_ratio: Any,
) -> tuple[tuple[float, float, float], tuple[float, float, float], str, float | None, str | None, float | None, float | None]:
    n = _vector(normal, "normal")
    e = _vector(e_vector, "e_vector")
    cross = (
        n[1] * e[2] - n[2] * e[1],
        n[2] * e[0] - n[0] * e[2],
        n[0] * e[1] - n[1] * e[0],
    )
    if math.sqrt(sum(item * item for item in cross)) <= 1e-12 * math.sqrt(sum(item * item for item in n)) * math.sqrt(sum(item * item for item in e)):
        raise ValueError("E 场向量不得与传播法向量平行")
    normalized_pol = str(polarization).strip().casefold()
    pol_names = {"linear": "Linear", "circular": "Circular", "elliptical": "Elliptical"}
    if normalized_pol not in pol_names:
        raise ValueError("polarization 仅允许 Linear、Circular 或 Elliptical")
    pol = pol_names[normalized_pol]
    frequency = None
    normalized_hand = None
    phase = None
    ratio = None
    if pol in {"Circular", "Elliptical"}:
        frequency = _finite(reference_frequency, "reference_frequency")
        if frequency <= 0:
            raise ValueError("reference_frequency 必须大于零")
    if pol in {"Circular", "Elliptical"} and handedness is not None:
        hand_key = str(handedness).strip().casefold()
        if hand_key not in {"left", "right"}:
            raise ValueError("handedness 仅允许 Left 或 Right")
        normalized_hand = hand_key.title()
    elif pol in {"Circular", "Elliptical"}:
        raise ValueError(f"{pol} 极化必须提供 handedness")
    if pol == "Elliptical":
        phase = _finite(phase_difference, "phase_difference")
        ratio = _finite(axial_ratio, "axial_ratio")
        if ratio <= 0:
            raise ValueError("axial_ratio 必须大于零")
    return n, e, pol, frequency, normalized_hand, phase, ratio


def inspect_plane_wave(project_path: str) -> dict[str, Any]:
    project, status, normalized = _attach(project_path)
    if project is None:
        return status
    lines = [
        "Dim cstRtNx As Double, cstRtNy As Double, cstRtNz As Double",
        "Dim cstRtEx As Double, cstRtEy As Double, cstRtEz As Double",
        "PlaneWave.GetNormal cstRtNx, cstRtNy, cstRtNz",
        "PlaneWave.GetEVector cstRtEx, cstRtEy, cstRtEz",
        'Print #cstRtQueryFile, "NORMAL" & Chr(9) & CStr(cstRtNx) & Chr(9) & CStr(cstRtNy) & Chr(9) & CStr(cstRtNz)',
        'Print #cstRtQueryFile, "EVECTOR" & Chr(9) & CStr(cstRtEx) & Chr(9) & CStr(cstRtEy) & Chr(9) & CStr(cstRtEz)',
        'Print #cstRtQueryFile, "VALUE" & Chr(9) & "polarization" & Chr(9) & PlaneWave.GetPolarizationType',
        'Print #cstRtQueryFile, "VALUE" & Chr(9) & "reference_frequency" & Chr(9) & CStr(PlaneWave.GetReferenceFrequency)',
        'Print #cstRtQueryFile, "VALUE" & Chr(9) & "circular_direction" & Chr(9) & PlaneWave.GetCircularDirection',
        'Print #cstRtQueryFile, "VALUE" & Chr(9) & "phase_difference" & Chr(9) & CStr(PlaneWave.GetPhaseDifference)',
        'Print #cstRtQueryFile, "VALUE" & Chr(9) & "axial_ratio" & Chr(9) & CStr(PlaneWave.GetAxialRatio)',
    ]
    try:
        rows = execute_text_query(project, lines)
        values: dict[str, Any] = {}
        for row in rows:
            parts = row.split("\t")
            if len(parts) >= 4 and parts[0] in {"NORMAL", "EVECTOR"}:
                values["normal" if parts[0] == "NORMAL" else "e_vector"] = [float(item) for item in parts[1:4]]
            elif len(parts) >= 3 and parts[0] == "VALUE":
                values[parts[1]] = parts[2]
        required = {"normal", "e_vector", "polarization", "reference_frequency", "circular_direction", "phase_difference", "axial_ratio"}
        if not required.issubset(values):
            raise ValueError("PlaneWave 查询结果不完整")
        for name in ("reference_frequency", "phase_difference", "axial_ratio"):
            values[name] = float(values[name])
        return success_response(project_path=normalized, plane_wave=values)
    except Exception as exc:
        return _query_failure(exc, normalized)


def define_plane_wave(
    project_path: str,
    *,
    normal: Sequence[Any],
    e_vector: Sequence[Any],
    polarization: str = "Linear",
    reference_frequency: Any = None,
    handedness: Any = None,
    phase_difference: Any = None,
    axial_ratio: Any = None,
) -> dict[str, Any]:
    normalized_project = abs_project_path(project_path)
    try:
        normalized = _normalize_plane_wave(normal, e_vector, polarization, reference_frequency, handedness, phase_difference, axial_ratio)
    except (TypeError, ValueError) as exc:
        return error_response("invalid_plane_wave", str(exc), phase="validation", project_path=normalized_project)
    n, e, pol, frequency, hand, phase, ratio = normalized
    return _submit_versioned_vba(
        normalized_project,
        "Define Plane Wave",
        plane_wave_vba,
        normal=n,
        e_vector=e,
        polarization=pol,
        reference_frequency=frequency,
        handedness=hand,
        phase_difference=phase,
        axial_ratio=ratio,
    )


def _normalize_excitation(excitation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(excitation, dict):
        raise ValueError("excitation 必须是配置对象")
    strategy = str(excitation.get("strategy", "")).strip().casefold().replace("-", "_")
    aliases = {"all+floquet": "all_with_floquet", "plane wave": "plane_wave"}
    strategy = aliases.get(strategy, strategy)
    if strategy not in {"all", "all_with_floquet", "plane_wave", "single", "list"}:
        raise ValueError("未知的 excitation.strategy")
    normalized: dict[str, Any] = {"strategy": strategy}
    if strategy == "single":
        normalized.update(port=_integer(excitation.get("port"), "port", minimum=1), mode=_integer(excitation.get("mode"), "mode", minimum=1))
    elif strategy == "list":
        items = excitation.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError("显式激励列表不得为空")
        normalized_items: list[dict[str, str]] = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("激励列表项必须是对象")
            port = str(item.get("port", "")).strip()
            mode = str(item.get("mode", "")).strip()
            if not port or not mode:
                raise ValueError("显式激励项的 port 和 mode 不得为空")
            port_key = port.casefold()
            if port_key in {"zmin", "zmax"}:
                port = port_key
            else:
                try:
                    port_number = int(port)
                except ValueError as exc:
                    raise ValueError("显式激励项的 port 仅允许正整数或 zmin/zmax") from exc
                if port_number < 1 or str(port_number) != port:
                    raise ValueError("显式激励项的 port 仅允许正整数或 zmin/zmax")
                port = str(port_number)
            normalized_items.append({"port": port, "mode": mode})
        keys = [(item["port"], item["mode"]) for item in normalized_items]
        if len(keys) != len(set(keys)):
            raise ValueError("显式激励列表不得重复")
        normalized["items"] = normalized_items
    return normalized


def configure_frequency_domain_solver(
    project_path: str,
    *,
    mesh_method: str,
    excitation: dict[str, Any],
) -> dict[str, Any]:
    normalized_project = abs_project_path(project_path)
    mesh_names = {"hexahedral": "Hexahedral", "tetrahedral": "Tetrahedral", "surface": "Surface"}
    try:
        mesh = mesh_names[str(mesh_method).strip().casefold()]
        normalized_excitation = _normalize_excitation(excitation)
    except (KeyError, TypeError, ValueError) as exc:
        message = "mesh_method 仅允许 Hexahedral、Tetrahedral 或 Surface" if isinstance(exc, KeyError) else str(exc)
        return error_response("invalid_frequency_domain_solver_configuration", message, phase="validation", project_path=normalized_project)
    result = _submit_versioned_vba(
        normalized_project,
        "Configure Frequency Domain Solver",
        frequency_domain_solver_vba,
        mesh_method=mesh,
        excitation=normalized_excitation,
    )
    if result.get("status") != "error":
        result.update(
            solver_type="HF Frequency Domain",
            mesh_method=mesh,
            excitation=normalized_excitation,
            untouched_settings="保持工程当前值；新工程由 CST 默认值决定",
        )
    return result


def list_monitors(project_path: str) -> dict[str, Any]:
    """通过 Monitor 对象公开 getter 列出实际定义的监视器。"""
    project, status, normalized = _attach(project_path)
    if project is None:
        return status
    lines = [
        "Dim cstRtMonitorIndex As Long",
        "For cstRtMonitorIndex = 0 To Monitor.GetNumberOfMonitors - 1",
        '    Print #cstRtQueryFile, "MONITOR" & Chr(9) & Monitor.GetMonitorNameFromIndex(cstRtMonitorIndex) & Chr(9) & Monitor.GetMonitorTypeFromIndex(cstRtMonitorIndex) & Chr(9) & Monitor.GetMonitorDomainFromIndex(cstRtMonitorIndex) & Chr(9) & CStr(Monitor.GetMonitorFrequencyFromIndex(cstRtMonitorIndex))',
        "Next cstRtMonitorIndex",
    ]
    try:
        monitors: list[dict[str, Any]] = []
        for row in execute_text_query(project, lines):
            parts = row.split("\t")
            if len(parts) >= 5 and parts[0] == "MONITOR":
                monitors.append({"name": parts[1], "type": parts[2], "domain": parts[3], "frequency": float(parts[4])})
        return success_response(project_path=normalized, monitors=monitors, count=len(monitors))
    except Exception as exc:
        return _query_failure(exc, normalized)


__all__ = [
    "configure_frequency_domain_solver",
    "define_floquet_port",
    "define_plane_wave",
    "define_unit_cell_boundary",
    "inspect_boundary",
    "inspect_floquet_ports",
    "inspect_plane_wave",
    "list_monitors",
]
