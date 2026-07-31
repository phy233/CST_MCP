"""cst_runtime 的统一公共操作注册表。"""

from .registry import (
    OperationSpec,
    describe_operations,
    describe_tools,
    invoke,
    invoke_tool,
    operations,
    tools,
)
from .inventory import operation_inventory

__all__ = [
    "OperationSpec",
    "describe_operations",
    "describe_tools",
    "invoke",
    "invoke_tool",
    "operations",
    "tools",
    "operation_inventory",
]
