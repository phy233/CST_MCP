import sys
import json
import time
from mcp_server.server import create_mcp_server
from mcp_server.proxy import CSTWorkerProxy, CSTTransportError

def test():
    print("=== 1. Tool List & 2. Schema & 3. Description ===")
    mcp = create_mcp_server()
    # FastMCP uses _tool_manager.list_tools() internally, but we can also use mcp.list_tools() if it's async, wait, mcp doesn't expose it synchronously directly for tools, we'll iterate mcp._tools or whatever it has.
    # Actually, mcp._tool_manager is an internal component. FastMCP 1.2+ exposes it slightly differently.
    # We can just iterate mcp._tools dictionary if it exists.
    
    tools = []
    # Hacky way to get tools from FastMCP depending on version
    if hasattr(mcp, '_tools'):
        tools = mcp._tools.values()
    elif hasattr(mcp, '_tool_manager') and hasattr(mcp._tool_manager, 'list_tools'):
        tools = mcp._tool_manager.list_tools()
        
    print(f"Total tools registered: {len(tools)}")
    
    for tool in tools:
        if tool.name in ["open-project", "define-brick", "start-simulation"]:
            print(f"\nTool: {tool.name}")
            print(f"Description: {tool.description}")
            print(f"Schema: {json.dumps(tool.parameters, indent=2)}")

    print("\n=== 4. Result & 5. Worker Continuity & 6. Session ===")
    proxy = CSTWorkerProxy.get_instance()
    pid = proxy.process.pid
    print(f"Worker PID: {pid}")
    
    # Send a call to check format and continuity
    resp1 = proxy.call("lib.session", "list_open")
    print(f"Call 1 Result: {resp1}")
    print(f"Call 1 Worker PID: {proxy.process.pid} (Same? {pid == proxy.process.pid})")
    
    resp2 = proxy.call("lib.session", "list_open")
    print(f"Call 2 Result: {resp2}")
    print(f"Call 2 Worker PID: {proxy.process.pid} (Same? {pid == proxy.process.pid})")

    print("\n=== 7. Timeout / Crash Test ===")
    print("Killing worker process...")
    proxy.process.kill()
    time.sleep(1) # wait for process to die
    
    try:
        # Worker is dead, proxy should auto-restart it or throw error.
        # Actually our proxy auto-restarts if process is dead.
        print("Making a call after kill (should auto-restart)...")
        resp3 = proxy.call("lib.session", "list_open")
        print(f"Auto-restart Call Result: {resp3}")
        print(f"New Worker PID: {proxy.process.pid} (Restarted? {pid != proxy.process.pid})")
    except Exception as e:
        print(f"Exception after kill: {type(e).__name__} - {e}")
        
    print("\nSimulating a crash DURING a call (Timeout/Crash)...")
    proxy2 = CSTWorkerProxy.get_instance()
    # We monkey-patch the stdin to simulate writing, then kill the process so queue.get() times out or fails
    original_write = proxy2.process.stdin.write
    def fake_write(data):
        proxy2.process.kill()
        original_write(data)
    proxy2.process.stdin.write = fake_write
    
    try:
        resp4 = proxy2.call("lib.session", "list_open", timeout=3)
        print(f"Result: {resp4}")
    except CSTTransportError as e:
        print(f"Successfully caught TransportError: {e}")
    except Exception as e:
        print(f"Caught unexpected error: {type(e).__name__} - {e}")

if __name__ == "__main__":
    test()
