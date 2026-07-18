import sys
import os

project_root = r"D:\My_Program\Python\CST_MCP\skills\cst-runtime-cli\scripts"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from cst_runtime.lib.session import create_blank_project, save_project
from cst_runtime.lib.parameters import set_params
from cst_runtime.lib.geometry import brick, boolean_add
from cst_runtime.lib.boundary import set_all as set_boundary_all
from cst_runtime.lib.monitors import set_farfield

def run_tests():
    print("=== Testing lib layer functions ===")
    project_name = os.path.join(project_root, "test_lib_auto.cst")
    if os.path.exists(project_name):
        try: os.remove(project_name)
        except Exception: import shutil; shutil.rmtree(project_name, ignore_errors=True)
    target_dir = project_name[:-4]
    if os.path.exists(target_dir):
        import shutil
        shutil.rmtree(target_dir, ignore_errors=True)
    
    # 1. Session
    res = create_blank_project(project_name)
    assert res.get("status") == "success", f"create_blank_project failed: {res}"
    pp = res["project_path"]
    print("[PASS] create_blank_project")
    
    try:
        # 2. Parameters
        set_params(pp, {"len": 10.0, "rad": 5.0})
        print("[PASS] set_parameters")
        
        # 3. Geometry
        brick(pp, "comp1", "b1", "PEC", (0.0, 10.0), (0.0, 10.0), (0.0, 2.0))
        print("[PASS] brick 1")
        
        brick(pp, "comp1", "b2", "PEC", (2.0, 8.0), (2.0, 8.0), (2.0, 4.0))
        print("[PASS] brick 2")
        
        boolean_add(pp, "comp1:b1", "comp1:b2")
        print("[PASS] boolean_add")
        
        # 4. Boundary
        set_boundary_all(pp, "open")
        print("[PASS] set_boundary_all")
        
        # 5. Monitors
        set_farfield(pp, 1.0, 10.0, 1.0)
        print("[PASS] set_farfield")
        
        # 7. Save
        res = save_project(pp)
        assert res.get("status") == "success", f"save_project failed: {res}"
        print("[PASS] save_project")
        
        print("=== All lib layer tests passed! ===")
    finally:
        # 尝试静默关闭
        try:
            from cst_runtime.core.session import close_project
            close_project(pp, save=False)
        except Exception:
            pass

if __name__ == "__main__":
    run_tests()
