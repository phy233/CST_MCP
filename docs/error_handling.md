# CST Runtime / MCP 错误处理

## 目标与边界

本阶段解决 CST 2022 `add_to_history()` 可能在 VBA 失败时仍返回 `True` 的问题。
Runtime 不再把“已缓冲”“COM 已接受”和“VBA 已执行”混成同一个成功状态；写操作不再附加执行后验证状态。

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
| `rollback_failed` | `rollback` | 后续版本尝试恢复但无法确认成功 |
| `runtime_error` | `runtime` | 未归入上述阶段的运行时错误 |

## 测试入口

普通 `python -m pytest -q` 只运行离线测试，不启动 CST。真实 CST 2022 测试必须显式运行：

```powershell
python -m pytest -q -s --run-cst -m cst_integration
```

真机层通过唯一 Python 3.9 Worker 复用一个隔离工程副本，不再使用每用例复制工程或人工
观察脚本。建模测试会查询实体真实存在，再调用公开删除工具并确认实体消失；求解器只启动到
`running=True`，随后强制停止。

完整的环境要求、单工程生命周期、清理契约和空结果 xfail 规则见
[CST MCP 测试指南](testing.md)。

## 已知限制

- `execution=reported_ok` 表示业务 VBA 已无错误执行到状态文件 `OK`，写操作据此返回成功；
  Runtime 不再自动读回实体、材料、参数或设置来改变该成功结论。
- 默认状态等待为 5 秒。超大批次若超过该时间会安全地返回
  `vba_compile_or_host_error`，不会误报成功；后续可按操作规模暴露超时配置。
- 状态缺失不能可靠地区分语法错误、编译错误、CST 宿主拒绝和代码未运行。
- compile/host 类错误会附带原始 VBA 便于诊断，可能包含模型细节；MCP/CLI 日志应按工程数据处理。
- 状态文件是 CST 错误侧信道。用户需要查看当前工程状态时，应显式调用只读查询工具；
  文件导出和仿真结果工具仍检查其承诺的输出是否真实存在且非空。
- 自动回滚、Message Window 读取、完整事务和 History 修复不在本阶段范围内。
