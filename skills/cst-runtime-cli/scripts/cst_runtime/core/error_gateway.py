"""Reliable VBA History submission using a filesystem status side channel."""
from __future__ import annotations

import hashlib
import locale
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .errors import (
    CSTSubmissionError,
    VBACompileOrHostError,
    VBARuntimeError,
    success_response,
)


@dataclass(frozen=True)
class VBAStatus:
    """Parsed result written by the VBA wrapper."""

    state: str
    code: int | None = None
    source: str = ""
    description: str = ""
    line: int | None = None


def _decode_status_file(path: Path) -> str:
    raw = path.read_bytes()
    encodings = ["utf-8-sig", locale.getpreferredencoding(False), "mbcs", "cp1252"]
    attempted: set[str] = set()
    for encoding in encodings:
        normalized = encoding.lower()
        if normalized in attempted:
            continue
        attempted.add(normalized)
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def parse_vba_status(path: str | Path) -> VBAStatus:
    """Parse an ``OK``/``ERROR`` status file or raise a classified error."""
    status_path = Path(path)
    if not status_path.is_file():
        raise VBACompileOrHostError(
            "VBA status file was not created; the macro may have failed to compile, "
            "the CST host may have rejected it, or the wrapper did not execute.",
            next_action="Inspect the CST Message Window and the submitted VBA script.",
            context={"status_state": "missing"},
        )

    try:
        lines = _decode_status_file(status_path).splitlines()
        while lines and not lines[-1].strip():
            lines.pop()
    except OSError as exc:
        raise VBACompileOrHostError(
            f"VBA status file could not be read: {exc}",
            next_action="Check access to the worker temporary directory.",
            context={"status_state": "unreadable"},
        ) from exc

    if lines == ["OK"]:
        return VBAStatus(state="ok")

    if not lines or lines[0] != "ERROR" or len(lines) < 5:
        raise VBACompileOrHostError(
            "VBA status file is incomplete or malformed; the error handler may have failed.",
            next_action="Inspect the CST Message Window and the submitted VBA script.",
            context={
                "status_state": "malformed",
                "status_content": lines,
            },
        )

    try:
        code = int(lines[1].strip())
        line = int(lines[-1].strip())
    except ValueError as exc:
        raise VBACompileOrHostError(
            "VBA status file contains an invalid error number or line number.",
            next_action="Inspect the CST Message Window and the submitted VBA script.",
            context={
                "status_state": "malformed",
                "status_content": lines,
            },
        ) from exc

    source = lines[2]
    description = "\n".join(lines[3:-1])
    raise VBARuntimeError(
        description or "VBA runtime error",
        code=code,
        source=source or None,
        line=line,
        next_action="Correct the CST object references or VBA command and retry.",
        context={"status_state": "error"},
    )


def wait_for_vba_status(
    path: str | Path,
    *,
    timeout: float = 5.0,
    poll_interval: float = 0.05,
) -> VBAStatus:
    """Wait for a complete status file without waiting forever on compile errors."""
    deadline = time.monotonic() + max(timeout, 0.0)
    last_error: VBACompileOrHostError | None = None
    while True:
        try:
            return parse_vba_status(path)
        except VBARuntimeError:
            raise
        except VBACompileOrHostError as exc:
            last_error = exc
        if time.monotonic() >= deadline:
            assert last_error is not None
            raise VBACompileOrHostError(
                "Timed out waiting for a complete VBA status file; execution may "
                "still be running or the macro may have failed before the wrapper ran.",
                next_action=(
                    "Inspect the CST Message Window, then retry with a new operation ID "
                    "to avoid accepting a late status file."
                ),
                context={
                    "status_state": "timeout",
                    "last_status_state": last_error.context.get("status_state", "unknown"),
                },
            ) from last_error
        time.sleep(min(max(poll_interval, 0.001), max(deadline - time.monotonic(), 0.001)))


def _vba_string(value: str) -> str:
    return value.replace('"', '""')


