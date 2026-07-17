import sys
import os

project_root = r"D:\My_Program\Python\CST_MCP\skills\cst-runtime-cli\scripts"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import cst.interface
from cst_runtime.lib.session import create_blank_project, quit_cst
from cst_runtime.core.utils import abs_project_path

def main():
    print("=== Testing add_to_history Return Value ===")
    
    project_name = os.path.join(project_root, "test_return.cst")
    target_cst = abs_project_path(project_name)
    
    import shutil
    target_dir = target_cst[:-4]
    for p in [target_cst, target_dir]:
        if os.path.exists(p):
            if os.path.isfile(p): os.remove(p)
            else: shutil.rmtree(p)
            
    print("1. Creating blank project...")
    res = create_blank_project(project_name)
    if res.get("status") != "success":
        print(f"FAILED: {res}")
        return
        
    pp = res["project_path"]
    
    from cst_runtime.core.identity import attach_expected_project
    project, _ = attach_expected_project(pp)
    if not project:
        print("Could not attach to project")
        return
    
    print("\n--- Test 1: Valid VBA ---")
    valid_vba = '''
    With Brick
        .Reset
        .Name "test_brick"
        .Component "component1"
        .Material "PEC"
        .Xrange "-5", "5"
        .Yrange "-5", "5"
        .Zrange "0", "1"
        .Create
    End With
    '''
    try:
        ret1 = project.modeler.add_to_history("Valid Brick", valid_vba)
        print(f"Valid VBA Return Value: {repr(ret1)}")
        print(f"Type of return: {type(ret1)}")
    except Exception as e:
        print(f"Valid VBA Raised Exception: {type(e).__name__}: {e}")
        
    print("\n--- Test 2: Invalid VBA (Bad Material) ---")
    invalid_vba = '''
    With Brick
        .Reset
        .Name "test_brick2"
        .Component "component1"
        .Material "THIS_MATERIAL_DOES_NOT_EXIST"
        .Xrange "-5", "5"
        .Yrange "-5", "5"
        .Zrange "0", "1"
        .Create
    End With
    '''
    try:
        ret2 = project.modeler.add_to_history("Invalid Brick", invalid_vba)
        print(f"Invalid VBA Return Value: {repr(ret2)}")
        print(f"Type of return: {type(ret2)}")
    except Exception as e:
        print(f"Invalid VBA Raised Exception: {type(e).__name__}: {e}")
        
    print("\n--- Test 3: Complete Syntax Garbage ---")
    garbage_vba = 'Solid.DoSomethingCrazy "what is this"'
    try:
        ret3 = project.modeler.add_to_history("Garbage VBA", garbage_vba)
        print(f"Garbage VBA Return Value: {repr(ret3)}")
        print(f"Type of return: {type(ret3)}")
    except Exception as e:
        print(f"Garbage VBA Raised Exception: {type(e).__name__}: {e}")
        
    print("\nCleaning up...")
    project.save()
    project.close()

if __name__ == "__main__":
    main()
