"""Reliable VBA History submission using a filesystem status side channel."""
from __future__ import annotations

import hashlib
import locale
import re
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
from .compatibility import compatibility_metadata
from .compatibility.execution import resolve_cst_temp_context


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


_LITERAL_REPORT_ERROR = re.compile(
    r'^(?P<indent>[ \t]*)ReportError\s+(?P<message>"(?:""|[^"])*")\s*$',
    re.IGNORECASE,
)


def _route_literal_report_errors(
    vba_script: str,
    *,
    variable_prefix: str,
    error_label: str,
) -> str:
    """把内部字面量 ``ReportError`` 路由到确定的状态网关错误分支。"""
    routed_lines: list[str] = []
    for line in vba_script.splitlines():
        match = _LITERAL_REPORT_ERROR.fullmatch(line)
        if match is None:
            routed_lines.append(line)
            continue
        indent = match.group("indent")
        message = match.group("message")
        routed_lines.extend(
            [
                f"{indent}{variable_prefix}ExplicitFailure = True",
                f"{indent}{variable_prefix}ErrorNumber = 9999",
                f"{indent}{variable_prefix}ErrorDescription = {message}",
                f"{indent}GoTo {error_label}",
            ]
        )
    return "\n".join(routed_lines)


def resolve_cst_temp_directory(
    project: Any,
    project_path: str,
    *,
    timeout: float = 2.0,
) -> Path:
    """通过即时 VBA 验证并取得 CST 工程 Temp 路径。"""
    directory, _expression = resolve_cst_temp_context(project, project_path, timeout=timeout)
    return directory


