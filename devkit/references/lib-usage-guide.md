# CST Runtime `lib` 门面指南

## 定位

`cst_runtime.lib` 是面向 Python 调用者的门面层。MCP 与 CLI 工具参数应通过 Registry 查询；开发者只有在编写 Python 集成或实现工具 handler 时才直接使用 `lib`。

## 事实来源

- 可导入模块以 `cst_runtime/lib/__init__.py` 的 `__all__` 为准；
- 函数签名和返回类型以对应模块源码、类型注解和 docstring 为准；
- CLI/MCP 工具名、Schema、风险和暴露状态以 `list-tools`、`describe-tool` 为准；
- 不再维护手工枚举全部函数的静态 API Reference。

## 返回契约

门面并非所有模块都使用同一种 Python 风格：

- Session、参数、结果和多数现代门面返回 `OperationResult`，调用者检查 `status`，需要快速失败时使用 `raise_for_error()` 或 `unwrap()`；
- 部分早期几何门面成功时返回 `None`，失败时根据核心结果抛异常；
- 修改现有门面时不得假设所有函数都已统一，必须先检查实际签名和测试。

## 示例

```python
from cst_runtime.lib.session import open_project, close_project
from cst_runtime.lib.parameters import get_param, set_param

project_path = r"D:\models\working.cst"

open_project(project_path).raise_for_error()
before = get_param(project_path, "gap").unwrap("value")
set_param(project_path, "gap", 0.25).raise_for_error()
after = get_param(project_path, "gap").unwrap("value")
close_project(project_path, save=True).raise_for_error()
```

写操作成功后仍应按能力检查实际参数、实体、结果或文件。门面返回成功不自动证明电磁设置或仿真结论正确。

## 开发约束

- 新工具遵守 `tools -> lib -> core` 分层；
- `mcp_server` 不直接导入 Runtime；
- 普通 History VBA 保持紧凑，错误网关和快照由公共提交链统一处理；
- 新 CST API 先核对目标版本本机手册，再完成离线契约测试和单独真机验收；
- 具体流程见 [工具开发集成指南](tool-development-guide.md)。
