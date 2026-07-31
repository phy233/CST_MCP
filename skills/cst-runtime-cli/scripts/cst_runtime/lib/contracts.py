"""lib 层统一的公开返回契约。"""
from __future__ import annotations

from typing import Any, Mapping


class CSTOperationError(RuntimeError):
    """Python 调用者主动要求 fast-fail 时抛出的业务异常。"""

    def __init__(self, result: Mapping[str, Any]) -> None:
        self.result = dict(result)
        error_type = self.result.get("error_type", "operation_failed")
        message = self.result.get("message", "CST 操作失败")
        super().__init__(f"[{error_type}] {message}")


class OperationResult(dict):
    """兼容 JSON 字典、同时为 Python 提供 fast-fail 的操作结果。"""

    def raise_for_error(self) -> "OperationResult":
        """结果失败时抛出保留完整上下文的异常，否则返回自身。"""
        if self.get("status") == "error":
            raise CSTOperationError(self)
        return self

    def unwrap(self, field: str | None = None) -> Any:
        """先检查错误，再返回结果本身或指定业务字段。"""
        self.raise_for_error()
        if field is None:
            return self
        return self[field]


def as_result(value: Any, *, field: str = "result") -> OperationResult:
    """把 core 返回或普通 Python 值归一化为公开结果。"""
    if isinstance(value, OperationResult):
        return value
    if isinstance(value, Mapping):
        payload = dict(value)
        status = payload.get("status")
        if status not in {"success", "error"}:
            payload["status"] = "success"
        if payload["status"] == "error":
            payload.setdefault("error_type", "operation_failed")
            payload.setdefault("message", "CST 操作失败")
        return OperationResult(payload)
    return OperationResult({"status": "success", field: value})


def success_result(**payload: Any) -> OperationResult:
    """创建成功结果。"""
    return OperationResult({"status": "success", **payload})


def error_result(error_type: str, message: str, **context: Any) -> OperationResult:
    """创建失败结果。"""
    return OperationResult(
        {
            **context,
            "status": "error",
            "error_type": error_type,
            "message": message,
        }
    )


def raise_result_error(result: Mapping[str, Any], default_message: str) -> None:
    """Raise an exception that retains the complete structured core result."""
    payload = dict(result)
    payload.setdefault("message", default_message)
    raise CSTOperationError(payload)


def invalid_arguments(message: str, **context: Any) -> OperationResult:
    """创建统一的参数错误结果。"""
    return error_result("invalid_arguments", message, **context)


def internal_error(exc: Exception, **context: Any) -> OperationResult:
    """在公开边界隐藏内部异常类型，同时保留可操作信息。"""
    return error_result("internal_error", str(exc) or "内部操作失败", **context)
