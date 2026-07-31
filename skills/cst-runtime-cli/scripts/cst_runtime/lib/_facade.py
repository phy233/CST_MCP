"""lib 门面实现共享工具，仅供 lib 子模块使用。"""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from .contracts import (
    CSTOperationError,
    OperationResult,
    as_result,
    error_result,
    internal_error,
    invalid_arguments,
)


def call_core(
    function: Callable[..., Any],
    *args: Any,
    field: str = "result",
    **kwargs: Any,
) -> OperationResult:
    """调用 core，并把所有公开结果归一化为 OperationResult。"""
    try:
        return as_result(function(*args, **kwargs), field=field)
    except (TypeError, ValueError) as exc:
        return invalid_arguments(str(exc))
    except Exception as exc:
        return internal_error(exc)


def wrap_core(function: Callable[..., Any], *, field: str = "result") -> Callable[..., OperationResult]:
    """创建保留名称和文档的稳定 lib 调用包装器。"""
    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> OperationResult:
        return call_core(function, *args, field=field, **kwargs)

    return wrapped


def wrap_public(function: Callable[..., Any], *, field: str = "result") -> Callable[..., OperationResult]:
    """把已有 lib 函数迁移到统一契约，同时保留原签名语义。"""
    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> OperationResult:
        try:
            value = function(*args, **kwargs)
            if value is None:
                return OperationResult({"status": "success"})
            return as_result(value, field=field)
        except (TypeError, ValueError, KeyError) as exc:
            return invalid_arguments(str(exc))
        except CSTOperationError as exc:
            return as_result(exc.result)
        except RuntimeError as exc:
            return error_result("operation_failed", str(exc))
        except Exception as exc:
            return internal_error(exc)

    return wrapped
