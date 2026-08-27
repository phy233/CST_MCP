# Registry 元数据中文补充工作稿（临时）

> 状态：等待人工填写。此文件是从当前 Registry 自动整理的临时工作稿，不是最终接口文档。
> 请只修改各工具的“待补充信息”，已有信息用于核对当前代码事实。填写完成后交回，由 Agent 统一压缩、润色、翻译，并写回 Registry 代码。

## 使用说明

- 当前清单包含 `137` 个 `exposure=agent` 工具。
- 已有工具说明按 Registry 原文保留；英文原文无需在本阶段自行翻译。
- 所有待补充内容请使用简体中文，尽量写事实、边界和可观察结果，不写宣传性表述。
- 普通 CST/VBA 写入在接口返回成功后应充分信任，不要求重复执行前检查或执行后读回；导出文件、异步求解和错误状态不明确等必要操作除外。
- 不要修改工具名、参数名、风险值或现有说明；如果发现它们有问题，请写在“其他备注”。
- 相似工具必须说明区别。例如同步/异步求解、结果枚举/结果导出、普通边界/Unit Cell 边界、模型会话/结果工程读取。

## 待补充字段说明

每个工具需要补充以下内容：

1. **中文标题**：面向用户的简短动作名称。
2. **用户目标**：用户希望得到什么结果，不描述内部函数实现。
3. **何时使用**：能够触发该工具的任务场景。
4. **不要用于**：与相似工具的区别、禁止场景或重要限制。
5. **前置条件**：调用前必须已经具备的工程、会话、实体、结果节点、Run ID 或文件。
6. **副作用**：会修改什么、写出什么文件、是否启动或停止求解器。只读工具写“无”。
7. **成功后的重试规则**：成功后是否可重复调用。写入和长任务通常应明确“成功后不要重复执行”。
8. **关联工具**：常见前一步、替代工具和后一步。
9. **成功返回摘要**：Agent 后续真正需要读取的稳定业务字段。
10. **失败处理**：哪些错误可调整参数后重试，哪些情况必须停止并询问用户。
11. **参数补充**：为当前缺少说明的参数补充含义、单位、坐标参考、允许值、互斥关系和例子。
12. **检索关键词**：中文、英文和 CST 术语，用于后续工具搜索。

## 当前分类概览

| Registry 分类 | 中文含义 | Agent 工具数 |
| --- | --- | ---: |
| `audit` | 审计记录 | 3 |
| `farfield` | 远场结果 | 4 |
| `history` | CST History | 3 |
| `interaction` | Agent 交互记录 | 4 |
| `modeling` | 几何与建模 | 37 |
| `optimization` | 扫参与优化 | 11 |
| `project_identity` | 工程身份与锁定状态 | 4 |
| `project_ops` | 工程配置与求解控制 | 35 |
| `results` | 结果发现、读取与导出 | 22 |
| `run` | 任务与运行目录 | 2 |
| `session_manager` | CST 会话管理 | 6 |
| `simulation` | 仿真工作流 | 1 |
| `workflow` | 复合工作流 | 2 |
| `workspace` | Runtime 工作区 | 3 |

## 审计记录（`audit`，3 个）

### `record-stage`

**已有信息**

- 当前分类：`audit`（审计记录）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Write a stage record and production-chain log entry.
- 必填参数：`task_path`、`run_id`、`stage`、`status`、`message`、`details_json`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`task_path`、`run_id`、`stage`、`status`、`message`、`details_json`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `stage-evidence`

**已有信息**

- 当前分类：`audit`（审计记录）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Capture CST project state snapshots and generate before/after comparison reports. Use --capture to snapshot, --compare to diff two snapshots into HTML.
- 必填参数：`project_path`、`capture`、`stage_name`、`output_dir`、`compare`、`output_html`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`capture`、`stage_name`、`output_dir`、`compare`、`output_html`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `update-status`

**已有信息**

- 当前分类：`audit`（审计记录）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Update the formal run status.json file.
- 必填参数：`task_path`、`run_id`、`status`、`stage`、`best_result_json`、`output_files_json`、`error_json`、`extra_json`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`task_path`、`run_id`、`status`、`stage`、`best_result_json`、`output_files_json`、`error_json`、`extra_json`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## 远场结果（`farfield`，4 个）

### `calculate-farfield-neighborhood-flatness`

**已有信息**

- 当前分类：`farfield`（远场结果）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Calculate near-boresight farfield cut flatness from exported cut JSON payloads.
- 必填参数：`file_paths`、`theta_max_deg`、`output_json`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`file_paths`、`theta_max_deg`、`output_json`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `export-farfield-cut`

**已有信息**

- 当前分类：`farfield`（远场结果）
- 当前风险：`long-running`（长时间运行）
- 当前说明（Registry 原文）：Export an existing CST Farfield Cut tree item to JSON under {export_dir}/farfield/cuts/.
- 必填参数：`project_path`、`tree_path`、`export_dir`、`fresh_session`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`tree_path`、`export_dir`、`fresh_session`
- 当前声明的业务输出字段：`project_path`、`output_path`、`output_file`、`file_size`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `export-farfield-grid`

**已有信息**

- 当前分类：`farfield`（远场结果）
- 当前风险：`long-running`（长时间运行）
- 当前说明（Registry 原文）：Compute a compatible farfield scalar grid and export as JSON under {export_dir}/farfield/. Supports fresh_session reuse.
- 必填参数：`project_path`、`farfield_name`、`export_dir`、`quantity`、`theta_step_deg`、`phi_step_deg`、`theta_min_deg`、`theta_max_deg`、`phi_min_deg`、`phi_max_deg`、`run_id`、`fresh_session`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`farfield_name`、`export_dir`、`quantity`、`theta_step_deg`、`phi_step_deg`、`theta_min_deg`、`theta_max_deg`、`phi_min_deg`、`phi_max_deg`、`run_id`、`fresh_session`
- 当前声明的业务输出字段：`project_path`、`output_path`、`output_file`、`file_size`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `inspect-farfield-monitors`

**已有信息**

- 当前分类：`farfield`（远场结果）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Discover farfield monitors from a CST project by scanning the result tree.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## CST History（`history`，3 个）

### `diff-history-snapshots`

**已有信息**

