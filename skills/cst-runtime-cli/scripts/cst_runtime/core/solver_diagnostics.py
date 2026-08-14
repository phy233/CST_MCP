"""solver_diagnostics.py — 从 CST 工程 Result 目录日志中提取求解器原始报错。

求解器错误只通过 CST GUI 的 Message Window 可见，Python/COM 没有官方读取通道；
CST 会把错误写入工程 companion 目录的 Result\\*.log（如 Model.log、MCalc.log）。
本模块提供基线增量读取与 *** Error *** 块提取，作为求解失败诊断的增强通道。
所有读取失败都静默降级为空结果，绝不干扰主流程。
"""
from __future__ import annotations

import locale
import re
from pathlib import Path
from typing import Any

from .identity import _project_companion_dir

# *** Error *** 行（可带时间戳前缀，如 "13/Aug/2026 23:08:30  *** Error ***"）
_ERROR_OPEN = re.compile(r"\*{3}\s*Error\s*\*{3}")
# 错误块的结尾分隔线（----…----，CST 日志中常带前导空格缩进）
_SEPARATOR = re.compile(r"^\s*-{10,}\s*$")
# 新日志条目的时间戳行（23/Aug/2026 12:34:56 开头）
_TIMESTAMP = re.compile(r"^\d{2}/[A-Za-z]{3}/\d{4}\s")
# 非块式错误写法的行级兜底标记（排除 "0 errors occurred" 等良性文本）
_ERROR_LINE_MARKERS = re.compile(
    r"(?i)((?<!\d)[1-9]\d*\s+errors?\s+occurred|not supported|"
    r"\bsolver\b[^\n]{0,80}\bfailed\b|\baborted\b)"
)

_DEFAULT_LOG_GLOB = "*.log"
_MAX_BLOCK_LINES = 40
_TAIL_LINES = 40


def _decode_log_bytes(raw: bytes) -> str:
    """按常见编码链解码日志字节，避免编码异常中断诊断。"""
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        # UTF-16 BOM：优先按 BOM 解码，避免被单字节代码页吞掉成乱码
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError:
            pass
    for encoding in ("utf-8-sig", locale.getpreferredencoding(False), "mbcs", "cp1252"):
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def solver_log_files(project_path: str) -> list[Path]:
    """列出可能包含求解器错误的文本日志文件（companion/Result/*.log）。"""
    result_dir = _project_companion_dir(project_path) / "Result"
    if not result_dir.is_dir():
        return []
    try:
        return sorted(
            path
            for path in result_dir.glob(_DEFAULT_LOG_GLOB)
            if path.is_file()
        )
    except OSError:
        return []


def capture_solver_log_baseline(project_path: str) -> dict[str, int]:
    """记录当前各日志文件的大小，供增量读取做基线。"""
    baseline: dict[str, int] = {}
    for path in solver_log_files(project_path):
        try:
            baseline[str(path)] = path.stat().st_size
        except OSError:
            continue
    return baseline


def _extract_error_blocks(text: str) -> list[str]:
    """提取 *** Error *** 块；没有块时按行级标记兜底。"""
    blocks: list[str] = []
    current: list[str] = []
    in_block = False

    def _close_block() -> None:
        nonlocal current, in_block
        stripped = [line for line in current if line.strip()]
        if stripped:
            blocks.append("\n".join(stripped))
        current = []
        in_block = False

    for line in text.splitlines():
        has_error_open = bool(_ERROR_OPEN.search(line))
        if in_block:
            if has_error_open:
                _close_block()
                current = [line]
                continue
            if _SEPARATOR.match(line):
                _close_block()
                continue
            if _TIMESTAMP.match(line):
                # 新日志条目开始（不含 *** Error *** 开头）
                _close_block()
                current = []
                continue
            current.append(line)
            if len(current) >= _MAX_BLOCK_LINES:
                current.append("...")
                _close_block()
            continue
        if has_error_open:
            in_block = True
            current = [line]

    if in_block:
        _close_block()

    if not blocks:
        for line in text.splitlines():
            if _ERROR_LINE_MARKERS.search(line):
                blocks.append(line.strip())
    return [block for block in blocks if block]


def read_appended_solver_logs(
    project_path: str,
    baseline: dict[str, int] | None = None,
    since: float | None = None,
) -> dict[str, Any]:
    """读取本次求解新增的日志内容并提取错误。

    baseline: {路径字符串: 字节大小}。有 baseline 时只读取追加的字节；
    文件变小（CST 重写/截断）则整文件视为新内容。无 baseline 时只扫描
    mtime >= since 的文件，避免把历史运行的旧错误误报为本次错误。
    """
    baseline = baseline or {}
    since = since or 0.0
    errors: list[str] = []
    error_lines: list[str] = []
    tails: dict[str, list[str]] = {}
    checked: list[str] = []
    for path in solver_log_files(project_path):
        key = str(path)
        try:
            stat = path.stat()
            if not baseline and since and stat.st_mtime < since:
                continue
            start = baseline.get(key)
            if start is None:
                data = path.read_bytes()
            elif stat.st_size < start:
                data = path.read_bytes()  # 文件被重写，整文件视为新内容
            elif start >= stat.st_size:
                continue  # 没有新增内容
            else:
                with path.open("rb") as file_handle:
                    file_handle.seek(start)
                    data = file_handle.read()
        except OSError:
            continue
        checked.append(key)
        text = _decode_log_bytes(data)
        found = _extract_error_blocks(text)
        if found:
            errors.extend(found)
            error_lines.extend(line for block in found for line in block.splitlines())
        lines = text.splitlines()
        tails[key] = lines[-_TAIL_LINES:] if lines else []
    return {
        "errors": errors,
        "error_lines": error_lines,
        "log_files": checked,
        "log_tails": tails,
    }


__all__ = [
    "capture_solver_log_baseline",
    "read_appended_solver_logs",
    "solver_log_files",
]
