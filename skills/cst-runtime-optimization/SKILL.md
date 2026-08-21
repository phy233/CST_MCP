---
name: cst-runtime-optimization
description: 使用 CST Runtime 或 MCP 分步骤执行参数优化、灵敏度探测、多轮仿真对比和早停判断。用户要求优化 S 参数、幅相、增益、带宽或超表面指标时使用；单次仿真、纯建模或尚未明确目标和参数范围时不使用。
---

# CST Runtime 优化 Skill

本 Skill 负责优化决策和逐轮记录，不复制 Runtime 工具实现。MCP 调用遵守 `cst-mcp`，直接 CLI 调用遵守 `cst-runtime-cli`，超表面物理判断遵守 `cst-metasurface-design`。

## 默认流程

1. 检查工作副本、当前参数和基线结果；
2. 与用户确认目标函数、方向、阈值、变量范围、约束、预算和停止条件；
3. 需要时先做少量探针或灵敏度分析；
4. 每轮只生成并审查一个候选；
5. 修改参数并确认实际生效；
6. 运行仿真，读取并验证目标结果；
7. 将结果反馈给优化器并记录 trial；
8. 立即判断达标、无改进、越界、失败或继续。

完整规则见 [optimization-loop.md](references/optimization-loop.md)，任务卡和记录要求见 [task-and-records.md](references/task-and-records.md)。

## 原子步骤优先

默认把候选生成、改参、验证、求解、结果读取、目标计算和 `tell` 分开，使用户能够在每轮调整参数范围、目标或停止条件。

`run-probe-phase`、`run-optimization-step`、`prepare-experiment` 和 `run-experiment` 仅是可选管道。只有用户明确接受、步骤已经展开且无需中间决策时才使用。

## 结果边界

- 每个 trial 必须关联工程副本、参数、Run ID、结果来源、目标值和状态；
- 目标计算使用明确公式和单位，S 参数先确认复数/线性/dB 表示；
- 没有新 Run ID、结果为空、日志含错误或结果来源不明时，该 trial 记为失败或未验证，不能反馈为有效观测；
- 不能只保存初始点和最佳点，失败样本和被拒绝样本也要保留原因；
- 当前仓库没有代理模型训练与模型版本管理能力，不在本 Skill 中承诺相关产物。

## 停止条件

满足任一条件就停止并报告：达到目标、预算耗尽、连续无改进、候选违反约束、仿真状态不明确、History ambiguous、结果验证失败或用户要求停止。

最终报告包含最佳有效 trial、与基线的对比、失败/未验证数量、停止原因、结果与日志路径，以及是否仍需真机或人工检查。
