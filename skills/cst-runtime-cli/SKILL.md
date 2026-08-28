---
name: cst-runtime-cli
description: 直接使用 Python 3.9 Worker 运行 CST Runtime CLI，覆盖环境诊断、工程会话、建模、仿真、结果读取、History 检查点和高风险运维。当用户明确要求直接调用 CLI、诊断或部署 Runtime、MCP 未连接，或所需操作标记为 CLI-only 时使用；已连接 MCP 的普通设计任务优先使用 cst-mcp。
---

# CST Runtime CLI Skill

本 Skill 是人工授权下的执行与运维通道，不自行选择目标工程、转移会话所有权或替用户作出电磁设计决定。能够调用 CLI 只代表具有执行接口，不代表能够完成端到端或全自动设计。

## 运行边界

Runtime 必须由 CST 兼容的 Python 3.9 Worker 执行：

```powershell
& $env:CST_WORKER_PYTHON -m cst_runtime <tool> [args]
```

如果没有设置该环境变量，优先使用项目内 `.envs/cst39/Scripts/python.exe`，也可以在 `.cst_config.json` 中设置 `runtime.worker_python`。Python 3.9 与 MCP 的 Python 3.12 环境都可由 uv 管理，但不得共用同一个虚拟环境，也不得通过 MCP 环境执行 `python -m cst_runtime`。

首次部署或环境故障时读取 [setup_guide.md](references/setup_guide.md)。

## 默认调用方式

1. 仅在首次部署、Worker/MCP 连接异常或环境故障时运行 `health-check --auto-fix false`；普通业务调用前不重复运行；
2. 仅在工具名、参数 Schema 或暴露状态未知或可能已变化时使用一次 `list-tools` / `describe-tool`；已有当前契约时直接调用；
3. 数组、对象和复杂路径参数先用 `args-template` 生成 JSON，再通过 `--args-file` 调用；
4. 默认每次执行一个边界清楚的步骤，解析 stdout 的 JSON `status` 后再继续；
5. 接口没有返回错误并给出成功状态时，充分相信 CST 已成功执行对应 VBA，不在普通写操作前后重复读取参数、实体、配置或 History。

必要检查只用于结果导出等文件产物、异步求解完成与结果取得，以及接口已经返回错误、超时或 ambiguous 后的副作用判断。删除、覆盖、关闭或进程终止前的目标与授权确认仍然保留，但不把它解释为对 CST 成功返回的不信任。

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
