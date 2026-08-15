"""真实 CST 集成测试的共享纯函数工具（不连接 CST，仅数据结构处理）。"""
from __future__ import annotations

import os
import struct
from pathlib import Path
from typing import Any

COMPONENT = "component1"


def entity_keys(items: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {
        (str(item.get("component", "")), str(item.get("name", "")))
        for item in items
    }


def project_arguments(cst_case: Any, **arguments: Any) -> dict[str, Any]:
    return {"project_path": cst_case.project_path, **arguments}


def assert_error_response(
    result: dict[str, Any],
    *,
    error_types: set[str],
    phase: str,
) -> None:
    """同时检查旧顶层字段和统一错误信封，避免把任意失败当成预期失败。"""
    assert result.get("status") == "error", result
    assert result.get("ok") is False, result
    assert result.get("error_type") in error_types, result
    error = result.get("error")
    assert isinstance(error, dict), result
    assert error.get("type") == result.get("error_type"), result
    assert error.get("phase") == phase, result


def assert_png_1920x1080(path: Path) -> None:
    """检查 PNG 文件签名和 IHDR 尺寸，不让任意非空文件冒充截图。"""
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n", path
    assert header[12:16] == b"IHDR", path
    assert struct.unpack(">II", header[16:24]) == (1920, 1080), path


def prepare_interactive_result_read(cst_case: Any) -> None:
    """保存隔离工程，使 CST 2022 交互结果接口读取到明确的最近保存状态。"""
    saved = cst_case.require_success(
        "save-project",
        {"project_path": cst_case.project_path},
    )
    assert Path(saved["project_path"]).resolve() == Path(cst_case.project_path).resolve()
    cst_case.shared.require_visible_window()


def normalized(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))
