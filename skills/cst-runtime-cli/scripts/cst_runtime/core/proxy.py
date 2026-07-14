import json
import subprocess
import threading
import sys
import queue
from pathlib import Path
from typing import Any

class CSTWorkerProxy:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.process = None
        self.response_queue = queue.Queue()
        self.reader_thread = None
        self._start_worker()
        
    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = CSTWorkerProxy()
            return cls._instance
            
    def _start_worker(self):
        # Locate cst_worker.py
        scripts_dir = Path(__file__).resolve().parent.parent.parent
        worker_script = scripts_dir / "cst_worker.py"
        
        # We assume conda environment 'cst39' exists
        # On Windows, 'conda' is often a .bat file, which requires shell=True to be found
        cmd_str = f'conda run -n cst39 --no-capture-output python "{worker_script}"'
        
        # Launch worker
        self.process = subprocess.Popen(
            cmd_str,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # line buffered
            shell=True  # Required on Windows to resolve 'conda' command
        )
        
        self.reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader_thread.start()
        
        # Wait for ready signal
        try:
            ready_resp = self.response_queue.get(timeout=15)
            if ready_resp.get("status") != "ready":
                raise RuntimeError(f"Worker failed to start: {ready_resp}")
        except queue.Empty:
            raise RuntimeError("Timeout waiting for cst_worker.py to initialize. Ensure conda env 'cst39' exists.")
            
    def _read_stdout(self):
        try:
            if self.process and self.process.stdout:
                for line in self.process.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        resp = json.loads(line)
                        self.response_queue.put(resp)
                    except json.JSONDecodeError:
                        # Print non-json output to stderr for debugging (likely CST engine output)
                        print(f"[CST Worker] {line}", file=sys.stderr)
        except Exception:
            pass

    def call(self, module_name: str, func_name: str, **kwargs) -> dict[str, Any]:
        if self.process is None or self.process.poll() is not None:
            # Restart if dead
            self._start_worker()
            
        req = {
            "module": module_name,
            "function": func_name,
            "kwargs": kwargs
        }
        
        try:
            self.process.stdin.write(json.dumps(req) + "\n")
            self.process.stdin.flush()
            
            # Wait for response
            resp = self.response_queue.get(timeout=60) # 1 minute timeout for simulation calls
            return resp
        except queue.Empty:
            return {"status": "error", "error_type": "timeout", "message": "Worker did not respond in time"}
        except Exception as e:
            return {"status": "error", "error_type": "ipc_error", "message": str(e)}
            
    def shutdown(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(json.dumps({"action": "shutdown"}) + "\n")
                self.process.stdin.flush()
                self.process.wait(timeout=3)
            except Exception:
                self.process.kill()

def call_cst(module_name: str, func_name: str, **kwargs) -> dict[str, Any]:
    proxy = CSTWorkerProxy.get_instance()
    return proxy.call(module_name, func_name, **kwargs)
