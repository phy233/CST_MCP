"""试验设计业务门面。"""
from ..core import doe as _core
from ._facade import wrap_core

design_probes = wrap_core(_core.design_probes)
analyze_probes = wrap_core(_core.analyze_probes)
