import sys
import os

project_root = r"D:\My_Program\Python\CST_MCP\skills\cst-runtime-cli\scripts"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import inspect
from cst_runtime.lib.session import create_blank_project
from cst_runtime.core.identity import attach_expected_project
from cst_runtime.core.utils import abs_project_path

def main():
    print("=== Testing CST Object Introspection ===")
    
    project_name = os.path.join(project_root, "test_intro.cst")
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
    
    project, _ = attach_expected_project(pp)
    if not project:
        print("Could not attach to project")
        return
        
    modeler = project.modeler
    
    print("\n--- Introspection of project.modeler ---")
    print(f"Type: {type(modeler)}")
    
    # 获取所有的成员和方法
    try:
        attrs = dir(modeler)
        print(f"\nAll Attributes / Methods ({len(attrs)}):")
        # 过滤掉以双下划线开头的内置方法，重点找我们关心的隐藏接口
        public_attrs = [a for a in attrs if not a.startswith("__")]
        print(", ".join(public_attrs))
        
        # 找找有没有带 error, log, message, output 的
        keywords = ["error", "log", "message", "output", "history", "status"]
        suspicious = [a for a in public_attrs if any(k in a.lower() for k in keywords)]
        if suspicious:
            print("\nSuspicious attributes found matching our keywords:")
            for s in suspicious:
                print(f" - {s}: {type(getattr(modeler, s, None))}")
    except Exception as e:
        print(f"Failed to introspect: {e}")
    
    print("\n--- Introspection of project ---")
    print(f"Type: {type(project)}")
    try:
        p_attrs = [a for a in dir(project) if not a.startswith("__")]
        suspicious_p = [a for a in p_attrs if any(k in a.lower() for k in keywords)]
        if suspicious_p:
            print("\nSuspicious attributes on PROJECT object:")
            for s in suspicious_p:
                print(f" - {s}: {type(getattr(project, s, None))}")
    except Exception as e:
        pass
        
    print("\n--- Test Return Values again ---")
    ret = modeler.add_to_history("Garbage", "THIS IS NONSENSE")
    print(f"ret = {ret}")
    print(f"ret is True: {ret is True}")
    print(f"type(ret) = {type(ret)}")
    
    print("\nCleaning up...")
    project.save()
    project.close()

if __name__ == "__main__":
    main()
