"""工具协议参数解析；不得包含 CST 业务执行逻辑。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def parse_list_arg(value: Any) -> list[str]:
    """解析 JSON 数组或逗号分隔的工具参数。"""
    if isinstance(value, list):
        return [str(item) for item in value]
    if not isinstance(value, str) or not value.strip():
        return []
    text = value.strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except (TypeError, ValueError):
            pass
    return [
        item.strip().strip('"').strip("'")
        for item in text.strip("[]").split(",")
        if item.strip()
    ]


def project_path_from_args(args: dict[str, Any]) -> str:
    """解析工具层支持的工程路径别名并要求具体的 .cst 文件。"""
    value = args.get("project_path") or args.get("fullpath") or args.get("working_project")
    if not value:
        raise ValueError("project_path is required")
    project_path = str(value)
    if Path(project_path).suffix.lower() != ".cst":
        raise ValueError("project_path must point to a concrete .cst file, not a directory")
    return project_path


def run_id_from_args(args: dict[str, Any], default: int = 0) -> int:
    """解析单个 run_id，兼容旧协议中的 run_ids。"""
    if args.get("run_id") is not None:
        return int(args["run_id"])
    run_ids = args.get("run_ids")
    if isinstance(run_ids, list) and run_ids:
        return int(max(run_ids))
    return default