- 当前分类：`history`（CST History）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：比较任意两个 History 快照并输出块级增删改及原始 VBA 统一 diff。
- 必填参数：`before_snapshot_id`、`after_snapshot_id`
- 可选参数：`project_path`
- 已有参数说明：无
- 尚缺参数说明：`before_snapshot_id`、`after_snapshot_id`、`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `generate-restore-plan`

**已有信息**

- 当前分类：`history`（CST History）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：纯只读分析基线工程与目标快照的严格前缀关系并生成重放计划。
- 必填参数：`baseline_project_path`、`target_snapshot_id`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`baseline_project_path`、`target_snapshot_id`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-history-log`

**已有信息**

- 当前分类：`history`（CST History）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：查询 CST History 操作记录流水与快照哈希变更。
- 必填参数：无
- 可选参数：`project_path`、`execution_state`、`reconciliation_state`、`limit`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`execution_state`、`reconciliation_state`、`limit`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## Agent 交互记录（`interaction`，4 个）

### `inspect-interaction-history`

**已有信息**

- 当前分类：`interaction`（Agent 交互记录）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：查询单次 MCP 工具调用关联的 History 快照及 Operation 详细变更。
- 必填参数：`interaction_id`
- 可选参数：`workspace`、`project_path`
- 已有参数说明：`workspace`、`project_path`
- 尚缺参数说明：`interaction_id`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-agent-notes`

**已有信息**

- 当前分类：`interaction`（Agent 交互记录）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：查询已持久化的 Agent 显式工作说明与人工处置笔记列表。
- 必填参数：无
- 可选参数：`task_id`、`run_id`、`project_path`、`category`、`limit`
- 已有参数说明：`project_path`
- 尚缺参数说明：`task_id`、`run_id`、`category`、`limit`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-interaction-log`

**已有信息**

- 当前分类：`interaction`（Agent 交互记录）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：查询 MCP 工具调用的全生命周期交互日志流。
- 必填参数：无
- 可选参数：`workspace`、`project_path`、`task_id`、`run_id`、`tool_name`、`interaction_id`、`limit`
- 已有参数说明：`workspace`、`project_path`
- 尚缺参数说明：`task_id`、`run_id`、`tool_name`、`interaction_id`、`limit`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `record-agent-note`

**已有信息**

- 当前分类：`interaction`（Agent 交互记录）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：显式记录 Agent 或用户的阶段工作说明、关键设计决策或人工处置结论。
- 必填参数：`content`
- 可选参数：`category`、`task_id`、`run_id`、`project_path`、`user_confirmed`、`interaction_id`、`operation_id`、`snapshot_id`
- 已有参数说明：`project_path`
- 尚缺参数说明：`content`、`category`、`task_id`、`run_id`、`user_confirmed`、`interaction_id`、`operation_id`、`snapshot_id`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## 几何与建模（`modeling`，37 个）

