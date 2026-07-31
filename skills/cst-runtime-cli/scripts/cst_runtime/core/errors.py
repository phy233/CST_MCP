"""Runtime exception types backed by the shared response contract."""
from __future__ import annotations

from typing import Any, Mapping

from ..contracts import (
    error_response,
    normalize_response,
    phase_for_error,
    success_response,
)


class CSTRuntimeError(RuntimeError):
    """Base exception that can cross process boundaries as a stable envelope."""

    error_type = "runtime_error"
    phase = "runtime"

    def __init__(
        self,
        message: str,
        *,
        code: int | str | None = None,
        source: str | None = None,
        line: int | None = None,
        feature: str | None = None,
        rollback: Mapping[str, Any] | None = None,
        next_action: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.source = source
        self.line = line
        self.feature = feature
        self.rollback = dict(rollback) if rollback is not None else None
        self.next_action = next_action
        self.context = dict(context or {})

    def to_response(self, **context: Any) -> dict[str, Any]:
        merged_context = {**self.context, **context}
        return error_response(
            self.error_type,
            str(self),
            phase=self.phase,
            code=self.code,
            source=self.source,
            line=self.line,
            feature=self.feature,
            rollback=self.rollback,
            next_action=self.next_action,
            context=merged_context,
        )


class ValidationError(CSTRuntimeError):
    error_type = "validation_error"
    phase = "validation"


class UnsupportedFeatureError(CSTRuntimeError):
    """Raised when the active CST API does not provide a required capability."""

    error_type = "unsupported_feature"
    phase = "validation"


class CSTSubmissionError(CSTRuntimeError):
    error_type = "cst_submission_error"
    phase = "submission"


class VBARuntimeError(CSTRuntimeError):
    error_type = "vba_runtime_error"
    phase = "execution"


class VBACompileOrHostError(CSTRuntimeError):
    error_type = "vba_compile_or_host_error"
    phase = "execution"


class VerificationError(CSTRuntimeError):
    error_type = "verification_failed"
    phase = "verification"


class RollbackError(CSTRuntimeError):
    error_type = "rollback_failed"
    phase = "rollback"


class WorkerError(CSTRuntimeError):
    error_type = "worker_error"
    phase = "worker"


__all__ = [
    "CSTRuntimeError",
    "CSTSubmissionError",
    "RollbackError",
    "UnsupportedFeatureError",
    "ValidationError",
    "VBACompileOrHostError",
    "VBARuntimeError",
    "VerificationError",
    "WorkerError",
    "error_response",
    "normalize_response",
    "phase_for_error",
    "success_response",
]
