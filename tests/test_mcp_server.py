"""Tests for MCP Server configuration and adapter."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Add cst_runtime to path
CRT_SCRIPTS = PROJECT_ROOT / "skills" / "cst-runtime-cli" / "scripts"
sys.path.insert(0, str(CRT_SCRIPTS))


class TestMCPConfig:
    """Test MCP configuration."""

    def test_config_defaults(self):
        from mcp_server.config import MCPConfig

        config = MCPConfig()
        assert config.server_name == "cst-runtime"
        assert config.transport == "stdio"
        assert config.enable_write_tools is True
        assert config.enable_session_tools is True

    def test_config_instructions(self):
        from mcp_server.config import MCPConfig

        config = MCPConfig()
        instructions = config.instructions
        assert "CST Studio Suite" in instructions
        assert "[WRITE]" in instructions
        assert "[READ]" in instructions

    def test_get_config(self):
        from mcp_server.config import get_config

        config = get_config()
        assert config is not None
        assert hasattr(config, "cst_runtime_root")


class TestAdapter:
    """Test MCP adapter functionality."""

    def test_list_available_tools(self):
        from mcp_server.adapter import list_available_tools

        tools = list_available_tools()
        assert len(tools) > 0

        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "module" in tool
            assert "function" in tool
            assert "description" in tool
            assert "risk" in tool
            assert tool["risk"] in ["read", "write", "session", "long-running"]

    def test_tool_count(self):
        from mcp_server.adapter import TOOL_SPECS

        # Should have ~60+ tools defined
        assert len(TOOL_SPECS) >= 50

    def test_tool_specs_unique_names(self):
        from mcp_server.adapter import TOOL_SPECS

        names = [spec[2] for spec in TOOL_SPECS]
        assert len(names) == len(set(names)), "Tool names must be unique"

    def test_wrap_lib_function_read(self):
        from mcp_server.adapter import _wrap_lib_function

        def sample_read_func(project_path: str) -> dict:
            return {"status": "success", "data": "test"}

        handler = _wrap_lib_function(sample_read_func, "test-tool", "Test tool", "read")
        assert handler.__name__ == "test_tool"
        assert "[READ]" in handler.__doc__

    def test_wrap_lib_function_write(self):
        from mcp_server.adapter import _wrap_lib_function

        def sample_write_func(project_path: str, value: float) -> None:
            pass

        handler = _wrap_lib_function(sample_write_func, "test-write", "Test write", "write")
        assert "[WRITE]" in handler.__doc__

    @pytest.mark.asyncio
    async def test_handler_success(self):
        from mcp_server.adapter import _wrap_lib_function

        def sample_func(project_path: str) -> dict:
            return {"status": "success", "value": 42}

        handler = _wrap_lib_function(sample_func, "test-tool", "Test", "read")
        result = await handler(project_path="test.cst")
        assert '"status": "success"' in result
        assert '"value": 42' in result

    @pytest.mark.asyncio
    async def test_handler_error(self):
        from mcp_server.adapter import _wrap_lib_function

        def failing_func(project_path: str) -> dict:
            raise RuntimeError("Test error")

        handler = _wrap_lib_function(failing_func, "test-tool", "Test", "read")
        result = await handler(project_path="test.cst")
        assert '"status": "error"' in result
        assert "Test error" in result

    @pytest.mark.asyncio
    async def test_handler_key_error(self):
        from mcp_server.adapter import _wrap_lib_function

        def key_error_func(project_path: str) -> dict:
            raise KeyError("param not found")

        handler = _wrap_lib_function(key_error_func, "test-tool", "Test", "read")
        result = await handler(project_path="test.cst")
        assert '"status": "error"' in result
        assert "KeyError" in result

    @pytest.mark.asyncio
    async def test_handler_none_result(self):
        from mcp_server.adapter import _wrap_lib_function

        def none_func(project_path: str) -> None:
            pass

        handler = _wrap_lib_function(none_func, "test-tool", "Test", "write")
        result = await handler(project_path="test.cst")
        assert '"status": "success"' in result

    @pytest.mark.asyncio
    async def test_handler_list_result(self):
        from mcp_server.adapter import _wrap_lib_function

        def list_func(project_path: str) -> list:
            return ["item1", "item2"]

        handler = _wrap_lib_function(list_func, "test-tool", "Test", "read")
        result = await handler(project_path="test.cst")
        assert '"item1"' in result
        assert '"item2"' in result


class TestCompatLayer:
    """Test CST version compatibility layer."""

    def test_detect_version_without_cst(self):
        """Test version detection when CST is not available."""
        # Reset detection state
        import cst_runtime.core.compat as compat_module
        compat_module._detected = False
        compat_module._CST_MAJOR = 0
        compat_module._CST_MINOR = 0

        # This should not raise even if cst is not installed
        try:
            major, minor = compat_module.detect_version()
            assert isinstance(major, int)
            assert isinstance(minor, int)
        except ImportError:
            # If cst module is not available, that's expected
            pass

    def test_is_2022_or_later(self):
        from cst_runtime.core.compat import is_2022_or_later

        # Should return False when CST is not detected
        result = is_2022_or_later()
        assert isinstance(result, bool)

    def test_is_2026_or_later(self):
        from cst_runtime.core.compat import is_2026_or_later

        # Should return False when CST is not detected
        result = is_2026_or_later()
        assert isinstance(result, bool)

    def test_safe_running_design_environments(self):
        from cst_runtime.core.compat import safe_running_design_environments

        result = safe_running_design_environments()
        assert isinstance(result, list)

    def test_safe_quiet_mode_returns_context_manager(self):
        from cst_runtime.core.compat import safe_quiet_mode

        # Mock DE without quiet_mode_enabled
        mock_de = MagicMock(spec=[])
        cm = safe_quiet_mode(mock_de)
        assert hasattr(cm, "__enter__")
        assert hasattr(cm, "__exit__")


class TestServerModule:
    """Test server module structure."""

    def test_import_server(self):
        """Test that server module can be imported."""
        from mcp_server import server
        assert hasattr(server, "create_mcp_server")
        assert hasattr(server, "main")

    def test_import_adapter(self):
        """Test that adapter module can be imported."""
        from mcp_server import adapter
        assert hasattr(adapter, "register_all_tools")
        assert hasattr(adapter, "list_available_tools")
        assert hasattr(adapter, "TOOL_SPECS")

    def test_import_config(self):
        """Test that config module can be imported."""
        from mcp_server import config
        assert hasattr(config, "MCPConfig")
        assert hasattr(config, "get_config")


class TestToolRegistration:
    """Test tool registration with mocked FastMCP."""

    def test_register_tools(self):
        """Test that tools can be registered."""
        from mcp_server.adapter import register_all_tools

        # Create mock MCP
        mock_mcp = MagicMock()
        registered_tools = []

        def mock_tool(name, description):
            def decorator(func):
                registered_tools.append((name, func))
                return func
            return decorator

        mock_mcp.tool = mock_tool

        count = register_all_tools(mock_mcp)
        assert count > 0
        assert len(registered_tools) == count

        # Check some expected tools
        tool_names = [t[0] for t in registered_tools]
        assert "list-parameters" in tool_names
        assert "set-parameter" in tool_names
        assert "define-brick" in tool_names
        assert "start-simulation" in tool_names