### `boolean-add`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Unite two solids (boolean union).
- 必填参数：`project_path`、`shape1`、`shape2`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`shape1`、`shape2`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `boolean-insert`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Insert one solid into another (boolean insert).
- 必填参数：`project_path`、`shape1`、`shape2`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`shape1`、`shape2`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `boolean-intersect`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Intersect two solids (boolean intersection).
- 必填参数：`project_path`、`shape1`、`shape2`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`shape1`、`shape2`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `boolean-subtract`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Subtract one solid from another (boolean difference). CST may accept a subtraction between non-intersecting solids without changing the target, so confirm geometric overlap from the modeled coordinates before calling.
- 必填参数：`project_path`、`target`、`tool`
- 可选参数：无
- 已有参数说明：`target`、`tool`
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `change-material`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Change the material of a geometry entity. Use list-materials to see available names.
- 必填参数：`project_path`、`shape_name`、`material`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`shape_name`、`material`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `create-component`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create a new component in the CST project.
- 必填参数：`project_path`、`component_name`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`component_name`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `create-hollow-sweep`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create a hollow loft between two rectangular profiles in active X/Y/Z or local U/V/W coordinates.
- 必填参数：`project_path`、`name`、`component`、`material`、`x_min1`、`x_max1`、`y_min1`、`y_max1`、`z1`、`x_min2`、`x_max2`、`y_min2`、`y_max2`、`z2`、`wall_thickness`
- 可选参数：无
- 已有参数说明：`x_min1`、`x_max1`、`y_min1`、`y_max1`、`z1`、`x_min2`、`x_max2`、`y_min2`、`y_max2`、`z2`
- 尚缺参数说明：`project_path`、`name`、`component`、`material`、`wall_thickness`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `create-horn-segment`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create a Z-axis horn segment; Z means W when a local WCS is active.
- 必填参数：`project_path`、`segment_id`、`bottom_radius`、`top_radius`、`z_min`、`z_max`
- 可选参数：无
- 已有参数说明：`z_min`、`z_max`
- 尚缺参数说明：`project_path`、`segment_id`、`bottom_radius`、`top_radius`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `create-loft-sweep`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create a loft between two rectangular profiles in active X/Y/Z or local U/V/W coordinates.
- 必填参数：`project_path`、`name`、`component`、`material`、`x_min1`、`x_max1`、`y_min1`、`y_max1`、`z1`、`x_min2`、`x_max2`、`y_min2`、`y_max2`、`z2`
- 可选参数：无
- 已有参数说明：`x_min1`、`x_max1`、`y_min1`、`y_max1`、`z1`、`x_min2`、`x_max2`、`y_min2`、`y_max2`、`z2`
- 尚缺参数说明：`project_path`、`name`、`component`、`material`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `create-mesh-group`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create a mesh group and add items.
- 必填参数：`project_path`、`group_name`、`items`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`group_name`、`items`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-analytical-curve`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create a parametric curve in active X/Y/Z or local U/V/W coordinates; each law must be differentiable over the parameter range.
- 必填参数：`project_path`、`name`、`curve`、`law_x`、`law_y`、`law_z`、`param_start`、`param_end`
- 可选参数：无
- 已有参数说明：`law_x`、`law_y`、`law_z`
- 尚缺参数说明：`project_path`、`name`、`curve`、`param_start`、`param_end`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-brick`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create a brick in active X/Y/Z or local U/V/W coordinates.
- 必填参数：`project_path`、`name`、`component`、`material`、`x_min`、`x_max`、`y_min`、`y_max`、`z_min`、`z_max`
- 可选参数：无
- 已有参数说明：`x_min`、`x_max`、`y_min`、`y_max`、`z_min`、`z_max`
- 尚缺参数说明：`project_path`、`name`、`component`、`material`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-cone`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create a cone along an active X/U, Y/V, or Z/W axis. axis_min/axis_max set the axial range; the two transverse centers are mapped to axis-specific VBA setters. bottom_radius is at the lower bound and top_radius at the upper bound.
- 必填参数：`project_path`、`name`、`component`、`material`、`bottom_radius`、`top_radius`、`axis`、`axis_min`、`axis_max`、`x_center`、`y_center`
- 可选参数：无
- 已有参数说明：`axis`、`axis_min`、`axis_max`、`x_center`、`y_center`
- 尚缺参数说明：`project_path`、`name`、`component`、`material`、`bottom_radius`、`top_radius`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-cylinder`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create a cylinder along an active X/U, Y/V, or Z/W axis. axis_min/axis_max set the axial range; the two transverse centers are mapped to axis-specific VBA setters.
- 必填参数：`project_path`、`name`、`component`、`material`、`outer_radius`、`inner_radius`、`axis`、`axis_min`、`axis_max`、`x_center`、`y_center`
- 可选参数：无
- 已有参数说明：`axis`、`axis_min`、`axis_max`、`x_center`、`y_center`
- 尚缺参数说明：`project_path`、`name`、`component`、`material`、`outer_radius`、`inner_radius`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-extrude-curve`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Extrude a closed planar curve. Positive thickness follows its ordered normal (CST 2022 real-machine verified); negative reverses it. Compute the normal and sign first.
- 必填参数：`project_path`、`name`、`component`、`material`、`curve`、`thickness`
- 可选参数：无
- 已有参数说明：`curve`、`thickness`
- 尚缺参数说明：`project_path`、`name`、`component`、`material`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-farfield-monitor`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：按 CST 2022 Monitor Object 为每个频率创建独立单频远场监视器，并读回名称、类型、域和频率验证；子体积完全可选，不含模型专用默认坐标。
- 必填参数：`project_path`、`name`、`frequencies`
- 可选参数：`enable_nearfield`、`subvolume`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`name`、`frequencies`、`enable_nearfield`、`subvolume`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-loft`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Connect two pre-picked surfaces; CST 2022 defines no separate plane-normal argument.
- 必填参数：`project_path`、`name`、`component`、`material`、`tangency`、`minimize_twist`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`name`、`component`、`material`、`tangency`、`minimize_twist`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-material-from-mtd`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Define a CST material from .mtd file by material name. Material must exist in references/Materials/. Use list-materials to see available names.
- 必填参数：`project_path`、`material_name`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`material_name`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-polygon-3d`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create ordered points in active X/Y/Z or local U/V/W coordinates. For extrusion, close the loop, verify coplanarity, and compute its ordered normal.
- 必填参数：`project_path`、`name`、`curve`、`points`
- 可选参数：无
- 已有参数说明：`points`
- 尚缺参数说明：`project_path`、`name`、`curve`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-rectangle`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create a rectangle in the active XY or local UV plane; calculate bounds in that coordinate system first.
- 必填参数：`project_path`、`name`、`curve`、`x_min`、`x_max`、`y_min`、`y_max`
- 可选参数：无
- 已有参数说明：`x_min`、`x_max`、`y_min`、`y_max`
- 尚缺参数说明：`project_path`、`name`、`curve`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-units`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Set the CST project unit system.
- 必填参数：`project_path`、`length`、`frequency`
- 可选参数：`temperature`
- 已有参数说明：`temperature`
- 尚缺参数说明：`project_path`、`length`、`frequency`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `delete-entity`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Delete a geometry entity from the CST project.
- 必填参数：`project_path`、`component`、`name`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`component`、`name`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `delete-monitor`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Delete a monitor by name.
- 必填参数：`project_path`、`monitor_name`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`monitor_name`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `delete-probe`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Delete a probe by its ID.
- 必填参数：`project_path`、`probe_id`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`probe_id`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-entities`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：List geometry entities from the verified CST working project.
- 必填参数：`project_path`、`component`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`component`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-materials`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：List available CST material names from the Materials library.
- 必填参数：无
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：无
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `pick-face`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Select a face by ID for loft operations (zero-thickness entities only).
- 必填参数：`project_path`、`component`、`name`、`face_id`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`component`、`name`、`face_id`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `rename-entity`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Rename a geometry entity.
- 必填参数：`project_path`、`old_name`、`new_name`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`old_name`、`new_name`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `set-background-with-space`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Add distances to the global X/Y/Z bounds of the calculation volume.
- 必填参数：`project_path`
- 可选参数：`x_min_space`、`x_max_space`、`y_min_space`、`y_max_space`、`z_min_space`、`z_max_space`
- 已有参数说明：`x_min_space`、`x_max_space`、`y_min_space`、`y_max_space`、`z_min_space`、`z_max_space`
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `set-efield-monitor`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：设置 E-field 监视器；CST 2022 只支持单频，start_freq 必须等于 end_freq。
- 必填参数：`project_path`、`start_freq`、`end_freq`、`step`
- 可选参数：无
- 已有参数说明：`start_freq`、`end_freq`
- 尚缺参数说明：`project_path`、`step`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `set-entity-color`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Set the display color of a geometry entity.
- 必填参数：`project_path`、`shape_name`、`r`、`g`、`b`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`shape_name`、`r`、`g`、`b`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `set-farfield-plot-cuts`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Set farfield plot cut angles.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `set-field-monitor`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：设置 E/H 场监视器；CST 2022 只支持单频。
- 必填参数：`project_path`、`field_type`、`start_frequency`、`end_frequency`、`num_samples`
- 可选参数：无
- 已有参数说明：`start_frequency`、`end_frequency`、`num_samples`
- 尚缺参数说明：`project_path`、`field_type`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `set-probe`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Set an internal E/H-field probe at a global X/Y/Z position.
- 必填参数：`project_path`、`field_type`、`x_pos`、`y_pos`、`z_pos`
- 可选参数：无
- 已有参数说明：`x_pos`、`y_pos`、`z_pos`
- 尚缺参数说明：`project_path`、`field_type`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `show-bounding-box`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Toggle bounding box display.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `transform-curve`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Mirror a curve using Center and PlaneNormal in active X/Y/Z or local U/V/W coordinates; compute both first.
- 必填参数：`project_path`、`curve_name`、`center_x`、`center_y`、`center_z`、`plane_normal_x`、`plane_normal_y`、`plane_normal_z`
- 可选参数：无
- 已有参数说明：`center_x`、`center_y`、`center_z`、`plane_normal_x`、`plane_normal_y`、`plane_normal_z`
- 尚缺参数说明：`project_path`、`curve_name`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `transform-shape`

**已有信息**

- 当前分类：`modeling`（几何与建模）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Mirror uses PlaneNormal; rotate uses Angle. Center and components use active X/Y/Z or local U/V/W coordinates. Required plane_normal fields do not define a rotate axis.
- 必填参数：`project_path`、`shape_name`、`transform_type`、`center_x`、`center_y`、`center_z`、`plane_normal_x`、`plane_normal_y`、`plane_normal_z`
- 可选参数：`angle_x`、`angle_y`、`angle_z`、`multiple_objects`、`group_objects`、`repetitions`、`destination`
- 已有参数说明：`transform_type`、`center_x`、`center_y`、`center_z`、`plane_normal_x`、`plane_normal_y`、`plane_normal_z`、`angle_x`、`angle_y`、`angle_z`、`multiple_objects`、`group_objects`、`repetitions`、`destination`
- 尚缺参数说明：`project_path`、`shape_name`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## 扫参与优化（`optimization`，11 个）

### `analyze-probes`

**已有信息**

- 当前分类：`optimization`（扫参与优化）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Analyze probe results: compute main effects and two-way interactions. Input must include the parameter values and the objective value for each probe.
- 必填参数：`parameters`、`probes`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`parameters`、`probes`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `ask-study`

**已有信息**

- 当前分类：`optimization`（扫参与优化）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Ask the study for the next trial parameter suggestion.
- 必填参数：`storage_path`、`study_name`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`storage_path`、`study_name`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `best-study`

**已有信息**

- 当前分类：`optimization`（扫参与优化）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Get current best result. For multi-objective returns Pareto front samples.
- 必填参数：`storage_path`、`study_name`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`storage_path`、`study_name`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `create-study`

**已有信息**

- 当前分类：`optimization`（扫参与优化）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Create or load an Optuna optimization study. Supports single-objective, multi-objective (directions), and constraint-enabled studies.
- 必填参数：`storage_path`、`study_name`、`parameters`、`direction`、`directions`、`value_names`、`constraints`、`sampler`、`n_startup_trials`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`storage_path`、`study_name`、`parameters`、`direction`、`directions`、`value_names`、`constraints`、`sampler`、`n_startup_trials`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `design-probes`

**已有信息**

- 当前分类：`optimization`（扫参与优化）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Design a Plackett-Burman probe plan to screen parameters. Returns a list of experiments; run each via prepare-experiment + run-experiment, then feed results to analyze-probes.
- 必填参数：`parameters`、`max_probes`、`include_center`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`parameters`、`max_probes`、`include_center`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `run-optimization-step`

**已有信息**

- 当前分类：`optimization`（扫参与优化）
- 当前风险：`long-running`（长时间运行）
- 当前说明（Registry 原文）：Run one optimization iteration: ask Optuna for next parameters, apply them, simulate, compute objective, and report back. Agent inspects the objective_value output to decide whether to stop or continue the loop.
- 必填参数：`project_path`、`completion_result_paths`、`study_storage`、`study_name`
- 可选参数：`objective`、`sampler`
- 已有参数说明：`project_path`、`completion_result_paths`、`study_storage`、`study_name`、`objective`、`sampler`
- 尚缺参数说明：无
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `run-probe-phase`

**已有信息**

- 当前分类：`optimization`（扫参与优化）
- 当前风险：`long-running`（长时间运行）
- 当前说明（Registry 原文）：Run the complete probe phase: design Plackett-Burman probes, simulate each, analyze main effects and interactions, then inject results into an Optuna study. The working.cst is copied to working_probe.cst for isolation; exports go to exports/probe/. Returns top_params, edge_hit, and suggested_algorithm. Supports objective parameter to customize the objective function (default: s11_min_db).
- 必填参数：`project_path`、`completion_result_paths`、`parameters`、`study_storage`、`study_name`
- 可选参数：`max_probes`、`include_center`、`objective`
- 已有参数说明：`project_path`、`completion_result_paths`、`parameters`、`study_storage`、`study_name`、`max_probes`、`include_center`、`objective`
- 尚缺参数说明：无
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `study-add-trials`

**已有信息**

- 当前分类：`optimization`（扫参与优化）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Inject pre-computed trials (e.g. from manual grid scan) into a study. Each trial: {params, values, constraints?}.
- 必填参数：`storage_path`、`study_name`、`trials`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`storage_path`、`study_name`、`trials`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `study-param-importances`

**已有信息**

- 当前分类：`optimization`（扫参与优化）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Analyze which parameters most affect the objective. Requires at least 5 completed trials.
- 必填参数：`storage_path`、`study_name`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`storage_path`、`study_name`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `study-terminate-check`

**已有信息**

- 当前分类：`optimization`（扫参与优化）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Check if optimization has converged using Optuna's regret-bound evaluator. Returns should_terminate.
- 必填参数：`storage_path`、`study_name`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`storage_path`、`study_name`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `tell-study`

**已有信息**

- 当前分类：`optimization`（扫参与优化）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Report trial result. Supports single value, multi-objective values array, and optional constraints.
- 必填参数：`storage_path`、`study_name`、`trial_number`、`value`、`values`、`constraints`、`state`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`storage_path`、`study_name`、`trial_number`、`value`、`values`、`constraints`、`state`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## 工程身份与锁定状态（`project_identity`，4 个）

### `infer-run-dir`

**已有信息**

- 当前分类：`project_identity`（工程身份与锁定状态）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Infer run_dir from a projects/working.cst project path.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-open-projects`