def resolve_cst_temp_directory(
    project: Any,
    project_path: str,
    *,
    timeout: float = 2.0,
) -> Path:
    """Query CST's own dynamic ``Temp`` path via the reliable immediate VBA API."""
    probe_path = Path(tempfile.gettempdir()) / f"cst-runtime-temp-probe-{uuid.uuid4().hex}.txt"
    macro = "\n".join(
        [
            "Public Sub Main()",
            "Dim cstRtProbeFile As Integer",
            "Dim cstRtTempPath As String",
            'cstRtTempPath = GetProjectPathName("Temp")',
            "cstRtProbeFile = FreeFile",
            f'Open "{_vba_string(str(probe_path))}" For Output As #cstRtProbeFile',
            "Print #cstRtProbeFile, cstRtTempPath",
            "Close #cstRtProbeFile",
            "End Sub",
        ]
    )
    try:
        probe_path.unlink(missing_ok=True)
        project.schematic.execute_vba_code(macro)
        deadline = time.monotonic() + max(timeout, 0.0)
        while not probe_path.is_file() and time.monotonic() < deadline:
            time.sleep(0.01)
        if not probe_path.is_file():
            raise CSTSubmissionError(
                "CST did not report its Temp directory through the immediate VBA probe.",
                next_action="Verify schematic.execute_vba_code support in the active CST session.",
                context={"project_path": project_path},
            )
        reported = _decode_status_file(probe_path).strip()
        resolved = Path(reported).expanduser().resolve()
        if not reported or not resolved.is_dir():
            raise CSTSubmissionError(
                "CST reported an invalid Temp directory.",
                next_action="Check CST project temporary-directory configuration.",
                context={"project_path": project_path, "cst_raw": {"temp_directory": reported}},
            )
        return resolved
    except CSTSubmissionError:
        raise
    except Exception as exc:
        raise CSTSubmissionError(
            f"Failed to query CST Temp directory: {exc}",
            next_action="Verify schematic.execute_vba_code support in the active CST session.",
            context={"project_path": project_path},
        ) from exc
    finally:
        try:
            probe_path.unlink(missing_ok=True)
        except OSError:
            pass


def wrap_vba_with_status_channel(
    vba_script: str,
    status_file_name: str,
    arm_file_name: str,
    operation_id: str,
    *,
    status_directory_expression: str = 'GetProjectPathName("Temp")',
) -> str:
    """Wrap History VBA without persisting a machine-specific absolute path.

    The arm file exists only for the initial submission. A later History rebuild
    still executes the business VBA but does not recreate diagnostic files.
    """
    valid_filename_characters = frozenset(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    )
    if (
        Path(status_file_name).name != status_file_name
        or not status_file_name
        or any(character not in valid_filename_characters for character in status_file_name)
    ):
        raise ValueError("status_file_name must not contain a directory")
    if (
        Path(arm_file_name).name != arm_file_name
        or not arm_file_name
        or any(character not in valid_filename_characters for character in arm_file_name)
    ):
        raise ValueError("arm_file_name must not contain a directory")
    suffix = "".join(character for character in operation_id if character.isalnum())[:12]
    if not suffix:
        suffix = uuid.uuid4().hex[:12]
    error_label = f"CSTRuntimeError{suffix}"
    done_label = f"CSTRuntimeDone{suffix}"
    variable_prefix = f"cstRt{suffix}"
    return "\n".join(
        [
            f"Dim {variable_prefix}StatusFile As String",
            f"Dim {variable_prefix}ArmFile As String",
            f"Dim {variable_prefix}Armed As Boolean",
            f"Dim {variable_prefix}FileNumber As Integer",
            f"Dim {variable_prefix}ErrorNumber As Long",
            f"Dim {variable_prefix}ErrorSource As String",
            f"Dim {variable_prefix}ErrorDescription As String",
            f"Dim {variable_prefix}ErrorLine As Long",
            f'{variable_prefix}StatusFile = {status_directory_expression} & "\\{status_file_name}"',
            f'{variable_prefix}ArmFile = {status_directory_expression} & "\\{arm_file_name}"',
            "On Error Resume Next",
            f'{variable_prefix}Armed = (Dir$({variable_prefix}ArmFile) <> "")',
            f"If {variable_prefix}Armed Then Kill {variable_prefix}ArmFile",
            "On Error GoTo 0",
            f"On Error GoTo {error_label}",
            vba_script,
            f"If {variable_prefix}Armed Then",
            f"{variable_prefix}FileNumber = FreeFile",
            f"Open {variable_prefix}StatusFile For Output As #{variable_prefix}FileNumber",
            f'Print #{variable_prefix}FileNumber, "OK"',
            f"Close #{variable_prefix}FileNumber",
            "End If",
            f"GoTo {done_label}",
            f"{error_label}:",
            f"{variable_prefix}ErrorNumber = Err.Number",
            f"{variable_prefix}ErrorSource = Err.Source",
            f"{variable_prefix}ErrorDescription = Err.Description",
            f"{variable_prefix}ErrorLine = Erl",
            "On Error Resume Next",
            f"If {variable_prefix}Armed Then",
            f"{variable_prefix}FileNumber = FreeFile",
            f"Open {variable_prefix}StatusFile For Output As #{variable_prefix}FileNumber",
            f'Print #{variable_prefix}FileNumber, "ERROR"',
            f"Print #{variable_prefix}FileNumber, CStr({variable_prefix}ErrorNumber)",
            f"Print #{variable_prefix}FileNumber, {variable_prefix}ErrorSource",
            f"Print #{variable_prefix}FileNumber, {variable_prefix}ErrorDescription",
            f"Print #{variable_prefix}FileNumber, CStr({variable_prefix}ErrorLine)",
            f"Close #{variable_prefix}FileNumber",
            "End If",
            "On Error GoTo 0",
            f"Err.Raise {variable_prefix}ErrorNumber, {variable_prefix}ErrorSource, {variable_prefix}ErrorDescription",
            f"{done_label}:",
            "",
        ]
    )


