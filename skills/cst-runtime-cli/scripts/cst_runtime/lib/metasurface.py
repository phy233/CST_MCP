"""超表面 S 参数离线分析 facade。"""
from __future__ import annotations

from ..core import metasurface as _core
from ._facade import wrap_core


analyze_metasurface_sparameters = wrap_core(_core.analyze_metasurface_sparameters)


__all__ = ["analyze_metasurface_sparameters"]