**已有信息**

- 当前分类：`project_identity`（工程身份与锁定状态）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：List CST projects visible through DesignEnvironment.connect_to_any().
- 必填参数：无
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：无
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `verify-project-identity`

**已有信息**

- 当前分类：`project_identity`（工程身份与锁定状态）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Verify the expected project is the sole open CST project before writes.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `wait-project-unlocked`

**已有信息**

- 当前分类：`project_identity`（工程身份与锁定状态）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Wait for a project companion directory to have no .lok files.
- 必填参数：`project_path`、`timeout_seconds`、`poll_interval_seconds`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`timeout_seconds`、`poll_interval_seconds`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## 工程配置与求解控制（`project_ops`，35 个）

### `capture-3d-view`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Export the current 3D sheet to PNG. Use a CST reserved view or relative horizontal/vertical rotations from Front.
- 必填参数：`project_path`
- 可选参数：`output_dir`、`filename_prefix`、`view_type`、`preset_name`、`horizontal_rotation_deg`、`vertical_rotation_deg`、`return_image_data`
- 已有参数说明：`project_path`、`output_dir`、`filename_prefix`、`view_type`、`preset_name`、`horizontal_rotation_deg`、`vertical_rotation_deg`、`return_image_data`
- 尚缺参数说明：无
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `change-parameter`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Change one CST parameter in the verified working project.
- 必填参数：`project_path`、`name`、`value`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`name`、`value`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `change-solver-type`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Change the CST solver type.
- 必填参数：`project_path`、`solver_type`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`solver_type`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `configure-frequency-domain-solver`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：仅切换 HF Frequency Domain、设置 mesh_method 和激励；不会生成 FDSolver.Reset，也不改精度、扫频或自适应设置。
- 必填参数：`project_path`、`mesh_method`、`excitation`
- 可选参数：无
- 已有参数说明：`project_path`、`excitation`
- 尚缺参数说明：`mesh_method`
- 当前声明的业务输出字段：`project_path`、`submission`、`execution`、`solver_type`、`mesh_method`、`excitation`、`untouched_settings`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-background`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：设置背景类型与材料参数（Normal 时显式写出 ε/μ，默认 1.0/1.0 等价 Vacuum）。CST 2022 手册的 Background 对象无读取接口，因此返回 requested 值与 farfield_compatible 判定（基于请求值），并把状态登记为运行时跟踪，供 get-background 返回；无法读回 GUI 中的修改。
- 必填参数：`project_path`
- 可选参数：`background_type`、`epsilon`、`mu`
- 已有参数说明：`background_type`、`epsilon`、`mu`
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-boundary`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：设置全部面的通用边界和对称性；该工具不等价于完整的 Unit Cell 或 Floquet 配置。高级周期边界需求应由用户在 CST 图形界面中手动完成。
- 必填参数：`project_path`
- 可选参数：`face_type`、`symmetry_type`
- 已有参数说明：`face_type`、`symmetry_type`
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-fdsolver-stimulation`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：依据本机 CST 2022 FDSolver.Stimulation 手册设置激励，不会隐式执行 FDSolver.Reset。该工具可由 MCP Agent 调用，但暴露状态不代表已完成 CST 2022 实机验收。
- 必填参数：`project_path`、`port`、`mode`
- 可选参数：无
- 已有参数说明：`port`、`mode`
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-floquet-port`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：配置 Zmin/Zmax Floquet 端口、显式或自动模式、参考面、极化基础和排序。仅公开 getter 可读字段会被验收。
- 必填参数：`project_path`、`ports`
- 可选参数：`polarization_basis`、`sort_code`、`sort_frequency`、`sort_theta`、`sort_phi`、`max_order_x`、`max_order_yprime`
- 已有参数说明：`project_path`
- 尚缺参数说明：`ports`、`polarization_basis`、`sort_code`、`sort_frequency`、`sort_theta`、`sort_phi`、`max_order_x`、`max_order_yprime`
- 当前声明的业务输出字段：`project_path`、`submission`、`execution`、`requested`、`actual`、`unverified_fields`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-frequency-range`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Set the simulation frequency range.
- 必填参数：`project_path`、`start_freq`、`end_freq`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`start_freq`、`end_freq`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-mesh`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Configure the hexahedral mesh parameters.
- 必填参数：`project_path`、`steps_per_wave_near`、`steps_per_wave_far`、`steps_per_box_near`、`steps_per_box_far`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`steps_per_wave_near`、`steps_per_wave_far`、`steps_per_box_near`、`steps_per_box_far`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-parameters`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Batch-define multiple CST parameters using StoreParameters.
- 必填参数：`project_path`、`names`、`values`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`names`、`values`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-plane-wave`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：创建真实 PlaneWave 源。普通平面波不产生 S 参数；无限周期单元应使用 Unit Cell 与 Floquet。
- 必填参数：`project_path`、`normal`、`e_vector`
- 可选参数：`polarization`、`reference_frequency`、`handedness`、`phase_difference`、`axial_ratio`
- 已有参数说明：`project_path`
- 尚缺参数说明：`normal`、`e_vector`、`polarization`、`reference_frequency`、`handedness`、`phase_difference`、`axial_ratio`
- 当前声明的业务输出字段：`project_path`、`submission`、`execution`、`requested`、`actual`、`unverified_fields`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-port`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Define an internal axis-aligned waveguide port from global X/Y/Z ranges. Collapse the normal-axis range to the port plane; *min radiates +axis and *max radiates -axis.
- 必填参数：`project_path`、`port_number`、`x_min`、`x_max`、`y_min`、`y_max`、`z_min`、`z_max`、`orientation`
- 可选参数：无
- 已有参数说明：`x_min`、`x_max`、`y_min`、`y_max`、`z_min`、`z_max`、`orientation`
- 尚缺参数说明：`project_path`、`port_number`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-solver`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Configure the time-domain solver settings.
- 必填参数：`project_path`、`stimulation_port`、`steady_state_limit`、`norming_impedance`
- 可选参数：`stimulation_mode`、`mesh_adaption`、`auto_norm_impedance`、`calculate_modes_only`、`s_para_symmetry`、`store_td_results`、`run_discretizer_only`、`full_deembedding`、`superimpose_plw`、`use_sensitivity`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`stimulation_port`、`stimulation_mode`、`steady_state_limit`、`norming_impedance`、`mesh_adaption`、`auto_norm_impedance`、`calculate_modes_only`、`s_para_symmetry`、`store_td_results`、`run_discretizer_only`、`full_deembedding`、`superimpose_plw`、`use_sensitivity`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `define-unit-cell-boundary`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：按 CST 2022 手册配置六面边界和 Unit Cell 扫描角；先校验 X/Y 配对，执行后再通过 getter 读回。
- 必填参数：`project_path`、`xmin`、`xmax`、`ymin`、`ymax`、`zmin`、`zmax`
- 可选参数：`theta`、`phi`、`direction`
- 已有参数说明：`project_path`
- 尚缺参数说明：`xmin`、`xmax`、`ymin`、`ymax`、`zmin`、`zmax`、`theta`、`phi`、`direction`
- 当前声明的业务输出字段：`project_path`、`submission`、`execution`、`requested`、`actual`、`unverified_fields`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `get-background`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：返回本会话运行时跟踪的背景状态（source=runtime_tracked）与 farfield_compatible 判定（远场监视器要求 Normal 且 ε=1、μ=1）。CST 2022 手册的 Background 对象未提供任何读取接口，本工具不调用未文档化的属性读取；没有跟踪状态时返回 background_state_unknown，需先调用 define-background 显式设置背景。
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `inspect-boundary`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：使用 Boundary 六面 getter 和 GetUnitCellScanAngle 读取实际边界状态。
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：`project_path`
- 尚缺参数说明：无
- 当前声明的业务输出字段：`project_path`、`faces`、`unit_cell_scan`、`ports`、`plane_wave`、`monitors`、`count`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `inspect-floquet-ports`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：读取 Floquet 端口位置、模式序号/名称、模式列表及考虑模式数；不伪造无 getter 字段。
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：`project_path`
- 尚缺参数说明：无
- 当前声明的业务输出字段：`project_path`、`faces`、`unit_cell_scan`、`ports`、`plane_wave`、`monitors`、`count`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `inspect-model-view`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Export a documented preset or Front-relative 3D view and return the PNG as base64.
- 必填参数：`project_path`
- 可选参数：`output_dir`、`filename_prefix`、`view_type`、`preset_name`、`horizontal_rotation_deg`、`vertical_rotation_deg`
- 已有参数说明：`project_path`、`output_dir`、`view_type`、`preset_name`、`horizontal_rotation_deg`、`vertical_rotation_deg`
- 尚缺参数说明：`filename_prefix`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `inspect-plane-wave`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：使用 PlaneWave 公开 getter 读取传播向量、电场向量和极化参数。
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：`project_path`
- 尚缺参数说明：无
- 当前声明的业务输出字段：`project_path`、`faces`、`unit_cell_scan`、`ports`、`plane_wave`、`monitors`、`count`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `inspect-project`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Open a CST project, list all parameters and entities, then close. Returns parameter names/values and entity names.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `is-simulation-running`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Check whether the CST solver is currently running for the verified working project.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-monitors`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：使用 Monitor 公开 getter 返回名称、类型、域和频率；与结果树扫描工具并存。
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：`project_path`
- 尚缺参数说明：无
- 当前声明的业务输出字段：`project_path`、`faces`、`unit_cell_scan`、`ports`、`plane_wave`、`monitors`、`count`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-parameters`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：List parameters from the verified CST working project.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `pause-simulation`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`session`（改变 CST 会话状态）
- 当前说明（Registry 原文）：Pause the currently running CST solver.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `prepare-experiment`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Open a CST project, change one or more parameters, confirm, then save and close. Supports batch via names+values arrays. Use before run-experiment.
- 必填参数：`project_path`、`param_name`、`param_value`、`names`、`values`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`param_name`、`param_value`、`names`、`values`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `resume-simulation`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Resume a paused CST solver.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `set-fdsolver-extrude-open-bc`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Enable or disable FD solver extruded open boundary.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `set-mesh-fpbavoid-nonreg-unite`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Enable or disable mesh FPBA non-regular unite avoidance.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `set-mesh-minimum-step-number`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Set the minimum mesh step number.
- 必填参数：`project_path`、`num_steps`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`num_steps`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `set-solver-acceleration`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Configure solver parallelization and hardware acceleration.
- 必填参数：`project_path`、`use_parallelization`、`max_threads`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`use_parallelization`、`max_threads`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `start-simulation`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`long-running`（长时间运行）
- 当前说明（Registry 原文）：同步运行 CST 求解器并阻塞到结束；仅当 CST 的 run_solver 返回 True 才报告 success。失败时返回 solver_run_failed，并附本次求解写入 Result 日志的 CST 原始报错文本。
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `start-simulation-async`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`long-running`（长时间运行）
- 当前说明（Registry 原文）：异步启动 CST 求解器；返回成功只表示启动调用完成，不代表求解成功。
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `stop-simulation`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`session`（改变 CST 会话状态）
- 当前说明（Registry 原文）：Stop the currently running CST solver.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `wait-simulation`

