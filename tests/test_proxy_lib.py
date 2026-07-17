import sys
from pathlib import Path

# Setup path so we can import proxy
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_SCRIPTS_PATH = PROJECT_ROOT / "skills" / "cst-runtime-cli" / "scripts"
if str(RUNTIME_SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS_PATH))

from cst_runtime.core.proxy import call_cst, CSTWorkerProxy

def test_proxy_lib_list_open():
    """Test calling lib.session.list_open through the proxy."""
    print("\n--- Testing: lib.session.list_open ---")
    
    # We call "lib.session" instead of "core.session"
    result = call_cst("lib.session", "list_open")
    
    # Since list_open directly returns a list (from lib), we check the format
    print(f"Result: {result}")
    
    assert isinstance(result, dict), f"Expected dict wrapper from worker, got {type(result)}"
    assert result.get("status") == "success", "Status should be success"
    assert isinstance(result.get("result"), list), "Result field should be a list"

def test_proxy_lib_inspect():
    """Test calling lib.session.inspect through the proxy."""
    print("\n--- Testing: lib.session.inspect ---")
    
    # inspect returns a dict directly
    result = call_cst("lib.session", "inspect", project_path="")
    print(f"Result: {result}")
    
    assert isinstance(result, dict), "Result should be a dict"
    
    assert "status" in result
    if result["status"] == "success":
        assert "readiness" in result or "processes" in result

def test_proxy_lib_error_handling():
    """Test calling a non-existent lib function to verify error handling."""
    print("\n--- Testing: Error Handling (Invalid Function) ---")
    
    result = call_cst("lib.session", "this_function_does_not_exist")
    print(f"Result: {result}")
    
    assert isinstance(result, dict)
    assert result.get("status") == "error"
    assert "ipc_error" in result.get("error_type", "") or "AttributeError" in result.get("error_type", "")

def main():
    print("=== Testing Proxy -> Lib Integration ===")
    try:
        test_proxy_lib_error_handling()
        test_proxy_lib_list_open()
        test_proxy_lib_inspect()
        
        print("\n[PASS] All Proxy -> Lib integration tests passed successfully.")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    finally:
        print("\nShutting down proxy worker...")
        CSTWorkerProxy.get_instance().shutdown()

if __name__ == "__main__":
    main()
