"""跨版本即时 VBA 执行与文本查询通道。"""
from __future__ import annotations

import locale
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Iterable

from ..errors import CSTSubmissionError


def vba_string(value: str) -> str:
    return value.replace('"', '""')


def _decode_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", locale.getpreferredencoding(False), "mbcs", "cp1252"):
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def _schematic(project: Any) -> Any:
    schematic = getattr(project, "schematic", None)
    executor = getattr(schematic, "execute_vba_code", None)
    if not callable(executor):
        raise CSTSubmissionError(
            "当前 CST 工程不支持即时 VBA 执行通道。",
            feature="compatibility.immediate_vba",
            next_action="请确认工程已打开，且 Python API 提供 schematic.execute_vba_code。",
        )
    return schematic


def execute_immediate_vba(project: Any, lines: Iterable[str]) -> None:
    """执行不需要返回值的即时 VBA，并统一转换提交错误。"""
    macro = "\n".join(["Public Sub Main()", *lines, "End Sub"])
    try:
        result = _schematic(project).execute_vba_code(macro)
        if result is False:
            raise RuntimeError("CST 拒绝执行即时 VBA")
    except CSTSubmissionError:
        raise
    except Exception as exc:
        raise CSTSubmissionError(
            f"即时 VBA 执行失败：{exc}",
            feature="compatibility.immediate_vba",
            next_action="请检查 CST Message Window 中的 VBA 编译或运行错误。",
            context={"vba_script": macro},
        ) from exc


def execute_text_query(
    project: Any,
    lines: Iterable[str],
    *,
    timeout: float = 2.0,
) -> list[str]:
    """通过临时文本文件取得即时 VBA 查询结果。

    ``lines`` 可使用已经打开的文件号变量 ``cstRtQueryFile`` 输出内容。
    """
    output_path = Path(tempfile.gettempdir()) / f"cst-runtime-query-{uuid.uuid4().hex}.txt"
    body = [
        "Dim cstRtQueryFile As Integer",
        "cstRtQueryFile = FreeFile",
        f'Open "{vba_string(str(output_path))}" For Output As #cstRtQueryFile',
        *lines,
        "Close #cstRtQueryFile",
    ]
    try:
        output_path.unlink(missing_ok=True)
        execute_immediate_vba(project, body)
        deadline = time.monotonic() + max(timeout, 0.0)
        while not output_path.is_file() and time.monotonic() < deadline:
            time.sleep(0.01)
        if not output_path.is_file():
            raise CSTSubmissionError(
                "即时 VBA 已提交，但没有生成查询结果文件。",
                feature="compatibility.vba_query",
                next_action="请检查临时目录权限和 CST Message Window。",
            )
        return _decode_text(output_path).splitlines()
    finally:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass


__all__ = ["execute_immediate_vba", "execute_text_query", "vba_string"]
