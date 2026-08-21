---
name: cst-mcp
description: 通过已连接的 CST MCP 服务检查工程、执行建模或配置、运行仿真、读取结果并查询审计记录。用户明确要求使用 MCP、CST MCP 或已连接该服务时使用；直接运行 Runtime CLI、部署环境或纯电磁理论讨论不使用本 Skill。
---

# CST MCP Skill

本 Skill 负责 MCP 工具调用边界。超表面的物理设计步骤由 `cst-metasurface-design` 负责；参数优化策略由 `cst-runtime-optimization` 负责。

## 调用原则

- 直接使用 MCP 当前暴露的工具；工具名称、描述和输入 Schema 是调用事实来源，不在文档中维护固定工具数量。
- 使用用户指定的绝对 `project_path`。多个打开工程、目标身份不唯一或锁未释放时，停止写入和关闭操作。
- 对未知工程先调用只读检查工具，确认参数、实体、端口、边界、监视器和结果节点后再提出修改。
- 默认逐步调用原子工具。只有用户明确选择时才使用管道，并先展示展开步骤、输入和停止条件。
- 每次调用都检查结构化 `status`、`error_type`、`message` 和关键输出，不以进程退出码或传输成功代替业务成功。

## 写操作与验证

`add_to_history()`、VBA 状态文件 `OK` 或 MCP `status=success` 证明的是相应提交/执行边界，不自动证明实体、配置、结果或导出文件正确。

根据操作补充验证：

- 参数写入后重新读取参数；
- 建模或布尔操作后检查实体；
- 边界、端口和激励配置后按工具能力显式 inspect；
- 仿真后确认日志、Run ID 和结果节点；
- 导出后确认文件存在且非空。

如果公开 getter 不足，明确写出未验证字段，不伪造读回结果。

## 失败处理

- 写操作返回超时、Worker 退出或 transport error 时，不立即重试；先检查 History、目标工程和实际副作用。
- expected-before 表示未应用，仍需用户确认后才能重试；expected-after 表示已应用并应跳过；两者都不匹配时按 ambiguous 停止。
- 不因工具重新连接成功而重复建模、启动求解或覆盖工程。
- 长时间仿真使用等待或状态工具，不反复发送启动命令。

## 记录与恢复

- MCP 自动记录工具请求、参数、返回值、耗时和可关联的 History 快照。
- 设计假设、用户确认和人工处置通过 `record-agent-note` 显式记录。
- 查询一次调用的 History 变化使用 `inspect-interaction-history`。
- 创建物理检查点、重放副本和人工 reconciliation 属于高风险 CLI 运维操作，MCP Agent 不自行绕过暴露策略。

需要详细的 History、检查点和交互审计步骤时，读取 `cst-runtime-cli/references/history-and-recovery.md`。需要超表面设计判断时，使用 `cst-metasurface-design`。