**已有信息**

- 当前分类：`project_ops`（工程配置与求解控制）
- 当前风险：`long-running`（长时间运行）
- 当前说明（Registry 原文）：轮询直到求解器不再运行或超时；running=false 只表示停止，不能证明求解成功。
- 必填参数：`project_path`
- 可选参数：`timeout_seconds`、`poll_interval_seconds`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`timeout_seconds`、`poll_interval_seconds`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## 结果发现、读取与导出（`results`，22 个）

### `analyze-metasurface-sparameters`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：完全离线读取多个 export-sparameter JSON，计算复数幅相、R/T/A、PCR、目标相位误差和被动性，并写出非空 JSON。
- 必填参数：`channels`、`output_path`
- 可选参数：`target_phases`、`passivity_tolerance`
- 已有参数说明：无
- 尚缺参数说明：`channels`、`target_phases`、`passivity_tolerance`、`output_path`
- 当前声明的业务输出字段：`output_path`、`file_size`、`run_id`、`frequency_range_ghz`、`frequency_count`、`channel_count`、`summary`、`warning_count`、`warnings`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `export-current-density`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：导出实际 ResultTree 中的电流密度节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 必填参数：`project_path`、`result_path`、`file_path`
- 可选参数：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`result_path`、`file_path`、`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 当前声明的业务输出字段：`project_path`、`output_path`、`output_file`、`file_size`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `export-e-field`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：导出实际 ResultTree 中的电场节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 必填参数：`project_path`、`result_path`、`file_path`
- 可选参数：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`result_path`、`file_path`、`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 当前声明的业务输出字段：`project_path`、`output_path`、`output_file`、`file_size`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `export-h-field`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：导出实际 ResultTree 中的磁场节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 必填参数：`project_path`、`result_path`、`file_path`
- 可选参数：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`result_path`、`file_path`、`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 当前声明的业务输出字段：`project_path`、`output_path`、`output_file`、`file_size`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `export-power-flow`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：导出实际 ResultTree 中的功率流节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 必填参数：`project_path`、`result_path`、`file_path`
- 可选参数：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`result_path`、`file_path`、`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 当前声明的业务输出字段：`project_path`、`output_path`、`output_file`、`file_size`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `export-power-loss-density`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：导出实际 ResultTree 中的功率损耗密度节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 必填参数：`project_path`、`result_path`、`file_path`
- 可选参数：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`result_path`、`file_path`、`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 当前声明的业务输出字段：`project_path`、`output_path`、`output_file`、`file_size`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `export-sparameter`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：按真实 ResultTree 节点导出一条 S 参数曲线。可直接指定 result_path，或使用响应端口、激励端口及可选模式；支持 S1,1 和 SZmin(1),Zmax(1) 等 CST 2022 名称。
- 必填参数：`project_path`、`run_id`、`output_path`
- 可选参数：`result_path`、`response_port`、`excitation_port`、`response_mode`、`excitation_mode`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`run_id`、`output_path`、`result_path`、`response_port`、`excitation_port`、`response_mode`、`excitation_mode`
- 当前声明的业务输出字段：`project_path`、`result_path`、`run_id`、`output_path`、`point_count`、`result_metric`、`s11_metric`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `export-surface-current`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：导出实际 ResultTree 中的表面电流节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 必填参数：`project_path`、`result_path`、`file_path`
- 可选参数：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`result_path`、`file_path`、`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`
- 当前声明的业务输出字段：`project_path`、`output_path`、`output_file`、`file_size`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `export-touchstone`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：使用 CST 2022 TOUCHSTONE Object 导出完整 S/Y/Z 网络矩阵；端口模式顺序由 CST 文件头给出。
- 必填参数：`project_path`、`output_base_path`
- 可选参数：`parameter_type`、`data_format`、`frequency_range`、`fmin`、`fmax`、`impedance`、`renormalize`、`sample_count`、`use_ar_results`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`output_base_path`、`parameter_type`、`data_format`、`frequency_range`、`fmin`、`fmax`、`impedance`、`renormalize`、`sample_count`、`use_ar_results`
- 当前声明的业务输出字段：`project_path`、`output_path`、`output_file`、`file_size`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `export-voltage-result`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：按实际 0D/1D ResultTree 完整路径导出电压结果，不生成固定监视器编号。
- 必填参数：`project_path`、`result_path`、`file_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`result_path`、`file_path`
- 当前声明的业务输出字段：`project_path`、`output_path`、`output_file`、`file_size`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `generate-report`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Generate a modular HTML report from exported S11, farfield, and audit files. Supports --modules and --split.
- 必填参数：`data_dir`、`output_html`、`page_title`、`modules`、`split`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`data_dir`、`output_html`、`page_title`、`modules`、`split`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `get-1d-result`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Read an exact 0D/1D result-tree path with cst.results and serialize its saved data to JSON.
- 必填参数：`project_path`、`treepath`、`module_type`、`run_id`、`load_impedances`、`export_path`、`allow_interactive`
- 可选参数：无
- 已有参数说明：`run_id`、`allow_interactive`
- 尚缺参数说明：`project_path`、`treepath`、`module_type`、`load_impedances`、`export_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `get-2d-result`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Serialize 2D data only when the installed cst.results API exposes get_result2d_item; CST 2022 does not document it.
- 必填参数：`project_path`、`treepath`、`module_type`、`export_path`、`allow_interactive`、`subproject_treepath`、`include_data`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`treepath`、`module_type`、`export_path`、`allow_interactive`、`subproject_treepath`、`include_data`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `get-parameter-combination`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Read the parameter combination for a result run ID.
- 必填参数：`project_path`、`run_id`、`module_type`、`allow_interactive`
- 可选参数：无
- 已有参数说明：`run_id`
- 尚缺参数说明：`project_path`、`module_type`、`allow_interactive`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `get-version-info`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Read cst.results version information.
- 必填参数：无
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：无
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-field-results`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：使用 CST 2022 ResultTree.GetTreeResults 枚举 2D/3D 节点、官方 Result Type 和关联文件。
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：`project_path`、`count`、`results`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-result-items`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：List result tree items from a project path.
- 必填参数：`project_path`、`module_type`、`filter_type`、`allow_interactive`、`subproject_treepath`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`module_type`、`filter_type`、`allow_interactive`、`subproject_treepath`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-run-ids`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：List CST result run IDs from a project path.
- 必填参数：`project_path`、`treepath`、`module_type`、`allow_interactive`、`skip_nonparametric`、`max_mesh_passes_only`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`treepath`、`module_type`、`allow_interactive`、`skip_nonparametric`、`max_mesh_passes_only`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-sparameter-results`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：枚举实际 ResultTree 中的普通端口与 Floquet S 参数节点及可用 Run ID。允许工程同时在 CST 中打开；此时读取最近保存到磁盘的工程状态。
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：`project_path`、`count`、`results`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `list-subprojects`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：List subprojects from a CST results project by explicit project_path.
- 必填参数：`project_path`、`allow_interactive`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`allow_interactive`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `open-results-project`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Validate that cst.results can open a project path.
- 必填参数：`project_path`、`allow_interactive`、`subproject_treepath`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`allow_interactive`、`subproject_treepath`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `plot-exported-file`

**已有信息**

- 当前分类：`results`（结果发现、读取与导出）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Render an exported JSON result or CST farfield ASCII/TXT file to an HTML preview.
- 必填参数：`file_path`、`output_html`、`page_title`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`file_path`、`output_html`、`page_title`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## 任务与运行目录（`run`，2 个）

### `get-run-context`

**已有信息**

- 当前分类：`run`（任务与运行目录）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Read standard run context through cst_runtime.
- 必填参数：`task_path`、`run_id`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`task_path`、`run_id`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `prepare-run`

**已有信息**

- 当前分类：`run`（任务与运行目录）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Create a standard run workspace through cst_runtime.
- 必填参数：`task_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`task_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## CST 会话管理（`session_manager`，6 个）

### `create-blank-project`

**已有信息**

- 当前分类：`session_manager`（CST 会话管理）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：Create a new blank CST project at the specified path.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `cst-session-close`

**已有信息**

- 当前分类：`session_manager`（CST 会话管理）
- 当前风险：`session`（改变 CST 会话状态）
- 当前说明（Registry 原文）：Close the expected CST project, optionally wait for locks to clear, then inspect the environment.
- 必填参数：`project_path`、`save`、`wait_unlock`、`timeout_seconds`、`poll_interval_seconds`
- 可选参数：`kill_processes`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`save`、`wait_unlock`、`timeout_seconds`、`poll_interval_seconds`、`kill_processes`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `cst-session-inspect`

**已有信息**

- 当前分类：`session_manager`（CST 会话管理）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：Central session/process gate: inspect processes, locks, open projects, and reattach readiness.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `cst-session-open`

**已有信息**

- 当前分类：`session_manager`（CST 会话管理）
- 当前风险：`session`（改变 CST 会话状态）
- 当前说明（Registry 原文）：通过中央会话管理器打开 CST 工程。默认只自动接管本次启动后唯一新增的 PID；若需要接管已有或归属不明确的会话，首次调用会返回候选 PID，调用方必须先询问用户，再同时提供 confirm_existing_session_takeover=true 与用户确认的 existing_session_pid。
- 必填参数：`project_path`
- 可选参数：`confirm_existing_session_takeover`、`existing_session_pid`
- 已有参数说明：`confirm_existing_session_takeover`、`existing_session_pid`
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `cst-session-reattach`

**已有信息**

- 当前分类：`session_manager`（CST 会话管理）
- 当前风险：`session`（改变 CST 会话状态）
- 当前说明（Registry 原文）：重新附着已打开的 CST 工程。首次调用只返回候选 PID；调用方询问用户后，必须同时传入确认标志和用户选择的 PID。
- 必填参数：`project_path`
- 可选参数：`confirm_existing_session_takeover`、`existing_session_pid`
- 已有参数说明：`confirm_existing_session_takeover`、`existing_session_pid`
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `save-project`

**已有信息**

- 当前分类：`session_manager`（CST 会话管理）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Save the verified CST working project.
- 必填参数：`project_path`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## 仿真工作流（`simulation`，1 个）

### `run-experiment`

**已有信息**

- 当前分类：`simulation`（仿真工作流）
- 当前风险：`long-running`（长时间运行）
- 当前说明（Registry 原文）：运行求解并等待完成；必须以指定 0D/1D 结果节点共同出现的新 Run ID 和非空数据验收。求解前结果节点尚不存在视为空基线（首次仿真的正常初始状态，支持由本次仿真生成节点）；不执行任何结果导出，返回通用 result_metrics；S1,1 仅保留兼容 s11_metric。
- 必填参数：`project_path`、`completion_result_paths`、`timeout_seconds`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`completion_result_paths`、`timeout_seconds`
- 当前声明的业务输出字段：`project_path`、`run_id`、`completion_result_paths`、`result_metrics`、`s11_metric`、`solver_completed`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## 复合工作流（`workflow`，2 个）

### `build-array`

**已有信息**

- 当前分类：`workflow`（复合工作流）
- 当前风险：`write`（修改 CST 工程或运行状态）
- 当前说明（Registry 原文）：按普通 code 和受控 builder 批量构建 CST 阵列；元素坐标是参考模板的相对平移量。brick-v1 的 origin 是最小角点，如使用中心坐标应由调用方预先换算。
- 必填参数：`project_path`、`units`、`elements`
- 可选参数：`summary`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`units`、`elements`、`summary`
- 当前声明的业务输出字段：`project_path`、`groups_built`、`instances_created`、`reference_objects`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `quick-sweep`

**已有信息**

- 当前分类：`workflow`（复合工作流）
- 当前风险：`long-running`（长时间运行）
- 当前说明（Registry 原文）：运行参数扫描并导出 JSON、CSV 和 NPZ 结果。
- 必填参数：`project_path`、`parameters`、`target_freq_ghz`
- 可选参数：`result_path`、`output_dir`、`continue_on_error`、`restore_parameters`
- 已有参数说明：无
- 尚缺参数说明：`project_path`、`parameters`、`target_freq_ghz`、`result_path`、`output_dir`、`continue_on_error`、`restore_parameters`
- 当前声明的业务输出字段：`output_dir`、`sweep_time`、`total_steps`、`successful_steps`、`failed_steps`、`records`、`exported_files`、`errors`

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]


## Runtime 工作区（`workspace`，3 个）

### `health-check`

**已有信息**

- 当前分类：`workspace`（Runtime 工作区）
- 当前风险：`read`（只读）
- 当前说明（Registry 原文）：只读检查 Python、工作区、CST 库和导入状态；不会初始化、安装或修改配置。
- 必填参数：`workspace`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`workspace`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `init-task`

**已有信息**

- 当前分类：`workspace`（Runtime 工作区）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Create a task.json and runs directory inside a runtime workspace.
- 必填参数：`workspace`、`task_id`、`source_project`、`goal`、`title`、`force`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`workspace`、`task_id`、`source_project`、`goal`、`title`、`force`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]

### `init-workspace`

**已有信息**

- 当前分类：`workspace`（Runtime 工作区）
- 当前风险：`filesystem-write`（写入工程或文件系统）
- 当前说明（Registry 原文）：Initialize a minimal CST runtime workspace in an empty or existing directory.
- 必填参数：`workspace`
- 可选参数：无
- 已有参数说明：无
- 尚缺参数说明：`workspace`
- 当前声明的业务输出字段：暂无；目前只有统一状态/错误外壳，需要确认稳定业务字段。

**待补充信息（请使用中文）**

- 中文标题：[待填写]
- 用户目标：[待填写]
- 何时使用：[待填写]
- 不要用于／与相似工具的区别：[待填写]
- 前置条件：[待填写]
- 副作用：[待填写]
- 成功后的重试规则：[待填写]
- 关联工具（前一步／替代／后一步）：[待填写]
- 成功返回摘要：[待填写]
- 失败处理：[待填写]
- 参数补充（仅写需要增加或修正的参数说明）：[待填写]
- 检索关键词：[待填写]
- 其他备注：[待填写]
