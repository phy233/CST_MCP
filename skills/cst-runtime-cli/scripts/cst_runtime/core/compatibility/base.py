"""CST 版本画像与兼容错误的公共定义。"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Iterable

from ..errors import UnsupportedFeatureError


@dataclass(frozen=True)
class CompatibilityProfile:
    """描述当前 CST Python/COM 环境中已确认的版本与能力。"""

    major: int = 0
    version: str = "unknown"
    source: str = "unknown"
    capabilities: frozenset[str] = frozenset()

    @property
    def label(self) -> str:
        if self.major == 2022:
            return "cst2022"
        if self.major >= 2026:
            return "cst2026"
        return "unknown"

    @property
    def is_2022(self) -> bool:
        return self.major == 2022

    @property
    def is_2026_or_later(self) -> bool:
        return self.major >= 2026

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities

    def metadata(self, path: str | None = None, **extra: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "profile": path or self.label,
            "detected_version": self.version,
            "detection_source": self.source,
        }
        payload.update(extra)
        return payload


_PROFILE_CACHE: CompatibilityProfile | None = None


def _iter_version_texts(value: Any) -> Iterable[str]:
    """按原始顺序遍历版本返回结构中的标量文本。"""
    if isinstance(value, dict):
        for item in value.values():
            yield from _iter_version_texts(item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            yield from _iter_version_texts(item)
        return
    yield str(value or "")


def _extract_product_year(value: Any) -> tuple[int, str] | None:
    """优先提取明确标注为 CST 产品版本的年份。"""
    texts = tuple(_iter_version_texts(value))
    for pattern in (
        r"(?<!\d)(20\d{2})(?:\.[0-9.]+)?\s+Release\b",
        r"\bCST(?:\s+Studio\s+Suite)?\s+(20\d{2})\b",
    ):
        for text in texts:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return int(match.group(1)), text
    return None


def _extract_year(value: Any) -> tuple[int, str] | None:
    """从 CST 返回值提取版本年份，同时排除普通构建日期。"""
    product_year = _extract_product_year(value)
    if product_year:
        return product_year
    if isinstance(value, dict):
        for key in ("version", "Version", "major", "Major", "release", "Release"):
            if key in value:
                parsed = _extract_year(value[key])
                if parsed:
                    return parsed
        for item in value.values():
            parsed = _extract_year(item)
            if parsed:
                return parsed
        return None
    if isinstance(value, (tuple, list)):
        for item in value:
            parsed = _extract_year(item)
            if parsed:
                return parsed
        return None
    text = str(value or "")
    match = re.search(
        r"(?<!\d)(20\d{2})(?!-[0-9]{2}-[0-9]{2})(?:[.\s_][0-9.]+)?",
        text,
    )
    if not match:
        return None
    return int(match.group(1)), text


def _capabilities_for_major(major: int) -> frozenset[str]:
    common = {
        "design_environment_constructor",
        "history_vba",
        "legacy_result_tree_vba",
        "parameter_vba_query",
    }
    if major == 2022:
        common.update(
            {
                "project_path",
                "legacy_modeling_vba",
                "legacy_monitor_vba",
                "legacy_farfield_plot",
            }
        )
    elif major >= 2026:
        common.update(
            {
                "project_path_name",
                "model3d",
                "result_tree_api",
                "result2d",
                "farfield_calculator",
                "modern_modeling_vba",
            }
        )
    return frozenset(common)


def detect_compatibility_profile(*, force_refresh: bool = False) -> CompatibilityProfile:
    """检测已绑定的 CST 库版本；未知版本保持未知，不推测 VBA 语法。"""
    global _PROFILE_CACHE
    if _PROFILE_CACHE is not None and not force_refresh:
        return _PROFILE_CACHE

    override = os.environ.get("CST_RUNTIME_CST_VERSION", "").strip()
    parsed = _extract_year(override)
    if parsed:
        major, version = parsed
        _PROFILE_CACHE = CompatibilityProfile(
            major=major,
            version=version,
            source="environment:CST_RUNTIME_CST_VERSION",
            capabilities=_capabilities_for_major(major),
        )
        return _PROFILE_CACHE

    candidates: list[tuple[str, Any]] = []
    try:
        import cst.results

        getter = getattr(cst.results, "get_version_info", None)
        if callable(getter):
            try:
                candidates.append(("cst.results.get_version_info", getter()))
            except Exception:
                pass
        candidates.append(("cst.results.__file__", getattr(cst.results, "__file__", "")))
    except Exception:
        pass

    try:
        import cst.interface

        candidates.append(("cst.interface.__file__", getattr(cst.interface, "__file__", "")))
        candidates.append(("cst.interface.__version__", getattr(cst.interface, "__version__", "")))
    except Exception:
        pass

    for module_name, module in tuple(sys.modules.items()):
        if module_name == "cst" or module_name.startswith("cst."):
            candidates.append((f"{module_name}.__file__", getattr(module, "__file__", "")))

    for source, value in candidates:
        parsed = _extract_year(value)
        if parsed:
            major, version = parsed
            _PROFILE_CACHE = CompatibilityProfile(
                major=major,
                version=version,
                source=source,
                capabilities=_capabilities_for_major(major),
            )
            return _PROFILE_CACHE

    _PROFILE_CACHE = CompatibilityProfile()
    return _PROFILE_CACHE


def profile_for(project: Any | None = None) -> CompatibilityProfile:
    """返回版本画像，并根据实际项目对象补充可验证的 Python API 能力。"""
    base = detect_compatibility_profile()
    capabilities = set(base.capabilities)
    if project is not None:
        if getattr(project, "model3d", None) is not None:
            capabilities.add("model3d")
        if getattr(project, "modeler", None) is not None:
            capabilities.add("modeler")
        if getattr(project, "schematic", None) is not None:
            capabilities.add("immediate_vba")
    return CompatibilityProfile(
        major=base.major,
        version=base.version,
        source=base.source,
        capabilities=frozenset(capabilities),
    )


def compatibility_metadata(
    project: Any | None = None,
    *,
    path: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    return profile_for(project).metadata(path=path, **extra)


def unsupported_feature(
    feature: str,
    *,
    project: Any | None = None,
    required_capability: str,
    unsupported_arguments: Iterable[str] = (),
    message: str | None = None,
    next_action: str | None = None,
) -> UnsupportedFeatureError:
    """创建字段完整、可跨 Worker 返回的兼容性错误。"""
    profile = profile_for(project)
    return UnsupportedFeatureError(
        message or f"当前 CST 版本不支持功能：{feature}",
        feature=feature,
        next_action=next_action or "请改用受支持的参数或升级 CST 后重试。",
        context={
            "detected_version": profile.version,
            "required_capability": required_capability,
            "unsupported_arguments": list(unsupported_arguments),
            "compatibility": profile.metadata(),
        },
    )


def get_model3d(project: Any) -> Any:
    """取得新版 model3d；旧版缺失时返回结构化兼容错误。"""
    model3d = getattr(project, "model3d", None)
    if model3d is None:
        raise unsupported_feature(
            "python.model3d",
            project=project,
            required_capability="model3d",
            next_action="改用兼容 VBA 查询通道，或在 CST 2026 中执行。",
        )
    return model3d


def reset_profile_cache() -> None:
    """仅供测试或重新绑定 CST Python 库后刷新版本画像。"""
    global _PROFILE_CACHE
    _PROFILE_CACHE = None


__all__ = [
    "CompatibilityProfile",
    "compatibility_metadata",
    "detect_compatibility_profile",
    "get_model3d",
    "profile_for",
    "reset_profile_cache",
    "unsupported_feature",
]
