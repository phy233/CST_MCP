---
name: cst-metasurface-design
description: 使用 CST 分步骤设计、修改、仿真或诊断超表面、频率选择表面、周期单元、反射阵列和透射阵列。任务涉及单元结构、周期边界、Floquet 端口、平面波、复数 S 参数、幅相或极化转换时使用；普通 RF 理论讨论且不涉及 CST 工程时不要触发。
---

# CST 超表面设计 Skill

本 Skill 负责电磁设计判断，不负责替代 MCP 或 Runtime CLI。优先使用当前环境已经提供的 CST MCP 工具；只有用户明确要求 CLI 或操作被限制为 CLI-only 时，才走 Runtime CLI。

## 默认工作方式

采用可检查的小步循环：

1. 明确目标和结构类型；
2. 只读检查当前工程；
3. 提出一个物理假设和本步修改；
4. 用户可见地确认关键输入；
5. 只执行这一小步；
6. 检查实体、参数、配置或结果是否真实变化；
7. 记录 History、快照和设计结论；
8. 再决定下一步。

不要把建模、边界、端口、求解和结果解释封装成不可调整的一键流程。管道仅在用户明确选择且其展开步骤、输入和停止条件均可见时使用。

## 任务路由

- 新建或理解超表面工程：先读 [requirements-and-physics-gates.md](references/requirements-and-physics-gates.md)。
- 修改几何、参数、材料或单元拓扑：读 [geometry-and-history.md](references/geometry-and-history.md)。
- 设置激励、求解或解释结果：读 [simulation-and-result-validation.md](references/simulation-and-result-validation.md)。
- 多轮演化、对比或恢复：读 [design-iteration.md](references/design-iteration.md)。

只读取当前任务所需的 reference，不要一次加载全部资料。

## 关键边界

- 无限周期单元通常使用 Unit Cell/Periodic 边界与 Floquet 端口；有限结构的 Plane Wave 仿真通常产生散射、场或 RCS 结果，不能据此承诺普通端口 S 参数。
- `add_to_history()`、状态文件 `OK` 或 MCP `status=success` 只证明对应提交边界成功；关键写操作仍要检查实体、参数、配置、结果节点或非空文件。
- 不凭经验猜测 CST VBA。陌生对象和方法先核对目标 CST 版本的本机 Online Help，再参考已验证代码。
- 默认操作工作副本。物理检查点和重放只在显式工程路径、明确用户授权和现有安全工具支持下执行。
- MCP 自动日志只覆盖工具请求与返回；设计假设、用户确认和阶段结论通过 `record-agent-note` 显式记录，不声称保存隐藏推理。

## 阶段输出

每一步向用户报告：本步目标、依据、实际调用、验证证据、History/interaction 关联、未验证项和建议的下一步。没有证据时使用“已提交”“待验证”或“仿真数据未验证”，不要写成“设计成功”。
