---
name: cst-runtime-cli
description: 直接使用 Python 3.9 Worker 运行 CST Runtime CLI，覆盖环境诊断、工程会话、建模、仿真、结果读取、History 检查点和高风险运维。当用户明确要求 CLI/runtime、低上下文命令链或 MCP 未暴露的 CLI-only 操作时使用；已连接 MCP 的普通设计任务优先使用 cst-mcp。
---

# CST Runtime CLI Skill

## 运行边界

Runtime 必须由 CST 兼容的 Python 3.9 Worker 执行：

```powershell
& $env:CST_WORKER_PYTHON -m cst_runtime <tool> [args]
```

如果没有设置该环境变量，使用 `.cst_config.json` 中 `runtime.worker_python` 的实际路径。不要通过 MCP 的现代 Python `.venv` 或 `uv run python -m cst_runtime` 启动 Runtime。

首次部署或环境故障时读取 [setup_guide.md](references/setup_guide.md)。

## 默认调用方式

1. 先运行 `health-check --auto-fix false`；
2. 使用 `list-tools` 和 `describe-tool` 获取实时工具名、参数 Schema、风险和暴露状态；
3. 数组、对象和复杂路径参数先用 `args-template` 生成 JSON，再通过 `--args-file` 调用；
4. 每次只执行一个可验证步骤，解析 stdout 的 JSON `status` 后再继续；
5. 修改后检查参数、实体、配置、结果或文件，不把提交成功当作工程结果正确。

详细命令约定见 [cli-invocation.md](references/cli-invocation.md)。原子工具与可选管道的选择见 [atomic-and-pipeline-usage.md](references/atomic-and-pipeline-usage.md)。

## 工程与 Session

- 所有 `project_path`、`source_project` 和 `working_project` 都必须指向具体 `.cst` 文件。
- 默认操作 `prepare-run` 创建的工作副本；参考工程视为只读蓝本。
- 不使用无目标的 `connect_to_any()` 回退。多个工程或目标身份不唯一时停止写入和关闭。
- 只有 Runtime 自己创建的 Design Environment 才能由 Runtime 退出或终止；用户已有会话即使确认附着也不转移所有权。
- 关闭、保存或复制工程前检查结构化返回值和 `.lok` 状态。

## 结果与错误

- modeler session 与离线 results 读取是不同边界，按工具返回的生命周期建议关闭和重新打开。
- S 参数原始数据通常为复数；dB 幅度使用 `20 * log10(abs(S))`。
- 远场 quantity 只按实际导出的 `Realized Gain`、`Gain` 或 `Directivity` 解释，不能把 `Abs(E)` 写成 dBi。
- Worker、VBA、求解器或锁文件故障按 [failure-recovery.md](references/failure-recovery.md) 处理；可能已产生副作用时不得盲目重试。

## History 与审计

History List、快照、物理检查点、恢复计划和交互日志的逐步用法见 [history-and-recovery.md](references/history-and-recovery.md)。其中物理检查点、重放副本和人工 reconciliation 是高风险 CLI-only 操作，执行前需要用户明确授权和精确工程路径。

## 领域路由

- 超表面、周期单元、Floquet 和 Plane Wave 设计判断：使用 `cst-metasurface-design`。
- 参数优化、多轮仿真和早停：使用 `cst-runtime-optimization`。
- 本 Skill 只维护 Runtime CLI 调用、安全边界和按需参考，不复制固定工具目录或 CST VBA 手册。
