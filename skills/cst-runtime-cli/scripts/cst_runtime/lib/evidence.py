"""证据采集业务门面。"""
from ..core import evidence as _core
from ._facade import wrap_core

capture_snapshot = wrap_core(_core.capture_snapshot)
compare_snapshots = wrap_core(_core.compare_snapshots)
