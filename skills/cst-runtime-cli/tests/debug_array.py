import sys
import json
import os
project_root = r"D:\My_Program\Python\CST_MCP\skills\cst-runtime-cli\scripts"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from cst_runtime.core.buffer import _buffers
import cst_runtime.core.modeling as modeling
from cst_runtime.lib.geometry import translate, brick, boolean_add

# Do NOT monkeypatch _single_vba! Just intercept _add_vba_history if we don't want to run it,
# but actually we are in a batch! So _add_vba_history won't run CST anyway!
# In batch mode, _add_vba_history just appends to the buffer!

pp = "dummy_path.cst"
coords = [(0, 0, 0), (15.0, 0.0, 0.0)]
modeling.begin_batch(pp, "Test")

brick(pp, component="metasurface", name="arm_h", material="PEC", x_range=(-5, 5), y_range=(-1, 1), z_range=(0, 0.5))
brick(pp, component="metasurface", name="arm_v", material="PEC", x_range=(-1, 1), y_range=(-5, 5), z_range=(0, 0.5))
boolean_add(pp, "metasurface:arm_h", "metasurface:arm_v")

for x,y,z in coords:
    translate(pp, "metasurface:arm_h", (x,y,z), multiple_objects=True, destination="metasurface")

for k, v in _buffers.items():
    print(f"BUFFER KEY: {k}")
    print("VBA LINES:")
    print(v.get_vba_script())