def submit_vba_history(
    project: Any,
    history_label: str,
    vba_lines: Iterable[str],
    *,
    project_path: str,
    feature: str = "modeling.history",
    operation_id: str | None = None,
    status_timeout: float = 5.0,
    poll_interval: float = 0.05,
    _status_directory: str | Path | None = None,
) -> dict[str, Any]:
    """Submit one History block and require an explicit VBA status report."""
    resolved_operation_id = operation_id or uuid.uuid4().hex
    original_script = "\n".join(vba_lines)
    digest = hashlib.sha256(original_script.encode("utf-8")).hexdigest()
    safe_operation_id = "".join(
        character for character in resolved_operation_id if character.isalnum()
    ) or uuid.uuid4().hex
    status_file_name = f"cst-runtime-{safe_operation_id}.status"
    arm_file_name = f"cst-runtime-{safe_operation_id}.arm"
    context = {
        "project_path": project_path,
        "history_label": history_label,
        "operation_id": resolved_operation_id,
        "vba_sha256": digest,
    }
    resolved_status_path: Path | None = None
    arm_path: Path | None = None
    owns_side_channel = False
    try:
        if _status_directory is None:
            status_directory = resolve_cst_temp_directory(project, project_path)
            status_directory_expression = 'GetProjectPathName("Temp")'
        else:
            status_directory = Path(_status_directory).resolve()
            status_directory_expression = f'"{_vba_string(str(status_directory))}"'
        resolved_status_path = status_directory / status_file_name
        arm_path = status_directory / arm_file_name
        if resolved_status_path.exists() or arm_path.exists():
            raise CSTSubmissionError(
                "VBA side-channel file collision; refusing to trust or overwrite stale state.",
                feature=feature,
                next_action="Retry the operation to generate a new operation ID.",
                context=context,
            )
        with arm_path.open("x", encoding="utf-8") as arm_file:
            arm_file.write(resolved_operation_id)
        owns_side_channel = True
        wrapped_script = wrap_vba_with_status_channel(
            original_script,
            status_file_name,
            arm_file_name,
            resolved_operation_id,
            status_directory_expression=status_directory_expression,
        )
        try:
            submission_result = project.modeler.add_to_history(history_label, wrapped_script)
        except Exception as exc:
            if resolved_status_path.exists():
                try:
                    wait_for_vba_status(
                        resolved_status_path,
                        timeout=min(max(status_timeout, 0.0), 0.25),
                        poll_interval=poll_interval,
                    )
                except VBARuntimeError as runtime_exc:
                    return runtime_exc.to_response(**context)
                except VBACompileOrHostError:
                    pass
            raise CSTSubmissionError(
                str(exc) or "CST History submission failed.",
                feature=feature,
                next_action="Verify the active CST project and COM connection before retrying.",
                context=context,
            ) from exc
        if submission_result is False:
            raise CSTSubmissionError(
                "CST rejected the History submission.",
                feature=feature,
                next_action="Verify the active project and CST COM connection before retrying.",
                context=context,
            )
        wait_for_vba_status(
            resolved_status_path,
            timeout=status_timeout,
            poll_interval=poll_interval,
        )
        return success_response(
            submission="accepted",
            execution="reported_ok",
            verification="not_run",
            project_path=project_path,
            history_label=history_label,
            operation_id=resolved_operation_id,
            vba_sha256=digest,
        )
    except (VBARuntimeError, VBACompileOrHostError, CSTSubmissionError) as exc:
        diagnostic_context = dict(context)
        if (
            isinstance(exc, VBACompileOrHostError)
            and exc.context.get("status_state") in {"missing", "malformed", "timeout"}
        ):
            diagnostic_context["vba_script"] = original_script
        return exc.to_response(**diagnostic_context)
    except Exception as exc:
        return CSTSubmissionError(
            str(exc) or "CST History submission failed.",
            feature=feature,
            next_action="Verify the active CST project and COM connection before retrying.",
            context=context,
        ).to_response()
    finally:
        if owns_side_channel and arm_path is not None and resolved_status_path is not None:
            for owned_path in (arm_path, resolved_status_path):
                try:
                    owned_path.unlink(missing_ok=True)
                except OSError:
                    pass
