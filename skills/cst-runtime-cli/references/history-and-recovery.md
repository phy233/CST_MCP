# History、检查点与交互审计

## 概念边界

- History List：`_GetHistory()` 导出的线性块列表及原始 VBA；不是 GUI 中实体依赖关系的 History Tree。
- History snapshot：用于查看、哈希和 diff，不包含完整求解结果或全部外部依赖。
- 轻量 checkpoint：给某个 snapshot 命名，不复制工程。
- 物理 checkpoint：保存并关闭工程、确认解锁后复制 `.cst` 与伴随目录。
- restore plan：只分析，不修改 CST。
- checkout/replay copy：在隔离副本中按前缀关系重放 Runtime 保存的业务 VBA。

`add_to_history()` 会在当前 History 末尾追加并执行命令，不能用来跳转到任意历史状态。恢复已有前缀时只重放缺失后缀，绝不向已有工程重新提交整段 History。

## 分步命令

以下示例省略公共入口 `& $env:CST_WORKER_PYTHON -m cst_runtime`，调用前用 `describe-tool` 获取准确参数。

| 动作 | 工具 | 是否修改 CST/工程 |
| --- | --- | --- |
| 查看能力 | `inspect-history-capabilities` | 只读；可能短暂精确打开目标工程 |
| 查看未完成操作 | `inspect-history-status` | 只读 |
| 导出快照 | `export-history-snapshot` | 只读 CST，写本地快照 JSON |
| 列出流水 | `list-history-log` | 只读本地日志 |
| 比较快照 | `diff-history-snapshots` | 只读，展示原始 VBA diff |
| 创建轻量检查点 | `create-history-checkpoint` | 写本地 checkpoint，不复制工程 |
| 创建物理检查点 | `create-project-checkpoint` | 保存并关闭目标工程，确认解锁后复制完整工程 |
| 生成恢复计划 | `generate-restore-plan` | 只读分析，不重放 |
| 在副本中重放 | `checkout-replay-copy` | 保存并关闭基线，在新副本逐步写入 CST |
| 人工对齐歧义 | `reconcile-history-operation` | 写审计结论，不自动改变 CST History |

物理检查点、重放副本和 reconciliation 均为 CLI-only；执行前向用户说明源工程、目标副本、关闭行为和失败后的保留位置。

## 重放判定

- 基线等于目标：`already_at_target`；
- 基线是目标的严格前缀：只计划并重放缺失后缀；
- 基线比目标更长：不能正向回退，选择更早物理检查点；
- 两者分叉：禁止向基线继续追加，从共同基线的物理副本恢复。

每步执行前校验 expected-before 哈希，执行后校验 expected-after 哈希；不匹配立即停止并保留副本。

## MCP 交互和工作笔记

| 目的 | 工具 |
| --- | --- |
| 查询工具请求/返回生命周期 | `list-interaction-log` |
| 查看一次 interaction 的 operation、前后快照和 diff | `inspect-interaction-history` |
| 显式记录计划、决定、用户确认或阶段结论 | `record-agent-note` |
| 查询工作笔记 | `list-agent-notes` |

大型请求、结果或错误可以外置到内容寻址 payload 文件。MCP 日志不包含 Agent 完整聊天或隐藏推理；Agent note 只保存主动提交的可见文本。

## 最小安全流程

```text
inspect-history-status
→ export-history-snapshot
→ diff-history-snapshots（需要比较时）
→ create-history-checkpoint
→ 一个业务修改
→ 再导出 snapshot 并检查 interaction
```

需要回退时先生成 restore plan；只有用户审查计划后，才创建物理副本并重放。
