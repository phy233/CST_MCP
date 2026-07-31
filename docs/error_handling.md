# CST Runtime / MCP 错误处理

## 目标与边界

本阶段解决 CST 2022 `add_to_history()` 可能在 VBA 失败时仍返回 `True` 的问题。
Runtime 不再把“已缓冲”“COM 已接受”“VBA 已执行”和“业务结果已验证”混成同一个成功状态。

本阶段不实现自动回滚、Message Window 读取、完整事务系统或 History 自动修复。私有
`_GetHistory` 和 `_TryToUndoNTimes` 只出现在显式启用的人工验收样例中，不进入生产路径。

## 调用链

```text
Python validation
  -> Command Buffer（可选）
  -> VBA Error Gateway
       -> 即时 VBA 查询 CST 自己的 Temp 路径
       -> 创建一次性 arm 文件
       -> add_to_history(带 On Error 包装的业务 VBA)
       -> 轮询 OK / ERROR 状态文件
  -> lib 保留结构化结果
  -> API registry 归一化结果
  -> Worker JSONL（traceback 只写 stderr）
  -> Proxy / MCP 结构化 transport_error
```

`mcp_server` 仍不导入 `cst_runtime`。协议无关的信封构造位于
`cst_runtime/contracts.py`，Runtime 异常类型位于 `core/errors.py`。

## VBA Error Side Channel

Gateway 使用 `schematic.execute_vba_code()` 运行一个不写入 History 的完整宏，读取
`GetProjectPathName("Temp")`。Python 和随后的 History VBA 因而使用 CST 报告的同一目录，
而 History 不保存用户名或本机绝对路径。

每次提交使用唯一 `operation_id`，并生成：

- `cst-runtime-<operation_id>.arm`
- `cst-runtime-<operation_id>.status`

arm 文件由 Python 独占创建。包装器开始运行时检查并立即删除它。正常 History rebuild
仍会重放业务 VBA，但因没有 arm，不再写诊断状态文件。Python 对状态文件做有界轮询，
随后尽力清理两个文件。

状态解释如下：

| 状态 | 结果 |
| --- | --- |
| `OK` | `execution=reported_ok` |
| `ERROR` + number/source/description/line | `vba_runtime_error` |
| 缺失、残缺或等待超时 | `vba_compile_or_host_error` |
| COM 调用抛异常且没有完整 `ERROR` | `cst_submission_error` |

若 VBA 已写出 `ERROR` 后 COM 再抛异常，Gateway 优先采用文件中的
`vba_runtime_error`，避免丢失更具体的 CST 错误。

语法错误在执行前发生，无法由 `On Error` 捕获。因此 `compile_error` 只是人工测试中的场景名；
公开类型使用 `vba_compile_or_host_error`，因为缺失状态文件也可能由宿主拒绝、超时或包装器未运行造成。

## Command Buffer

批处理使用两阶段生命周期：

```text
peek_batch -> submit / read status -> commit_batch
```

失败时批次保留，并返回 `batch_retained=true`。连接/附着 CST 前失败会同时返回
`retry_safe=true`，此时可再次 `flush`；一旦已经进入 Gateway，超时或错误可能伴随部分副作用，
因此返回 `retry_safe=false`，批次只用于诊断，不能直接重放，应先人工检查再显式 `discard`。
只有 VBA 报告成功后才返回 `batch_committed=true` 并删除内存批次。空批次无需连接 CST，
直接提交为空操作。

## 返回契约

成功示例：

```json
{
  "ok": true,
  "status": "success",
  "submission": "accepted",
  "execution": "reported_ok",
  "verification": "not_run",
  "operation_id": "..."
}
```

失败示例：

```json
{
  "ok": false,
  "status": "error",
  "error_type": "vba_runtime_error",
  "message": "Material does not exist.",
  "error": {
    "type": "vba_runtime_error",
    "code": 1004,
    "source": "Brick.Create",
    "line": 0,
    "message": "Material does not exist.",
    "phase": "execution"
  },
  "context": {
    "project_path": "...",
    "history_label": "Define Brick:demo",
    "operation_id": "...",
    "vba_sha256": "..."
  }
}
```

