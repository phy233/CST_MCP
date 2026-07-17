import sys
import json
import os
project_root = r"D:\My_Program\Python\CST_MCP\skills\cst-runtime-cli\scripts"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from cst_runtime.core.session import create_blank_project
from cst_runtime.core.project import save_project
from cst_runtime.lib.geometry import brick, boolean_add, translate
from cst_runtime.core.modeling import begin_batch, flush_batch

print("Creating blank project...")
res = create_blank_project("test_translate_zero")
pp = res["project_path"]

print("Begin batch...")
begin_batch(pp, "Test Translate Zero")

brick(pp, component="metasurface", name="arm_h", material="PEC", x_range=(-5, 5), y_range=(-1, 1), z_range=(0, 0.5))

print("Translating with (0,0,0)...")
translate(pp, "metasurface:arm_h", (0, 0, 0), multiple_objects=True, destination="metasurface")

print("Flushing...")
res = flush_batch(pp)
print("Flush result:", res)

save_project(pp)
