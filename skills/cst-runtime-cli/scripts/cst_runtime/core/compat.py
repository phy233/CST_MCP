"""旧兼容导入路径。

新实现统一位于 :mod:`cst_runtime.core.compatibility`；本模块只保留重导出，
避免已有内部调用或第三方脚本立即失效。
"""
from __future__ import annotations

from .compatibility import (
    CompatibilityProfile,
    connect_to_any_design_environment,
    detect_compatibility_profile,
    list_open_project_paths,
    running_design_environment_pids,
)


def detect_version() -> tuple[int, int]:
    profile = detect_compatibility_profile()
    return profile.major, 0


def is_2022_or_later() -> bool:
    return detect_compatibility_profile().major >= 2022


def is_2026_or_later() -> bool:
    return detect_compatibility_profile().major >= 2026


safe_connect_to_any = connect_to_any_design_environment
safe_running_design_environments = running_design_environment_pids
safe_list_open_projects = list_open_project_paths


class _NoOpContextManager:
    def __enter__(self) -> "_NoOpContextManager":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class _QuietModeContextManager:
    """临时开启静默模式，并在退出时恢复进入前的状态。"""

    def __init__(self, environment: object) -> None:
        self._environment = environment
        self._previous: bool | None = None
        self._changed = False

    def __enter__(self) -> "_QuietModeContextManager":
        getter = getattr(self._environment, "in_quiet_mode", None)
        setter = getattr(self._environment, "set_quiet_mode", None)
        if not callable(getter) or not callable(setter):
            return self
        try:
            self._previous = bool(getter())
            if not self._previous:
                setter(True)
                self._changed = True
        except Exception:
            self._previous = None
            self._changed = False
        return self

    def __exit__(self, *_args: object) -> None:
        setter = getattr(self._environment, "set_quiet_mode", None)
        if self._changed and self._previous is not None and callable(setter):
            try:
                setter(self._previous)
            except Exception:
                pass
        return None


def safe_quiet_mode(environment: object) -> object:
    getter = getattr(environment, "in_quiet_mode", None)
    setter = getattr(environment, "set_quiet_mode", None)
    if callable(getter) and callable(setter):
        return _QuietModeContextManager(environment)
    return _NoOpContextManager()


def safe_get_version(environment: object) -> str:
    value = getattr(environment, "version", None)
    try:
        value = value() if callable(value) else value
        return str(value) if value is not None else "unknown"
    except Exception:
        return "unknown"


__all__ = [
    "CompatibilityProfile",
    "detect_version",
    "is_2022_or_later",
    "is_2026_or_later",
    "safe_connect_to_any",
    "safe_get_version",
    "safe_list_open_projects",
    "safe_quiet_mode",
    "safe_running_design_environments",
]
