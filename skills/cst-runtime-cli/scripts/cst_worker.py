import sys
import json
import traceback
from pathlib import Path

# Ensure the parent directory is in sys.path so we can import cst_runtime
scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

import importlib

def handle_request(req: dict) -> dict:
    module_name = req.get("module")
    func_name = req.get("function")
    kwargs = req.get("kwargs", {})
    
    # 动态导入 cst_runtime 下的任意模块
    try:
        full_module_name = f"cst_runtime.{module_name}"
        mod = importlib.import_module(full_module_name)
    except ImportError as e:
        return {"status": "error", "error_type": "ipc_error", "message": f"Module {full_module_name} could not be imported: {e}"}
        
    if not hasattr(mod, func_name):
        return {"status": "error", "error_type": "ipc_error", "message": f"Function {func_name} not found in {module_name}."}
        
    func = getattr(mod, func_name)
    try:
        result = func(**kwargs)
        # Ensure result is dict
        if not isinstance(result, dict):
            return {"status": "success", "result": result}
        return result
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }

def main():
    # Setup environment: read workspace config for CST path
    # Workspace root is two levels up from scripts_dir
    workspace_root = scripts_dir.parent.parent
    cst_path = None
    try:
        config_path = workspace_root / ".cst_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            cst_path = config.get("project", {}).get("cst_path")
    except Exception:
        pass
        
    if cst_path:
        # Dynamically inject CST libraries path directly into sys.path
        if cst_path not in sys.path:
            sys.path.insert(0, cst_path)
    
    # Inform parent that worker is ready
    print(json.dumps({"status": "ready"}), flush=True)

    # Listen on stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        try:
            req = json.loads(line)
            if req.get("action") == "ping":
                resp = {"status": "pong"}
            elif req.get("action") == "shutdown":
                break
            else:
                resp = handle_request(req)
        except json.JSONDecodeError as e:
            resp = {"status": "error", "error_type": "json_error", "message": str(e)}
        except Exception as e:
            resp = {"status": "error", "error_type": type(e).__name__, "message": str(e)}
            
        # Write response back
        print(json.dumps(resp), flush=True)

if __name__ == "__main__":
    main()