def wrap_vba_with_status_channel(
    vba_script: str,
    status_file_name: str,
    arm_file_name: str,
    operation_id: str,
    *,
    status_directory_expression: str | None = None,
) -> str:
    """包装 History VBA，同时避免持久化当前机器的绝对路径。

    arm 文件只在首次提交时存在。以后重建 History 时仍会执行实际业务 VBA，
    但不会再次创建诊断文件。内部的字面量 ``ReportError`` 会先路由到明确的
    错误标签，写完状态文件后再向 CST 报错。包装代码只使用 CST 2022 文档
    确认支持的 ``ReportError``、``Err.Number/Description`` 和 ``GoTo``，
    不使用旧解释器不支持的 ``Err.Raise``。
    """
    valid_filename_characters = frozenset(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    )
    if not status_directory_expression:
        raise ValueError("必须传入已经由即时 VBA 验证的 Temp 路径表达式")
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
    routed_script = _route_literal_report_errors(
        vba_script,
        variable_prefix=variable_prefix,
        error_label=error_label,
    )
    return "\n".join(
        [
            f"Dim {variable_prefix}StatusFile As String",
            f"Dim {variable_prefix}ArmFile As String",
            f"Dim {variable_prefix}Armed As Boolean",
            f"Dim {variable_prefix}FileNumber As Integer",
            f"Dim {variable_prefix}ErrorNumber As Long",
            f"Dim {variable_prefix}ErrorDescription As String",
            f"Dim {variable_prefix}ExplicitFailure As Boolean",
            f'{variable_prefix}StatusFile = {status_directory_expression} & "\\{status_file_name}"',
            f'{variable_prefix}ArmFile = {status_directory_expression} & "\\{arm_file_name}"',
            "On Error Resume Next",
            f'{variable_prefix}Armed = (Dir$({variable_prefix}ArmFile) <> "")',
            f"If {variable_prefix}Armed Then Kill {variable_prefix}ArmFile",
            "On Error GoTo 0",
            f"On Error GoTo {error_label}",
            routed_script,
            f"If {variable_prefix}Armed Then",
            f"{variable_prefix}FileNumber = FreeFile",
            f"Open {variable_prefix}StatusFile For Output As #{variable_prefix}FileNumber",
            f'Print #{variable_prefix}FileNumber, "OK"',
            f"Close #{variable_prefix}FileNumber",
            "End If",
            f"GoTo {done_label}",
            f"{error_label}:",
            f"If Not {variable_prefix}ExplicitFailure Then",
            f"{variable_prefix}ErrorNumber = Err.Number",
            f"{variable_prefix}ErrorDescription = Err.Description",
            "End If",
            f'If {variable_prefix}ErrorDescription = "" Then',
            f'{variable_prefix}ErrorDescription = '
            f'"CST History VBA failed without Err.Description (error " & '
            f'CStr({variable_prefix}ErrorNumber) & ")."',
            "End If",
            "On Error Resume Next",
            f"If {variable_prefix}Armed Then",
            f"{variable_prefix}FileNumber = FreeFile",
            f"Open {variable_prefix}StatusFile For Output As #{variable_prefix}FileNumber",
            f'Print #{variable_prefix}FileNumber, "ERROR"',
            f"Print #{variable_prefix}FileNumber, CStr({variable_prefix}ErrorNumber)",
            f'Print #{variable_prefix}FileNumber, ""',
            f"Print #{variable_prefix}FileNumber, {variable_prefix}ErrorDescription",
            f'Print #{variable_prefix}FileNumber, "0"',
            f"Close #{variable_prefix}FileNumber",
            "End If",
            "On Error GoTo 0",
            f"ReportError {variable_prefix}ErrorDescription",
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
    """提交一个 History 块，并记录前后快照、操作流水和 VBA 状态。"""
    from ..context import get_current_execution_context
    from .compatibility.history import get_raw_history, supports_get_history
    from ..history.models import HistoryOperationRecord, HistorySnapshot
    from ..history.journal import append_operation, save_snapshot

    resolved_operation_id = operation_id or uuid.uuid4().hex
    original_script = "\n".join(vba_lines)
    digest = hashlib.sha256(original_script.encode("utf-8")).hexdigest()
    safe_operation_id = "".join(
        character for character in resolved_operation_id if character.isalnum()
    ) or uuid.uuid4().hex
    status_file_name = f"cst-runtime-{safe_operation_id}.status"
    arm_file_name = f"cst-runtime-{safe_operation_id}.arm"

    ctx = get_current_execution_context()
    history_supported = supports_get_history(project)
    recording_issues: list[dict[str, str]] = []

    def _record_issue(stage: str, exc: Exception | str) -> None:
        recording_issues.append({"stage": stage, "message": str(exc)})

    def _capture_snapshot(reason: str) -> tuple[str | None, str | None]:
        if not history_supported:
            _record_issue(reason, "当前 CST 工程不支持 _GetHistory")
            return None, None
        try:
            snapshot = HistorySnapshot.from_raw_cst(
                get_raw_history(project),
                project_path=project_path,
                reason=reason,
                operation_id=resolved_operation_id,
            )
            save_snapshot(snapshot, project_path=project_path)
            return snapshot.snapshot_sha256, snapshot.snapshot_id
        except Exception as exc:
            _record_issue(reason, exc)
            return None, None

    before_sha, before_snap_id = _capture_snapshot("before_submission")
    record = HistoryOperationRecord(
        operation_id=resolved_operation_id,
        history_label=history_label,
        business_vba=original_script,
        business_vba_sha256=digest,
        project_path=project_path,
        interaction_id=ctx.get("interaction_id"),
        task_id=ctx.get("task_id"),
        run_id=ctx.get("run_id"),
        before_snapshot_id=before_snap_id,
        before_snapshot_sha256=before_sha,
        execution_state="pending",
        recording_status="incomplete" if recording_issues else "complete",
    )

    def _append_record(stage: str) -> None:
        record.recording_status = "incomplete" if recording_issues else "complete"
        if recording_issues:
            record.extra["recording_issues"] = list(recording_issues)
        try:
            append_operation(record, project_path=project_path)
        except Exception as exc:
            _record_issue(stage, exc)
            record.recording_status = "incomplete"
            record.extra["recording_issues"] = list(recording_issues)

    _append_record("pending_journal")
    context = {
        "project_path": project_path,
        "history_label": history_label,
        "operation_id": resolved_operation_id,
        "vba_sha256": digest,
    }
    resolved_status_path: Path | None = None
    arm_path: Path | None = None
    owns_side_channel = False
    wrapped_script = original_script
    status_directory_expression = ""

    def _enrich_response(
        response: dict[str, Any],
        after_sha: str | None,
        after_snap_id: str | None,
    ) -> dict[str, Any]:
        response.update(
            {
                "operation_id": resolved_operation_id,
                "before_snapshot_id": before_snap_id,
                "before_snapshot_sha256": before_sha,
                "after_snapshot_id": after_snap_id,
                "after_snapshot_sha256": after_sha,
                "recording_status": record.recording_status,
                "recording_issues": list(recording_issues),
            }
        )
        return response

    try:
        if _status_directory is None:
            status_directory, status_directory_expression = resolve_cst_temp_context(
                project,
                project_path,
            )
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
        record.wrapped_vba = wrapped_script
        record.execution_state = "submitted"
        _append_record("submitted_journal")

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
                    raise runtime_exc
                except VBACompileOrHostError:
                    pass
            raise CSTSubmissionError(
                str(exc) or "CST History submission failed.",
                feature=feature,
                next_action="Verify the active CST project and COM connection before retrying.",
                context=context,
            ) from exc

        if submission_result is False:
            if resolved_status_path.exists():
                try:
                    wait_for_vba_status(
                        resolved_status_path,
                        timeout=min(max(status_timeout, 0.0), 0.25),
                        poll_interval=poll_interval,
                    )
                except VBACompileOrHostError:
                    pass
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
        after_sha, after_snap_id = _capture_snapshot("after_submission")
        record.execution_state = "succeeded"
        record.after_snapshot_id = after_snap_id
        record.after_snapshot_sha256 = after_sha
        _append_record("succeeded_journal")
        return _enrich_response(
            success_response(
                submission="accepted",
                execution="reported_ok",
                project_path=project_path,
                history_label=history_label,
                operation_id=resolved_operation_id,
                vba_sha256=digest,
                compatibility=compatibility_metadata(project),
            ),
            after_sha,
            after_snap_id,
        )
    except (VBARuntimeError, VBACompileOrHostError, CSTSubmissionError) as exc:
        diagnostic_context = dict(context)
        if (
            isinstance(exc, VBACompileOrHostError)
            and exc.context.get("status_state") in {"missing", "malformed", "timeout"}
        ):
            diagnostic_context["vba_script"] = original_script
            diagnostic_context["gateway_vba_script"] = wrapped_script
            diagnostic_context["status_directory_expression"] = status_directory_expression
        after_sha, after_snap_id = _capture_snapshot("after_failure")
        err_resp = exc.to_response(**diagnostic_context)
        record.execution_state = "failed"
        record.after_snapshot_id = after_snap_id
        record.after_snapshot_sha256 = after_sha
        record.error = err_resp
        record.cst_error_envelope = err_resp
        _append_record("failed_journal")
        return _enrich_response(err_resp, after_sha, after_snap_id)
    except Exception as exc:
        after_sha, after_snap_id = _capture_snapshot("after_failure")
        err_resp = CSTSubmissionError(
            str(exc) or "CST History submission failed.",
            feature=feature,
            next_action="Verify the active CST project and COM connection before retrying.",
            context=context,
        ).to_response()
        record.execution_state = "failed"
        record.after_snapshot_id = after_snap_id
        record.after_snapshot_sha256 = after_sha
        record.error = err_resp
        record.cst_error_envelope = err_resp
        _append_record("failed_journal")
        return _enrich_response(err_resp, after_sha, after_snap_id)
    finally:
        if owns_side_channel and arm_path is not None and resolved_status_path is not None:
            for owned_path in (arm_path, resolved_status_path):
                try:
                    owned_path.unlink(missing_ok=True)
                except OSError:
                    pass
