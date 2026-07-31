"""Protocol-neutral, JSON-safe operation response contracts."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


_ERROR_PHASES = {
    "validation_error": "validation",
    "invalid_arguments": "validation",
    "unsupported_feature": "validation",
    "transport_error": "transport",
    "worker_error": "worker",
    "cst_submission_error": "submission",
    "vba_runtime_error": "execution",
    "vba_compile_or_host_error": "execution",
    "compile_error": "execution",
    "verification_failed": "verification",
    "rollback_failed": "rollback",
    "runtime_error": "runtime",
    "internal_error": "runtime",
}

_CONTEXT_KEYS = frozenset(
    {
        "project_path",
        "history_label",
        "operation_id",
        "runtime_module",
        "cst_version",
        "cst_raw",
        "vba_sha256",
        "vba_script",
    }
)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    return str(value)


def phase_for_error(error_type: str) -> str:
    return _ERROR_PHASES.get(error_type, "runtime")


def error_response(
    error_type: str,
    message: str,
    *,
    phase: str | None = None,
    code: int | str | None = None,
    source: str | None = None,
    line: int | None = None,
    feature: str | None = None,
    rollback: Mapping[str, Any] | None = None,
    next_action: str | None = None,
    context: Mapping[str, Any] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Build the new envelope while retaining legacy top-level fields."""
    resolved_phase = phase or phase_for_error(error_type)
    error: dict[str, Any] = {
        "type": error_type,
        "message": str(message),
        "phase": resolved_phase,
    }
    optional_error_fields = {
        "code": code,
        "source": source,
        "line": line,
        "feature": feature,
        "rollback": rollback,
        "next_action": next_action,
    }
    error.update(
        {
            key: _json_safe(value)
            for key, value in optional_error_fields.items()
            if value is not None
        }
    )

    safe_extra = {key: _json_safe(value) for key, value in extra.items()}
    error_context = {
        key: value for key, value in safe_extra.items() if key in _CONTEXT_KEYS
    }
    if context:
        error_context.update(_json_safe(context))

    payload: dict[str, Any] = {
        "ok": False,
        "status": "error",
        "error_type": error_type,
        "message": str(message),
        "error": error,
        "context": error_context,
        **safe_extra,
    }
    for key, value in optional_error_fields.items():
        if value is not None:
            payload[key] = _json_safe(value)
    return payload


def success_response(
    *,
    submission: str = "not_applicable",
    execution: str = "not_run",
    verification: str = "not_run",
    **payload: Any,
) -> dict[str, Any]:
    return {
        "ok": True,
        "status": "success",
        "submission": submission,
        "execution": execution,
        "verification": verification,
        **_json_safe(payload),
    }


def normalize_response(value: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a legacy result at an API or IPC boundary."""
    payload = dict(value)
    if payload.get("status") == "error" or payload.get("ok") is False:
        nested = payload.get("error")
        nested_error = dict(nested) if isinstance(nested, Mapping) else {}
        error_type = str(
            payload.get("error_type") or nested_error.get("type") or "runtime_error"
        )
        message = str(
            payload.get("message") or nested_error.get("message") or "CST operation failed"
        )
        reserved = {
            "ok",
            "status",
            "error_type",
            "message",
            "error",
            "context",
            "phase",
            "code",
            "source",
            "line",
            "feature",
            "rollback",
            "next_action",
        }
        return error_response(
            error_type,
            message,
            phase=str(nested_error.get("phase") or payload.get("phase") or phase_for_error(error_type)),
            code=nested_error.get("code", payload.get("code")),
            source=nested_error.get("source", payload.get("source")),
            line=nested_error.get("line", payload.get("line")),
            feature=nested_error.get("feature", payload.get("feature")),
            rollback=nested_error.get("rollback", payload.get("rollback")),
            next_action=nested_error.get("next_action", payload.get("next_action")),
            context=payload.get("context") if isinstance(payload.get("context"), Mapping) else None,
            **{key: item for key, item in payload.items() if key not in reserved},
        )
    if payload.get("status") == "success" or payload.get("ok") is True:
        payload.pop("ok", None)
        payload.pop("status", None)
        return success_response(**payload)
    return _json_safe(payload)


__all__ = [
    "error_response",
    "normalize_response",
    "phase_for_error",
    "success_response",
]
