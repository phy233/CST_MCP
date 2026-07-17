import sys
import time
import os

try:
    import cst.interface
except ImportError:
    print("Could not import cst.interface. Ensure CST is in PYTHONPATH.")
    sys.exit(1)

def print_header(title):
    print(f"\n{'='*60}")
    print(f"--- {title} ---")
    print(f"{'='*60}\n")

def main():
    print("Connecting to CST Environment...")
    try:
        cst_env = cst.interface.DesignEnvironment()
        project = cst_env.new_mws()
        print("Successfully created new MWS project.")
    except Exception as e:
        print(f"Failed to start CST: {type(e).__name__}: {e}")
        return

    # ==========================================
    # Experiment 1: add_to_history sync/async?
    # ==========================================
    print_header("Experiment 1: add_to_history sync/async?")
    # VBA blocking execution using Timer
    vba_sleep = """
Sub Main()
    Dim t1 As Double
    t1 = Timer
    While Timer < t1 + 3
    Wend
End Sub
"""
    print("Running VBA with 3 seconds block via add_to_history...")
    t_start = time.perf_counter()
    res = project.modeler.add_to_history("SleepTest", vba_sleep)
    t_end = time.perf_counter()
    elapsed1 = t_end - t_start
    print(f"Elapsed Time: {elapsed1:.4f} seconds")
    print(f"Return Value: {res}")

    # ==========================================
    # Experiment 2: execute_vba_code sync/async?
    # ==========================================
    print_header("Experiment 2: execute_vba_code sync/async?")
    has_exec_vba = False
    methods_to_check = ['execute_vba_code', '_execute_vba_code']
    objects_to_check = [("project", project), ("project.modeler", project.modeler)]
    
    if hasattr(project, 'schematic'):
        objects_to_check.append(("project.schematic", project.schematic))
    if hasattr(project, 'model3d'):
        objects_to_check.append(("project.model3d", project.model3d))
        
    for name, obj in objects_to_check:
        for m in methods_to_check:
            if hasattr(obj, m):
                has_exec_vba = True
                print(f"Found {m} on {name}")
                func = getattr(obj, m)
                t_start = time.perf_counter()
                try:
                    res2 = func(vba_sleep)
                    t_end = time.perf_counter()
                    print(f"Elapsed Time: {t_end - t_start:.4f} seconds")
                    print(f"Return Value: {res2}")
                except Exception as e:
                    print(f"Exception calling {m}: {type(e).__name__}: {e}")

    if not has_exec_vba:
        print("No execute_vba_code method found on standard objects.")

    # ==========================================
    # Experiment 3: Python/VBA communication
    # ==========================================
    print_header("Experiment 3: Python/VBA communication")
    
    print("--- Plan A: File I/O ---")
    test_file_path = os.path.abspath("vba_test_out.txt").replace('\\', '\\\\')
    vba_file_io = f"""
Dim fso As Object
Set fso = CreateObject("Scripting.FileSystemObject")
Dim file As Object
Set file = fso.CreateTextFile("{test_file_path}", True)
file.WriteLine("Hello from VBA")
file.Close
"""
    project.modeler.add_to_history("FileIOTest", vba_file_io)
    
    # Give a tiny sleep to allow async completion if it was async
    time.sleep(1)
    
    file_path_real = test_file_path.replace('\\\\', '\\')
    if os.path.exists(file_path_real):
        with open(file_path_real, 'r') as f:
            content = f.read().strip()
        print(f"File Output: '{content}'")
        os.remove(file_path_real)
    else:
        print("File was not created. (Is VBA async or blocked?)")

    print("--- Plan B: Parameters ---")
    vba_param = 'StoreDouble("TestParamVBA", 42.5)'
    project.modeler.add_to_history("ParamTest", vba_param)
    print("Trying to read parameter 'TestParamVBA' from exported methods if possible...")

    print("--- Plan C: Function Returns via execute_vba_code ---")
    vba_return = """
Function Main() As String
    Main = "SecretDataFromVBA"
End Function
"""
    if has_exec_vba:
        try:
            ret = project.schematic.execute_vba_code(vba_return)
            print(f"Function Return Value: '{ret}'")
        except Exception as e:
            print(f"Function Return Exception: {e}")
    else:
        print("execute_vba_code not available, cannot test Plan C.")
    # Check what param methods exist
    print("Checking param methods on project:", [a for a in dir(project) if 'param' in a.lower()])
    print("Checking param methods on project.modeler:", [a for a in dir(project.modeler) if 'param' in a.lower()])
    if hasattr(project, 'schematic'):
        print("Checking param methods on schematic:", [a for a in dir(project.schematic) if 'param' in a.lower()])

    # ==========================================
    # Experiment 4: Message Window accessibility
    # ==========================================
    print_header("Experiment 4: Message Window Accessibility")
    print("Triggering Syntax Error via add_to_history...")
    project.modeler.add_to_history("SyntaxError", "Invalid VBA Syntax! $$$")
    
    print("Inspecting objects for message/log methods...")
    targets = {
        "project": project,
        "project.modeler": project.modeler
    }
    if hasattr(project, 'schematic'): targets['project.schematic'] = project.schematic
    if hasattr(project, 'model3d'): targets['project.model3d'] = project.model3d
    
    keywords = ['message', 'log', 'output', 'error', 'console', 'diagnostic', 'warning']
    found_any = False
    for name, obj in targets.items():
        attrs = dir(obj)
        matched = [a for a in attrs if any(k in a.lower() for k in keywords)]
        if matched:
            print(f"Found on {name}: {matched}")
            found_any = True
    if not found_any:
        print("No matching methods found for message retrieval.")

    # ==========================================
    # Experiment 5: full_history_rebuild error reporting
    # ==========================================
    print_header("Experiment 5: full_history_rebuild()")
    print("Executing full_history_rebuild with existing broken history (from Exp 4)...")
    t_start = time.perf_counter()
    try:
        rebuild_res = project.modeler.full_history_rebuild()
        t_end = time.perf_counter()
        print(f"Rebuild completed in {t_end - t_start:.4f}s. Result: {rebuild_res}")
    except Exception as e:
        print(f"Rebuild threw Exception: {type(e).__name__}: {e}")

    # ==========================================
    # Experiment 6: COM Exception Boundaries
    # ==========================================
    print_header("Experiment 6: COM Exception Boundary")
    
    def test_call(name, func, *args, **kwargs):
        print(f"Testing {name}...")
        try:
            res = func(*args, **kwargs)
            print(f" -> Returned: {res}")
        except Exception as e:
            print(f" -> Raised Exception: {type(e).__name__} : {e}")

    test_call("open_project(bogus_path)", cst_env.open_project, "C:\\invalid_bogus_dir\\bogus_proj.cst")
    test_call("project.save(bogus_path)", project.save, "X:\\invalid_drive\\test.cst")
    
    print("\nExperiments completed.")

if __name__ == "__main__":
    main()