为兼容现有 Python、CLI 和 workflow，顶层 `status/error_type/message` 暂时保留。
API/Worker 边界保证普通 JSON 字典。Worker 内部 traceback 只写受控 stderr，不返回 MCP 客户端。
Proxy 启动、IPC、退出、响应 ID 和超时故障统一为 `transport_error`，并带稳定的
`error.code` 与 `phase=transport`。

### 错误类型与阶段

| 类型 | phase | 含义 |
| --- | --- | --- |
| `validation_error` / `invalid_arguments` | `validation` | 发送前即可确认的输入错误 |
| `unsupported_feature` | `validation` | 当前 CST 会话没有所需能力 |
| `transport_error` | `transport` | Proxy、IPC、Worker 进程或超时故障 |
| `worker_error` | `worker` | Worker 导入、调用或协议处理故障 |
| `cst_submission_error` | `submission` | Side-channel 准备、COM 或 History 提交失败 |
| `vba_runtime_error` | `execution` | VBA `Err` 被包装器捕获 |
| `vba_compile_or_host_error` | `execution` | 无完整状态，不能安全断言成功 |
| `verification_failed` | `verification` | 命令无显式错误，但后置条件不成立 |
| `rollback_failed` | `rollback` | 后续版本尝试恢复但无法确认成功 |
| `runtime_error` | `runtime` | 未归入上述阶段的运行时错误 |

## 无 CST 测试

Runtime 测试要求普通 Python 3.9：

```powershell
$env:PYTHONPATH = (Resolve-Path "skills/cst-runtime-cli/scripts").Path
python -m pytest -q `
  skills/cst-runtime-cli/tests/test_error_gateway_contracts.py `
  skills/cst-runtime-cli/tests/test_history_buffer_gateway.py `
  skills/cst-runtime-cli/tests/test_lib_contracts.py `
  skills/cst-runtime-cli/tests/test_array.py `
  skills/cst-runtime-cli/tests/core/test_project.py
```

根目录 MCP/Proxy 无 CST 测试要求 Python 3.12+；测试时可让临时 Worker 使用同一解释器：

```powershell
$env:CST_WORKER_PYTHON = (Get-Command python).Source
python -m pytest -q
```

真实 CST 2022 Worker 仍必须配置为 CST 兼容的 Python 3.9，不能沿用上面的无 CST 测试设置。

测试覆盖异常类、JSON 序列化、`OK/ERROR/missing/malformed/timeout`、延迟状态写入、
ERROR 后 COM 抛错、stale 状态拒绝、两阶段 Buffer、Worker traceback 隐藏、Proxy/MCP
transport envelope，以及 lib 对原始错误类型的保留。

## CST 2022 人工验收

人工用例在 `skills/cst-runtime-cli/tests/test_error_gateway_cst2022.py`。它默认跳过，且每个用例
复制源工程；不要把生产工程直接作为测试目标。

```powershell
$env:CST_TEST_PROJECT = "D:\path\to\disposable-source.cst"
$env:CST_RUN_ERROR_GATEWAY_TESTS = "1"
python -m pytest -s -m "cst_integration" `
  skills/cst-runtime-cli/tests/test_error_gateway_cst2022.py
```

用例包括：正常 brick、不存在材料、主动 `Err.Raise`、VBA 语法错误，以及
`_GetHistory/_TryToUndoNTimes` 的观察性记录。最后一个用例不把一次 Undo 当作事务保证，
只输出执行前、失败后、Undo 后的 History 证据。

## 已知限制

- `execution=reported_ok` 只证明包装器到达成功出口；当前建模操作仍返回
  `verification=not_run`，不能替代实体、材料、参数或结果树的后置验证。
- 默认状态等待为 5 秒。超大批次若超过该时间会安全地返回
  `vba_compile_or_host_error`，不会误报成功；后续可按操作规模暴露超时配置。
- 状态缺失不能可靠地区分语法错误、编译错误、CST 宿主拒绝和代码未运行。
- compile/host 类错误会附带原始 VBA 便于诊断，可能包含模型细节；MCP/CLI 日志应按工程数据处理。
- 状态文件是错误侧信道，不是业务后置条件。实体存在性、参数读回、仿真终态和结果验证仍需后续实现。
- 自动回滚、Message Window 读取、完整事务和 History 修复不在本阶段范围内。
