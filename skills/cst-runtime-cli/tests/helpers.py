"""Shared test factory functions for cst-runtime-cli tests."""
from pathlib import Path
import json


def assert_json_error(result: dict, error_type: str) -> dict:
    """Assert JSON response has specific error type."""
    assert result["status"] == "error", f"Expected error, got: {result}"
    assert result["error_type"] == error_type, \
        f"Expected error_type='{error_type}', got: '{result.get('error_type')}'"
    return result
