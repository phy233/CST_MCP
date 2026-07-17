import sys
import os

project_root = r"D:\My_Program\Python\CST_MCP\skills\cst-runtime-cli\scripts"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from cst_runtime.core.session import create_blank_project
from cst_runtime.core.project import save_project
from cst_runtime.lib.geometry import brick, boolean_add, translate
import cst.interface

def main():
    print("=== Phase 3: Interactive Array Test ===")
    
    print("0. Starting CST and ensuring it is visible...")
    try:
        de = cst.interface.DesignEnvironment.new()
        de.set_quiet_mode(False)  # Ensure CST is visible
    except Exception as e:
        print(f"Note: Could not set quiet mode on DE: {e}")

    # Create project through our API
    res = create_blank_project("test_interactive_array")
    if res.get("status") != "success":
        print(f"FAILED to create project: {res}")
        return
    pp = res["project_path"]
    
    input(f"\nCST Project '{pp}' created.\nCheck if the CST window is visible. Press Enter to draw Arm H...")
    
    brick(pp, component="metasurface", name="arm_h", material="PEC", x_range=(-5, 5), y_range=(-1, 1), z_range=(0, 0.5))
    input("Arm H drawn. Check History Tree. Press Enter to draw Arm V...")
    
    brick(pp, component="metasurface", name="arm_v", material="PEC", x_range=(-1, 1), y_range=(-5, 5), z_range=(0, 0.5))
    input("Arm V drawn. Check History Tree. Press Enter to Boolean Add...")
    
    boolean_add(pp, "metasurface:arm_h", "metasurface:arm_v")
    input("Boolean add done. Check History Tree. Press Enter to start translation...")
    
    coords = []
    for x in range(3):
        for y in range(3):
            coords.append((x * 15.0, y * 15.0, 0.0))
            
    for i, (x, y, z) in enumerate(coords):
        if abs(x) < 1e-9 and abs(y) < 1e-9 and abs(z) < 1e-9:
            print(f"Skipping {x,y,z} (origin) as it throws an error in Translate")
            continue
            
        print(f"\nTranslating to {x, y, z}...")
        res = translate(pp, "metasurface:arm_h", (x, y, z), multiple_objects=True, destination="metasurface")
        input(f"Translated to {x,y,z}. Check CST. Press Enter to continue...")
        
    print("\nArray translation done. Press Enter to save and exit.")
    input()
    
    save_project(pp)
    print("Project saved. You can now inspect it in CST.")
    
if __name__ == "__main__":
    main()
