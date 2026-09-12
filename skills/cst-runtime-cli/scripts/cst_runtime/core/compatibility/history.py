"""CST Modeler 私有 _GetHistory 接口与能力的底层适配器。

本模块直接接触 CST COM / Python 接口，仅负责读取原始数据与探测能力，
不包含快照、diff、日志或恢复等上层领域逻辑。
"""
from __future__ import annotations

from typing import Any


def supports_get_history(project: Any) -> bool:
    """检查指定工程的 modeler 是否提供可调用的 _GetHistory 私有接口。"""
    if project is None:
        return False
    modeler = getattr(project, "modeler", None)
    if modeler is None:
        return False
    get_history = getattr(modeler, "_GetHistory", None)
    return callable(get_history)


def get_raw_history(project: Any) -> dict[str, Any]:
    """从指定 CST 工程的 modeler 读取原始 History 字典。

    若接口不可用或调用失败，抛出对应的异常由调用方处理。
    返回值保持 CST 2022.5 实测形态：
      {"list": None} 或 {"list": [{"name": ..., "contents": ..., ...}]}
    """
    if project is None:
        raise ValueError("project 不能为 None")
    modeler = getattr(project, "modeler", None)
    if modeler is None:
        raise RuntimeError("CST 工程没有关联的 3D Modeler")
    get_history = getattr(modeler, "_GetHistory", None)
    if not callable(get_history):
        raise RuntimeError("当前 CST Modeler 不支持 _GetHistory 接口")
    try:
        raw = get_history()
    except UnicodeDecodeError as exc:
        # CST 私有绑定在转换中文标题或内容时可能直接失败，不能伪造完整快照。
        raise RuntimeError(
            "CST _GetHistory 私有接口无法解码当前历史中的中文文本；"
            "本次工具请求和执行结果仍记录在交互日志中，但完整历史快照不可用。"
        ) from exc
    if raw is None:
        return {"list": None}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, (list, tuple)):
        return {"list": list(raw)}
    raise TypeError(f"_GetHistory 返回了非预期的类型: {type(raw).__name__}")


def detect_history_capabilities(project: Any) -> dict[str, Any]:
    """探测当前 CST 环境对 History 相关接口的支持情况。"""
    if project is None:
        return {
            "has_modeler": False,
            "supports_get_history": False,
            "supports_add_to_history": False,
            "supports_full_history_rebuild": False,
            "cst_version": None,
        }
    modeler = getattr(project, "modeler", None)
    has_modeler = modeler is not None
    supports_get = callable(getattr(modeler, "_GetHistory", None)) if has_modeler else False
    supports_add = callable(getattr(modeler, "add_to_history", None)) if has_modeler else False
    supports_rebuild = callable(getattr(modeler, "full_history_rebuild", None)) if has_modeler else False

    cst_version = None
    try:
        from .base import profile_for
        profile = profile_for(project)
        cst_version = profile.cst_version
    except Exception:
        pass

    return {
        "has_modeler": has_modeler,
        "supports_get_history": supports_get,
        "supports_add_to_history": supports_add,
        "supports_full_history_rebuild": supports_rebuild,
        "cst_version": cst_version,
    }
