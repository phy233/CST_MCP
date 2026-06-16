"""CST 2022/2026 version compatibility layer.

Provides safe wrappers for CST API calls that differ between versions.
CST 2022 uses older API methods that may not exist in CST 2026, and vice versa.
"""
from __future__ import annotations

import warnings
from typing import Any

_CST_MAJOR: int = 0
_CST_MINOR: int = 0
_detected: bool = False


def detect_version() -> tuple[int, int]:
    """Detect connected CST version.

    Returns:
        Tuple of (major, minor) version numbers.
        Returns (0, 0) if CST is not available.
    """
    global _CST_MAJOR, _CST_MINOR, _detected
    if _detected:
        return _CST_MAJOR, _CST_MINOR

    try:
        import cst.interface
        de = cst.interface.DesignEnvironment()
        ver = getattr(de, "version", "0.0.0")
        if isinstance(ver, str):
            parts = ver.split(".")
            _CST_MAJOR = int(parts[0]) if parts else 0
            _CST_MINOR = int(parts[1]) if len(parts) > 1 else 0
        else:
            _CST_MAJOR = int(ver) if ver else 0
    except Exception:
        pass

    _detected = True
    return _CST_MAJOR, _CST_MINOR


def is_2022_or_later() -> bool:
    """Check if CST version is 2022 or later."""
    major, _ = detect_version()
    return major >= 2022


def is_2026_or_later() -> bool:
    """Check if CST version is 2026 or later."""
    major, minor = detect_version()
    return major >= 2026


def safe_connect_to_any():
    """Connect to CST DesignEnvironment with version compatibility.

    Tries multiple connection methods:
    1. connect_to_any() - CST 2026
    2. connect_to_any_or_new() - CST 2025
    3. DesignEnvironment() constructor - CST 2022 fallback

    Returns:
        DesignEnvironment instance

    Raises:
        RuntimeError: If all connection methods fail
    """
    import cst.interface
    de_cls = cst.interface.DesignEnvironment

    # Try CST 2026 method
    if hasattr(de_cls, "connect_to_any"):
        try:
            return de_cls.connect_to_any()
        except Exception as e:
            warnings.warn(f"connect_to_any() failed: {e}")

    # Try CST 2025 method
    if hasattr(de_cls, "connect_to_any_or_new"):
        try:
            return de_cls.connect_to_any_or_new()
        except Exception as e:
            warnings.warn(f"connect_to_any_or_new() failed: {e}")

    # CST 2022 fallback: direct constructor
    try:
        return de_cls()
    except Exception as e:
        raise RuntimeError(f"Failed to connect to CST DesignEnvironment: {e}")


def safe_running_design_environments() -> list[int]:
    """Get list of running CST Design Environment process IDs.

    Returns:
        List of process IDs. Empty list if function not available.
    """
    try:
        import cst.interface
        if hasattr(cst.interface, "running_design_environments"):
            return cst.interface.running_design_environments()
    except Exception:
        pass
    return []


def safe_list_open_projects(de) -> list[str]:
    """List open projects with version compatibility.

    Args:
        de: DesignEnvironment instance

    Returns:
        List of open project paths. Empty list if function not available.
    """
    try:
        if hasattr(de, "list_open_projects"):
            return de.list_open_projects()
    except Exception:
        pass
    return []


def safe_quiet_mode(de):
    """Enter quiet mode with version compatibility.

    Args:
        de: DesignEnvironment instance

    Returns:
        Context manager for quiet mode.
        Returns no-op context manager if not supported.
    """
    try:
        if hasattr(de, "quiet_mode_enabled"):
            return de.quiet_mode_enabled()
    except Exception:
        pass

    # No-op context manager fallback
    class _NoOpContextManager:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    return _NoOpContextManager()


def safe_get_version(de) -> str:
    """Get CST version string with compatibility.

    Args:
        de: DesignEnvironment instance

    Returns:
        Version string (e.g., "2026.0.0") or "unknown"
    """
    try:
        ver = getattr(de, "version", None)
        if ver is not None:
            return str(ver)
    except Exception:
        pass
    return "unknown"
