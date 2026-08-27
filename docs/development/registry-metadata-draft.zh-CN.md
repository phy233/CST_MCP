# Registry 元数据中文首稿（待人工审核）

> 状态：Agent 首稿完成，等待人工审核。本文件仍是代码回填前的工作稿，不是最终用户文档。
> 审核者只需指出 CST 专业事实、单位、坐标、对象保留或删除语义、工作顺序哪里不正确；不需要填写 MCP 字段。

## 依据与证据边界

- OpenAI 官方：[Define tools](https://developers.openai.com/plugins/plan/tools)、[Optimize Metadata](https://developers.openai.com/plugins/guides/optimize-metadata)、[MCP server](https://developers.openai.com/plugins/concepts/mcp-server)。首稿据此记录用户目标、触发条件、相似工具区别、输入输出、副作用和失败行为。
- CST 官方：本机 CST Studio Suite 2022 Online Help。重点页面包括 Solid、Brick、ExtrudeCurve、Loft、Transform、Monitor、Boundary、Background、FDSolver、FloquetPort、PlaneWave、ASCIIExport、TOUCHSTONE、ResultTree，以及 Python 的 cst.results 和 cst.interface。
- 当前实现：Registry 的名称、风险、输入 Schema、输出 Schema 和现有 description。它们是代码事实，不自动等于官方手册事实或实机验收结果。
- 当前暴露范围：Registry 共注册 146 个工具，其中 136 个为 `agent`，本稿与这 136 个逐一对应；`checkout-replay-copy`、`create-history-checkpoint`、`create-project-checkpoint`、`cst-session-quit`、`export-history-snapshot`、`health-repair`、`inspect-history-capabilities`、`inspect-history-status`、`install-cst-libraries`、`reconcile-history-operation` 共 10 个高风险工具为 `cli_only`，不进入 Agent 初始工具清单。
- 首稿推断：关联流程、Agent 触发语句和失败恢复是基于上述资料的拟稿；有疑问的 CST 语义已标为“重点审核”。

### 本轮实际核对的 CST 2022 官方帮助页

以下路径均相对于 `D:\Program Files (x86)\CST Studio Suite 2022\Online Help`：

| 核对范围                       | Online Help 相对路径                                                                                                                                                                                                                                      |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Solid 布尔操作                 | `mergedProjects/VBA_3D/common_vbasolido/common_vbasolido_solid_object.htm`                                                                                                                                                                              |
| Brick、ExtrudeCurve、Loft      | `mergedProjects/VBA_3D/common_vbabasicSolids/common_vbabrick_object.htm`、`mergedProjects/VBA_3D/common_vbacurves/common_vbacurves_extrudecurve_object.htm`、`mergedProjects/VBA_3D/common_vbaloft/common_vbaloftloft_object.htm`                   |
| Transform                      | `mergedProjects/VBA_3D/special_vbatransformo/special_vbatransformo_transform_object.htm`                                                                                                                                                                |
| Boundary、Background、FDSolver | `mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_boundary_object.htm`、`mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_background_object.htm`、`mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_fdsolver_object.htm` |
| FloquetPort、PlaneWave         | `mergedProjects/VBA_3D/special_vbaports/floquetport_object.htm`、`mergedProjects/VBA_3D/special_vbaports/special_vbaports_planewave_object.htm`                                                                                                       |
| Monitor                        | `mergedProjects/VBA_3D/special_vbamonitors/special_vbamonitors_monitor_object.htm`                                                                                                                                                                      |
| 曲线与曲线拉伸                 | `mergedProjects/VBA_3D/common_vbacurves/common_vbacurves_analyticalcurve_object.htm`、`mergedProjects/VBA_3D/common_vbacurves/common_vbacurves_polygon3d.htm`、`mergedProjects/VBA_3D/common_vbacurves/common_vbacurves_rectangle_object.htm`、`mergedProjects/VBA_3D/common_vbacurves/common_vbacurves_extrudecurve_object.htm` |
| FarfieldPlot 自动切面          | `mergedProjects/VBA_3D/special_vbapostproc/special_vbapostproc_farfieldploto.htm`                                                                                                                                                                       |
| 求解器类型与时域/频域配置      | `mergedProjects/VBA_3D/common_vbaapp/common_vbaappapplication_object.htm`、`mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_solver_object.htm`、`mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_fdsolver_object.htm`                   |
| ASCII 与 Touchstone 导出       | `mergedProjects/VBA_3D/common_vbaimpexp/asciiexport_object.htm`、`mergedProjects/VBA_3D/special_vbaimpexp/special_vbaimp_exp_touchstone.htm`                                                                                                          |
| ResultTree 与 Python API       | `mergedProjects/VBA_3D/special_vbapostproc/special_vbapostproc_resulttreeo.htm`、`Python/source/cst.results.html`、`Python/source/cst.interface.html`                                                                                               |

## 审核方式

- 建议按类别审核，不必从头连续阅读 136 个工具。
- 每个工具的“当前 Registry”是现有代码文字；其他字段是拟写入 Registry 的中文首稿。
- 如果一句话不符合 CST 实际使用，直接改句子或在该工具下留言即可。
- OpenAI 官方建议准备直接提示、间接提示和负例提示；正式回填后再据此做工具发现测试。

## 全局规则

1. 本 MCP 是超表面设计辅助者，负责减轻扫参、优化和重复建模负担，并让 Agent 接入 CST 提供单元设计建议；主要设计判断与关键建模仍由人类用户完成。
2. 本 MCP 不定位为“通用超表面端到端设计”或“全自动超表面设计”，Agent 不得擅自确定结构、材料、参数范围、目标函数、优化预算或最终方案。
3. 普通 CST/VBA 写入只要接口没有返回错误，就应充分相信 CST 已成功执行；不要固定增加执行前检查和执行后检查。导出文件、异步求解、结果节点验收、会话归属不明等必要边界除外。
4. 写入类工具成功后通常不要重复调用；只读工具也不应仅为确认成功而重复调用。
5. 结果工具优先使用实际 ResultTree 完整路径；导出产物需要确认文件存在且非空。
6. R/T/A 通道求和与相位参考规则本轮只补文档，不修改实现。
7. AnalyticalCurve、Polygon3D 和 Rectangle 创建的是 `Curves` 下的曲线项，不属于组件实体，也不指定材料。当前 MCP 会在曲线容器不存在时创建容器，因此不要把 `create-component` 或 `list-materials` 写成曲线建模前置。若目标是实体，应先形成闭合、共面的曲线轮廓，再交给 `define-extrude-curve`；只有生成实体后才进入布尔操作。
8. 场监视器和内部场探针通常没有实体、组件或材料前置，应在求解前按结果需求定义，后续进入启动求解和结果读取流程。远场切面属于求解后自动处理设置：调用时不要求已有结果，但求解前必须存在远场监视器。
9. 本稿把“显式选择求解器类型、使用与当前类型匹配的求解器配置、完成边界相关设置”作为 `start-simulation`、`start-simulation-async` 和 `run-experiment` 的必要前置。不得在当前为时域求解器时调用 FDSolver 专用设置，也不得在当前为频域求解器时调用本实现中基于 Solver Object 的时域专用设置；只读检查工具不作为固定前置检查。

## 分类概览

| Registry 分类        | 中文含义             | Agent 工具数 |
| -------------------- | -------------------- | -----------: |
| `audit`            | 审计记录             |            3 |
| `farfield`         | 远场结果             |            4 |
| `history`          | CST History          |            3 |
| `interaction`      | Agent 交互记录       |            4 |
| `modeling`         | 几何与建模           |           36 |
| `optimization`     | 扫参与优化           |           11 |
| `project_identity` | 工程身份与锁定状态   |            4 |
| `project_ops`      | 工程配置与求解控制   |           35 |
| `results`          | 结果发现、读取与导出 |           22 |
| `run`              | 任务与运行目录       |            2 |
| `session_manager`  | CST 会话管理         |            6 |
| `simulation`       | 仿真工作流           |            1 |
| `workflow`         | 复合工作流           |            2 |
| `workspace`        | Runtime 工作区       |            3 |

## 审计记录（`audit`，3 个）

> 本类不修改 CST 模型；重点审核阶段名称、证据范围和状态含义。

### `record-stage` — 记录运行阶段

- 建议定位：完成“记录运行阶段”，保存或返回 Runtime 工作流所需的信息。
- 何时使用：需要建立可追溯的 Runtime 任务、日志、证据或运行目录时。
- 不要用于：不代表 CST 已执行建模或求解，也不替代实际工程文件和结果节点。
- 前置与副作用：必须提供 `task_path`、`run_id`、`stage`、`status`、`message`、`details_json`，并保证引用的工程、对象或文件真实存在；会写入 Runtime 工作区、日志、状态文件或报告。
- 成功与重试：成功后不要重复写入；失败时修正明确参数或路径后再重试。
- 关联流程：prepare-run → record-stage → update-status；需要证据时使用 stage-evidence。
- 接口摘要：当前风险 `filesystem-write`；必填：`task_path`、`run_id`、`stage`、`status`、`message`、`details_json`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`run_id=0` 的含义按该接口当前说明处理。写入失败时保留原错误和上下文，修正明确输入后重试。
- 当前 Registry：Write a stage record and production-chain log entry.

### `stage-evidence` — 采集与比较阶段证据

- 建议定位：完成“采集与比较阶段证据”，保存或返回 Runtime 工作流所需的信息。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：快照与比较用于审计，不应作为每个普通 CST 成功调用后的固定检查。
- 前置与副作用：必须提供 `project_path`、`capture`、`stage_name`、`output_dir`、`compare`、`output_html`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：record-stage 或 list-history-log → stage-evidence；仅在审计节点使用。
- 接口摘要：当前风险 `read`；必填：`project_path`、`capture`、`stage_name`、`output_dir`、`compare`、`output_html`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；输出路径应由调用方明确指定。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：Capture CST project state snapshots and generate before/after comparison reports. Use --capture to snapshot, --compare to diff two snapshots into HTML.
- 重点审核：当前 Registry 风险值为 read，但 capture/compare 会写快照或 HTML；代码回填时应重新核对风险元数据。

### `update-status` — 更新运行状态

- 建议定位：完成“更新运行状态”，保存或返回 Runtime 工作流所需的信息。
- 何时使用：需要建立可追溯的 Runtime 任务、日志、证据或运行目录时。
- 不要用于：不代表 CST 已执行建模或求解，也不替代实际工程文件和结果节点。
- 前置与副作用：必须提供 `task_path`、`run_id`、`status`、`stage`、`best_result_json`、`output_files_json`、`error_json`、`extra_json`，并保证引用的工程、对象或文件真实存在；会写入 Runtime 工作区、日志、状态文件或报告。
- 成功与重试：成功后不要重复写入；失败时修正明确参数或路径后再重试。
- 关联流程：prepare-run → record-stage → update-status。
- 接口摘要：当前风险 `filesystem-write`；必填：`task_path`、`run_id`、`status`、`stage`、`best_result_json`、`output_files_json`、`error_json`、`extra_json`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`run_id=0` 的含义按该接口当前说明处理。写入失败时保留原错误和上下文，修正明确输入后重试。
- 当前 Registry：Update the formal run status.json file.

## 远场结果（`farfield`，4 个）

> 本类位于已有远场监视器或结果之后；重点审核结果节点、角度范围、极化量和导出格式。

### `calculate-farfield-neighborhood-flatness` — 计算远场邻域平坦度

- 建议定位：完成“计算远场邻域平坦度”，返回后续步骤所需的信息。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `file_paths`、`theta_max_deg`、`output_json`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`file_paths`、`theta_max_deg`、`output_json`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：Calculate near-boresight farfield cut flatness from exported cut JSON payloads.

### `export-farfield-cut` — 导出远场切面

- 建议定位：把“导出远场切面”对应的已有 CST 结果写到指定文件，供离线分析或报告使用。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不用于发现结果节点；路径未知时先调用相应 list-* 工具。
- 前置与副作用：必须提供 `project_path`、`tree_path`、`export_dir`、`fresh_session`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `long-running`；必填：`project_path`、`tree_path`、`export_dir`、`fresh_session`；可选：无；关键返回：`project_path`、`output_path`、`output_file`、`file_size`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径；输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：Export an existing CST Farfield Cut tree item to JSON under {export_dir}/farfield/cuts/.

### `export-farfield-grid` — 导出远场角度网格

- 建议定位：把“导出远场角度网格”对应的已有 CST 结果写到指定文件，供离线分析或报告使用。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不用于发现结果节点；路径未知时先调用相应 list-* 工具。
- 前置与副作用：必须提供 `project_path`、`farfield_name`、`export_dir`、`quantity`、`theta_step_deg`、`phi_step_deg`、`theta_min_deg`、`theta_max_deg`、`phi_min_deg`、`phi_max_deg`、`run_id`、`fresh_session`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `long-running`；必填：`project_path`、`farfield_name`、`export_dir`、`quantity`、`theta_step_deg`、`phi_step_deg`、`theta_min_deg`、`theta_max_deg`、`phi_min_deg`、`phi_max_deg`、`run_id`、`fresh_session`；可选：无；关键返回：`project_path`、`output_path`、`output_file`、`file_size`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；`run_id=0` 的含义按该接口当前说明处理；输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：Compute a compatible farfield scalar grid and export as JSON under {export_dir}/farfield/. Supports fresh_session reuse.

### `inspect-farfield-monitors` — 检查远场监视器结果节点

- 建议定位：读取与“检查远场监视器结果节点”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：从结果树发现远场结果；查看模型中的 Monitor 对象使用 list-monitors。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：Discover farfield monitors from a CST project by scanning the result tree.

## CST History（`history`，3 个）

> 本类处理 Runtime 保存的 History 快照与日志，不直接替代 CST 的 Undo/Redo。

### `diff-history-snapshots` — 比较 History 快照

- 建议定位：比较任意两个 History 快照并输出块级增删改及原始 VBA 统一 diff。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `before_snapshot_id`、`after_snapshot_id`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：list-history-log → inspect-interaction-history（可选）→ diff-history-snapshots。
- 接口摘要：当前风险 `read`；必填：`before_snapshot_id`、`after_snapshot_id`；可选：`project_path`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：比较任意两个 History 快照并输出块级增删改及原始 VBA 统一 diff。

### `generate-restore-plan` — 生成 History 恢复计划

- 建议定位：纯只读分析基线工程与目标快照的严格前缀关系并生成重放计划。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `baseline_project_path`、`target_snapshot_id`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：list-history-log 或 diff-history-snapshots → generate-restore-plan；实际重放另行执行。
- 接口摘要：当前风险 `read`；必填：`baseline_project_path`、`target_snapshot_id`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：纯只读分析基线工程与目标快照的严格前缀关系并生成重放计划。

### `list-history-log` — 查询 History 日志

- 建议定位：查询 CST History 操作记录流水与快照哈希变更。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 无必填参数，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：list-history-log → 本工具 → diff-history-snapshots 或 generate-restore-plan。
- 接口摘要：当前风险 `read`；必填：无；可选：`project_path`、`execution_state`、`reconciliation_state`、`limit`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：查询 CST History 操作记录流水与快照哈希变更。

## Agent 交互记录（`interaction`，4 个）

> 本类保存 Agent 与用户的决策记录，不代表 CST 已执行建模或求解。

### `inspect-interaction-history` — 检查单次交互关联的 History

- 建议定位：查询单次 MCP 工具调用关联的 History 快照及 Operation 详细变更。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `interaction_id`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：list-interaction-log → inspect-interaction-history → diff-history-snapshots。
- 接口摘要：当前风险 `read`；必填：`interaction_id`；可选：`workspace`、`project_path`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `workspace`、`project_path` 的限定。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：查询单次 MCP 工具调用关联的 History 快照及 Operation 详细变更。

### `list-agent-notes` — 查询 Agent 工作说明

- 建议定位：查询已持久化的 Agent 显式工作说明与人工处置笔记列表。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 无必填参数，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：record-agent-note 或 list-interaction-log → 本工具 → inspect-interaction-history（需要时）。
- 接口摘要：当前风险 `read`；必填：无；可选：`task_id`、`run_id`、`project_path`、`category`、`limit`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；`run_id=0` 的含义按该接口当前说明处理；代码回填时保留现有 Schema 对 `project_path` 的限定。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：查询已持久化的 Agent 显式工作说明与人工处置笔记列表。

### `list-interaction-log` — 查询 MCP 交互日志

- 建议定位：查询 MCP 工具调用的全生命周期交互日志流。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 无必填参数，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：record-agent-note 或 list-interaction-log → 本工具 → inspect-interaction-history（需要时）。
- 接口摘要：当前风险 `read`；必填：无；可选：`workspace`、`project_path`、`task_id`、`run_id`、`tool_name`、`interaction_id`、`limit`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；`run_id=0` 的含义按该接口当前说明处理；代码回填时保留现有 Schema 对 `workspace`、`project_path` 的限定。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：查询 MCP 工具调用的全生命周期交互日志流。

### `record-agent-note` — 记录 Agent 或用户说明

- 建议定位：显式记录 Agent 或用户的阶段工作说明、关键设计决策或人工处置结论。
- 何时使用：需要建立可追溯的 Runtime 任务、日志、证据或运行目录时。
- 不要用于：不代表 CST 已执行建模或求解，也不替代实际工程文件和结果节点。
- 前置与副作用：必须提供 `content`，并保证引用的工程、对象或文件真实存在；会写入 Runtime 工作区、日志、状态文件或报告。
- 成功与重试：成功后不要重复写入；失败时修正明确参数或路径后再重试。
- 关联流程：record-agent-note → list-agent-notes；可关联 interaction_id 或 snapshot_id。
- 接口摘要：当前风险 `filesystem-write`；必填：`content`；可选：`category`、`task_id`、`run_id`、`project_path`、`user_confirmed`、`interaction_id`、`operation_id`、`snapshot_id`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；`run_id=0` 的含义按该接口当前说明处理；代码回填时保留现有 Schema 对 `project_path` 的限定。写入失败时保留原错误和上下文，修正明确输入后重试。
- 当前 Registry：显式记录 Agent 或用户的阶段工作说明、关键设计决策或人工处置结论。

## 几何与建模（`modeling`，36 个）

> 本类主要写入 CST History。普通接口返回成功后信任 CST 已执行；布尔减法重叠、导出和方向符号等必要边界除外。

### `boolean-add` — 布尔操作-合并

- 建议定位：对两个物体使用该操作后，导航树中两物体合并，且两模型的并集形状保持不变
- 何时使用：需要构造较复杂几何体，且该几何体可拆成若干基本几何体（圆柱球体立方体等）
- 不要用于：当复杂几何体需要挖孔等需要构建内部形状时，应采用布尔操作减法
- 前置与副作用：两个待合并物体均存在；导航树中两物体被合并，后一个传入的物体在导航树中会消失。
- 成功与重试：成功后不要重复执行。
- 关联流程：已有两个实体（名称不明确时才使用 list-entities，或先用实体创建/曲线拉伸工具生成）→ 本工具 → save-project；曲线项不能直接进入本流程。
- 接口摘要：当前风险 `write`；必填：`project_path`、`shape1`、`shape2`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Unite two solids (boolean union).

### `boolean-insert` — 布尔操作-插入

- 建议定位：在指定 CST 工程中完成“布尔操作-插入”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不要与 boolean-add 混用；Insert 后两个实体的保留语义应按 CST 官方 Solid Object 与用户目标确认。
- 前置与副作用：必须提供 `project_path`、`shape1`、`shape2`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：已有两个实体（名称不明确时才使用 list-entities，或先用实体创建/曲线拉伸工具生成）→ 本工具 → save-project；曲线项不能直接进入本流程。
- 接口摘要：当前风险 `write`；必填：`project_path`、`shape1`、`shape2`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Insert one solid into another (boolean insert).
- 重点审核：请重点确认 CST Insert 后 shape1/shape2 的导航树保留语义。

### `boolean-intersect` — 布尔操作-求交

- 建议定位：在指定 CST 工程中完成“布尔操作-求交”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：只保留两实体交集，不用于合并总体积或用工具体挖孔。
- 前置与副作用：必须提供 `project_path`、`shape1`、`shape2`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：已有两个实体（名称不明确时才使用 list-entities，或先用实体创建/曲线拉伸工具生成）→ 本工具 → save-project；曲线项不能直接进入本流程。
- 接口摘要：当前风险 `write`；必填：`project_path`、`shape1`、`shape2`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Intersect two solids (boolean intersection).

### `boolean-subtract` — 布尔操作-相减

- 建议定位：在指定 CST 工程中完成“布尔操作-相减”，作为用户建模流程中的一个明确步骤。
- 何时使用：已构造目标体和真实重叠的工具体，需要从目标体中挖孔或切除材料时。
- 不要用于：目标体与工具体必须在坐标上真实重叠，若两模型交集为空，执行布尔相减指令会导致减去的模型消失，被减模型不变且CST返回执行成功（不是bug，是CST自己的执行逻辑）；接口成功不单独证明材料已被移除。
- 前置与副作用：必须提供 `project_path`、`target`、`tool`，并保证引用的工程、对象或文件真实存在；确保两模型交集非空；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：已有两个真实重叠的实体（名称不明确时才使用 list-entities，或先用实体创建/曲线拉伸工具生成）→ 本工具 → save-project；曲线项不能直接进入本流程。
- 接口摘要：当前风险 `write`；必填：`project_path`、`target`、`tool`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `target`、`tool` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Subtract one solid from another (boolean difference). CST may accept a subtraction between non-intersecting solids without changing the target, so confirm geometric overlap from the modeled coordinates before calling.

### `change-material` — 更换实体材料

- 建议定位：在指定 CST 工程中完成“更换实体材料”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`shape_name`、`material`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：list-entities 或 list-materials（需要时）→ 本工具 → save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`shape_name`、`material`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Change the material of a geometry entity. Use list-materials to see available names.

### `create-component` — 创建组件

- 建议定位：在指定 CST 工程中完成“创建组件”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`component_name`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无前置依赖 → 本工具 → 使用该组件名的实体创建工具 → save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`component_name`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Create a new component in the CST project.

### `create-hollow-sweep` — 创建空心渐变扫掠体

- 建议定位：在指定 CST 工程中完成“创建空心渐变扫掠体”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`name`、`component`、`material`、`x_min1`、`x_max1`、`y_min1`、`y_max1`、`z1`、`x_min2`、`x_max2`、`y_min2`、`y_max2`、`z2`、`wall_thickness`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：create-component 或 list-materials（需要时）→ 本工具 → boolean-* / transform-* / save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`component`、`material`、`x_min1`、`x_max1`、`y_min1`、`y_max1`、`z1`、`x_min2`、`x_max2`、`y_min2`、`y_max2`、`z2`、`wall_thickness`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `x_min1`、`x_max1`、`y_min1`、`y_max1`、`z1`、`x_min2`、`x_max2`、`y_min2`、`y_max2`、`z2` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Create a hollow loft between two rectangular profiles in active X/Y/Z or local U/V/W coordinates.

### `create-loft-sweep` — 创建矩形渐变扫掠体

- 建议定位：在指定 CST 工程中完成“创建矩形渐变扫掠体”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`name`、`component`、`material`、`x_min1`、`x_max1`、`y_min1`、`y_max1`、`z1`、`x_min2`、`x_max2`、`y_min2`、`y_max2`、`z2`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：create-component 或 list-materials（需要时）→ 本工具 → boolean-* / transform-* / save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`component`、`material`、`x_min1`、`x_max1`、`y_min1`、`y_max1`、`z1`、`x_min2`、`x_max2`、`y_min2`、`y_max2`、`z2`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `x_min1`、`x_max1`、`y_min1`、`y_max1`、`z1`、`x_min2`、`x_max2`、`y_min2`、`y_max2`、`z2` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Create a loft between two rectangular profiles in active X/Y/Z or local U/V/W coordinates.

### `create-mesh-group` — 创建网格组

- 建议定位：在指定 CST 工程中完成“创建网格组”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`group_name`、`items`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：已有待分组实体（名称不明确时才使用 list-entities）→ 本工具 → 与当前求解器匹配的网格配置 → start-simulation 或 run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`、`group_name`、`items`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Create a mesh group and add items.

### `define-analytical-curve` — 创建解析曲线

- 建议定位：在 `Curves` 导航树下创建由参数方程定义的曲线项；它不是组件实体，不指定材料。
- 何时使用：用户已明确参数范围以及 X/Y/Z（活动 WCS 下为 U/V/W）坐标函数，需要构造开放路径或闭合轮廓时。
- 不要用于：开放或非共面的曲线不能直接作为拉伸实体的轮廓；曲线本身不能参与 Solid 布尔操作。
- 前置与副作用：必须提供 `project_path`、`name`、`curve`、`law_x`、`law_y`、`law_z`、`param_start`、`param_end`；当前实现会在 `Curves\curve` 容器不存在时自动创建，不需要组件或材料。该操作写入曲线项和 History，不创建实体。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无组件或材料前置 → 本工具 → transform-curve（需要时）；若目标是实体，先形成闭合共面轮廓 → define-extrude-curve → 生成实体后才可使用 boolean-*。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`curve`、`law_x`、`law_y`、`law_z`、`param_start`、`param_end`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `law_x`、`law_y`、`law_z` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Create a parametric curve in active X/Y/Z or local U/V/W coordinates; each law must be differentiable over the parameter range.

### `define-brick` — 创建砖块

- 建议定位：在指定 CST 工程中完成“创建砖块（长方体）”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`name`、`component`、`material`、`x_min`、`x_max`、`y_min`、`y_max`、`z_min`、`z_max`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：create-component 或 list-materials（需要时）→ 本工具 → boolean-* / transform-* / save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`component`、`material`、`x_min`、`x_max`、`y_min`、`y_max`、`z_min`、`z_max`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `x_min`、`x_max`、`y_min`、`y_max`、`z_min`、`z_max` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Create a brick in active X/Y/Z or local U/V/W coordinates.

### `define-cone` — 创建圆锥或圆台

- 建议定位：在指定 CST 工程中完成“创建圆锥或圆台”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`name`、`component`、`material`、`bottom_radius`、`top_radius`（0为圆锥，非0为圆柱）、`axis`、`axis_min`、`axis_max`、`x_center`、`y_center`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：create-component 或 list-materials（需要时）→ 本工具 → boolean-* / transform-* / save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`component`、`material`、`bottom_radius`、`top_radius`、`axis`、`axis_min`、`axis_max`、`x_center`、`y_center`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `axis`、`axis_min`、`axis_max`、`x_center`、`y_center` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Create a cone along an active X/U, Y/V, or Z/W axis. axis_min/axis_max set the axial range; the two transverse centers are mapped to axis-specific VBA setters. bottom_radius is at the lower bound and top_radius at the upper bound.

### `define-cylinder` — 创建圆柱或圆筒

- 建议定位：在指定 CST 工程中完成“创建圆柱或圆筒”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`name`、`component`、`material`、`outer_radius`、`inner_radius`（0为实心圆柱，非0为圆筒）、`axis`、`axis_min`、`axis_max`、`x_center`、`y_center`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：create-component 或 list-materials（需要时）→ 本工具 → boolean-* / transform-* / save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`component`、`material`、`outer_radius`、`inner_radius`、`axis`、`axis_min`、`axis_max`、`x_center`、`y_center`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `axis`、`axis_min`、`axis_max`、`x_center`、`y_center` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Create a cylinder along an active X/U, Y/V, or Z/W axis. axis_min/axis_max set the axial range; the two transverse centers are mapped to axis-specific VBA setters.

### `define-extrude-curve` — 拉伸闭合曲线

- 建议定位：把闭合、共面的曲线轮廓填充并按指定厚度拉伸为实体。拉伸方向取决于曲线法向；由有序点构成的轮廓应先按点序叉乘确定法向和厚度符号。
- 何时使用：已经存在可由 CST ExtrudeCurve 接受的闭合共面曲线项，并已确定输出实体的组件、材料和厚度时。
- 不要用于：开放或非共面曲线；也不要把本工具当作普通曲线变换。CST 2022 手册说明拉伸后原曲线项不再存在。
- 前置与副作用：必须提供 `project_path`、`name`、`component`、`material`、`curve`、`thickness`；`curve` 应使用 `容器:曲线项` 完整名称，组件与材料必须已经存在。该操作生成实体并消耗原曲线项，会写入 History。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：define-rectangle 或闭合共面的 define-polygon-3d / define-analytical-curve → 本工具 → transform-shape / boolean-*（需要时）→ save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`component`、`material`、`curve`、`thickness`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `curve`、`thickness` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Extrude a closed planar curve. Positive thickness follows its ordered normal (CST 2022 real-machine verified); negative reverses it. Compute the normal and sign first.
- 重点审核：CST 2022 官方文档确认曲线必须闭合且共面，负 thickness 向相反方向拉伸；有序法向规则还包含实机验证事实。

### `define-farfield-monitor` — 创建远场监视器

- 建议定位：按 CST 2022 Monitor Object 为每个频率创建独立单频远场监视器，并读回名称、类型、域和频率验证；子体积完全可选，不含模型专用默认坐标。
- 何时使用：需要在指定频率获得远场结果时，应在启动求解前定义。
- 不要用于：不创建近场 E/H 体监视器，也不依赖几何实体、组件或材料列表；非真空、PEC、色散或有损背景与远场监视器的兼容性需在求解前处理。
- 前置与副作用：必须提供 `project_path`、`name`、`frequencies`；没有实体、组件或材料前置。若需要远场结果，应使用兼容的 Normal/Vacuum 背景。该操作创建监视器并写入 History。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：define-background（仅需修正不兼容背景时）→ 本工具 → set-farfield-plot-cuts（需要自动切面时）→ 完成边界和匹配的求解器配置 → start-simulation / run-experiment → inspect-farfield-monitors 或远场导出工具。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`frequencies`；可选：`enable_nearfield`、`subvolume`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：按 CST 2022 Monitor Object 为每个频率创建独立单频远场监视器，并读回名称、类型、域和频率验证；子体积完全可选，不含模型专用默认坐标。

### `define-loft` — 连接已拾取表面生成 Loft

- 建议定位：在指定 CST 工程中完成“连接已拾取表面生成 Loft”，作为用户建模流程中的一个明确步骤。
- 何时使用：已按顺序拾取两个表面，需要在二者之间生成 Loft 实体时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`name`、`component`、`material`、`tangency`、`minimize_twist`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：对两个目标表面依次使用 pick-face → 本工具 → transform-shape / boolean-*（需要时）→ save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`component`、`material`、`tangency`、`minimize_twist`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Connect two pre-picked surfaces; CST 2022 defines no separate plane-normal argument.
- 重点审核：CST 2022 官方文档只说明连接两个表面；请重点审核两次拾取的顺序及 Tangency。

### `define-material-from-mtd` — 从材料库导入材料

- 建议定位：在指定 CST 工程中完成“从材料库导入材料”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`material_name`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无前置 → 本工具 → 使用该材料的实体创建工具或 change-material → save-project；材料导入本身不进入布尔操作。
- 接口摘要：当前风险 `write`；必填：`project_path`、`material_name`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Define a CST material from .mtd file by material name. Material must exist in references/Materials/. Use list-materials to see available names.

### `define-polygon-3d` — 创建三维多边形曲线

- 建议定位：在 `Curves` 导航树下按点序创建三维多边形曲线项；它不是组件实体，不指定材料。
- 何时使用：用户已明确活动坐标系中的有序点，需要构造三维路径或闭合轮廓时。
- 不要用于：非闭合或非共面的点列不能直接拉伸成实体；曲线本身不能参与 Solid 布尔操作。
- 前置与副作用：必须提供 `project_path`、`name`、`curve`、`points`；当前实现会在 `Curves\curve` 容器不存在时自动创建，不需要组件或材料。该操作创建曲线项并写入 History，不创建实体。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无组件或材料前置 → 本工具 → transform-curve（需要时）；若目标是实体，确认点列闭合且共面 → define-extrude-curve → 生成实体后才可使用 boolean-*。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`curve`、`points`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `points` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Create ordered points in active X/Y/Z or local U/V/W coordinates. For extrusion, close the loop, verify coplanarity, and compute its ordered normal.

### `define-rectangle` — 创建矩形曲线

- 建议定位：在 `Curves` 导航树下、活动 XY 或局部 UV 平面中创建闭合矩形曲线项；它不是组件实体，不指定材料。
- 何时使用：需要闭合平面矩形轮廓，后续用于曲线变换或拉伸成实体时。
- 不要用于：不直接创建带材料的实体，也不能在拉伸前参与 Solid 布尔操作。
- 前置与副作用：必须提供 `project_path`、`name`、`curve`、`x_min`、`x_max`、`y_min`、`y_max`；当前实现会在 `Curves\curve` 容器不存在时自动创建，不需要组件或材料。该操作创建曲线项并写入 History，不创建实体。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无组件或材料前置 → 本工具 → transform-curve（需要时）→ define-extrude-curve（需要实体时）→ 生成实体后才可使用 boolean-*。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`curve`、`x_min`、`x_max`、`y_min`、`y_max`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `x_min`、`x_max`、`y_min`、`y_max` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Create a rectangle in the active XY or local UV plane; calculate bounds in that coordinate system first.

### `define-units` — 设置工程单位

- 建议定位：在指定 CST 工程中完成“设置工程单位”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`length`、`frequency`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：create-blank-project → 本工具 → 参数、几何、边界与求解器配置；应在写入依赖工程单位的尺寸和频率前完成。
- 接口摘要：当前风险 `write`；必填：`project_path`、`length`、`frequency`；可选：`temperature`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `temperature` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Set the CST project unit system.

### `delete-entity` — 删除几何实体

- 建议定位：在指定 CST 工程中完成“删除几何实体”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：只用于用户明确要求的纠错或清理；成功后不要再次删除同一对象。
- 前置与副作用：必须提供 `project_path`、`component`、`name`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：相应 list-* 工具 → 用户确认 → 本工具 → save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`component`、`name`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Delete a geometry entity from the CST project.

### `delete-monitor` — 删除监视器

- 建议定位：在指定 CST 工程中完成“删除监视器”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：只用于用户明确要求的纠错或清理；成功后不要再次删除同一对象。
- 前置与副作用：必须提供 `project_path`、`monitor_name`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：相应 list-* 工具 → 用户确认 → 本工具 → save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`monitor_name`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Delete a monitor by name.

### `delete-probe` — 删除场探针

- 建议定位：在指定 CST 工程中完成“删除场探针”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：只用于用户明确要求的纠错或清理；成功后不要再次删除同一对象。
- 前置与副作用：必须提供 `project_path`、`probe_id`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：相应 list-* 工具 → 用户确认 → 本工具 → save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`probe_id`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Delete a probe by its ID.

### `list-entities` — 列出几何实体

- 建议定位：读取与“列出几何实体”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：需要取得准确的组件或实体名称，供布尔、重命名、变换或删除工具使用时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`、`component`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：根据用户任务在同类工具前后使用；不自动扩展工作流。
- 接口摘要：当前风险 `read`；必填：`project_path`、`component`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：List geometry entities from the verified CST working project.

### `list-materials` — 列出可用材料

- 建议定位：读取与“列出可用材料”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：在 define-material-from-mtd 或 change-material 前需要确认材料库中的合法名称时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 无必填参数，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：根据用户任务在同类工具前后使用；不自动扩展工作流。
- 接口摘要：当前风险 `read`；必填：无；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：List available CST material names from the Materials library.

### `pick-face` — 拾取实体表面

- 建议定位：在指定 CST 工程中完成“拾取实体表面”，作为用户建模流程中的一个明确步骤。
- 何时使用：准备调用 define-loft，且已经明确两个零厚度实体的面 ID 时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`component`、`name`、`face_id`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：已有目标零厚度实体和明确 face_id → 按顺序拾取两个表面 → define-loft。
- 接口摘要：当前风险 `write`；必填：`project_path`、`component`、`name`、`face_id`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Select a face by ID for loft operations (zero-thickness entities only).

### `rename-entity` — 重命名几何实体

- 建议定位：在指定 CST 工程中完成“重命名几何实体”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`old_name`、`new_name`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：已有明确实体名（名称不明确时才使用 list-entities）→ 本工具 → save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`old_name`、`new_name`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Rename a geometry entity.

### `set-background-with-space` — 设置计算域背景间距

- 建议定位：在指定 CST 工程中完成“设置计算域背景间距”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无读取工具前置 → 本工具 → 完成其他边界与匹配的求解器配置 → start-simulation 或 run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`；可选：`x_min_space`、`x_max_space`、`y_min_space`、`y_max_space`、`z_min_space`、`z_max_space`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `x_min_space`、`x_max_space`、`y_min_space`、`y_max_space`、`z_min_space`、`z_max_space` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Add distances to the global X/Y/Z bounds of the calculation volume.

### `set-efield-monitor` — 设置电场监视器

- 建议定位：设置 E-field 监视器；CST 2022 只支持单频，start_freq 必须等于 end_freq。
- 何时使用：需要指定单频电场结果时，应在启动求解前定义。
- 不要用于：只设置 E-field 监视器；E/H 通用入口使用 set-field-monitor，远场使用 define-farfield-monitor。
- 前置与副作用：必须提供 `project_path`、`start_freq`、`end_freq`、`step`；没有实体、组件或材料前置。该操作创建电场监视器并写入 History。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无建模前置 → 本工具 → 完成边界和匹配的求解器配置 → start-simulation / run-experiment → list-field-results → export-e-field。
- 接口摘要：当前风险 `write`；必填：`project_path`、`start_freq`、`end_freq`、`step`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `start_freq`、`end_freq` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：设置 E-field 监视器；CST 2022 只支持单频，start_freq 必须等于 end_freq。

### `set-entity-color` — 设置实体显示颜色

- 建议定位：在指定 CST 工程中完成“设置实体显示颜色”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`shape_name`、`r`、`g`、`b`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：已有明确实体名（名称不明确时才使用 list-entities）→ 本工具 → save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`shape_name`、`r`、`g`、`b`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Set the display color of a geometry entity.

### `set-farfield-plot-cuts` — 设置远场绘图切面

- 建议定位：按 CST 2022 FarfieldPlot.AddCut 定义自动一维远场切面；求解后 CST 会对全部远场监视器评估这些切面，并把结果放在 `Farfields\Farfield Cuts`。
- 何时使用：需要在下一次求解后自动生成固定 theta 或 phi 的远场切面时，应在启动求解前设置。
- 不要用于：不依赖 list-entities 或 list-materials，也不是对既有导出文件作图；没有远场监视器时不会生成远场切面结果。
- 前置与副作用：必须提供 `project_path`。调用时不要求已有求解结果，但求解前至少应定义一个远场监视器；该操作清除已有自动切面定义并写入新的 FarfieldPlot 切面设置。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：define-farfield-monitor → 本工具 → 完成边界和匹配的求解器配置 → start-simulation / run-experiment → inspect-farfield-monitors 或远场导出工具。
- 接口摘要：当前风险 `write`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Set farfield plot cut angles.

### `set-field-monitor` — 设置电场或磁场监视器

- 建议定位：设置 E/H 场监视器；CST 2022 只支持单频。
- 何时使用：需要指定单频 E/H 场结果时，应在启动求解前定义。
- 不要用于：只设置单频 E/H 场监视器，不创建远场监视器或内部点探针。
- 前置与副作用：必须提供 `project_path`、`field_type`、`start_frequency`、`end_frequency`、`num_samples`；没有实体、组件或材料前置。该操作创建 E-field 或 H-field 监视器并写入 History。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无建模前置 → 本工具 → 完成边界和匹配的求解器配置 → start-simulation / run-experiment → list-field-results → 对应场导出工具。
- 接口摘要：当前风险 `write`；必填：`project_path`、`field_type`、`start_frequency`、`end_frequency`、`num_samples`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `start_frequency`、`end_frequency`、`num_samples` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：设置 E/H 场监视器；CST 2022 只支持单频。

### `set-probe` — 设置内部场探针

- 建议定位：在指定 CST 工程中完成“设置内部场探针”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：用于全局坐标中的内部点探针，不替代体/面场监视器。
- 前置与副作用：必须提供 `project_path`、`field_type`、`x_pos`、`y_pos`、`z_pos`；没有实体、组件或材料前置，但应由用户确认全局坐标位置。该操作创建内部场探针并写入 History。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无建模前置 → 本工具 → 完成边界和匹配的求解器配置 → start-simulation / run-experiment → analyze-probes 或 run-probe-phase。
- 接口摘要：当前风险 `write`；必填：`project_path`、`field_type`、`x_pos`、`y_pos`、`z_pos`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `x_pos`、`y_pos`、`z_pos` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Set an internal E/H-field probe at a global X/Y/Z position.

### `show-bounding-box` — 切换包围盒显示

- 建议定位：在指定 CST 工程中完成“切换包围盒显示”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：根据用户任务在同类工具前后使用；不自动扩展工作流。
- 接口摘要：当前风险 `write`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Toggle bounding box display.

### `transform-curve` — 镜像变换曲线

- 建议定位：在指定 CST 工程中完成“镜像变换曲线”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`curve_name`、`center_x`、`center_y`、`center_z`、`plane_normal_x`、`plane_normal_y`、`plane_normal_z`，且目标曲线已存在；不需要组件或材料。该操作变换曲线并写入 History，结果仍是曲线而非实体。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：define-analytical-curve / define-polygon-3d / define-rectangle → 本工具 → define-extrude-curve（闭合共面且需要实体时）或 save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`、`curve_name`、`center_x`、`center_y`、`center_z`、`plane_normal_x`、`plane_normal_y`、`plane_normal_z`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `center_x`、`center_y`、`center_z`、`plane_normal_x`、`plane_normal_y`、`plane_normal_z` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Mirror a curve using Center and PlaneNormal in active X/Y/Z or local U/V/W coordinates; compute both first.

### `transform-shape` — 镜像或旋转实体

- 建议定位：在指定 CST 工程中完成“镜像或旋转实体”，作为用户建模流程中的一个明确步骤。
- 何时使用：模型拓扑、材料、坐标或监视器需求已经由用户确定，并进入相应建模步骤时。
- 不要用于：不替用户决定结构尺寸、材料或拓扑；坐标系和单位不明确时必须先询问。
- 前置与副作用：必须提供 `project_path`、`shape_name`、`transform_type`、`center_x`、`center_y`、`center_z`、`plane_normal_x`、`plane_normal_y`、`plane_normal_z`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：已有明确实体名（名称不明确时才使用 list-entities）→ 本工具 → boolean-*（需要时）→ save-project；曲线变换应使用 transform-curve。
- 接口摘要：当前风险 `write`；必填：`project_path`、`shape_name`、`transform_type`、`center_x`、`center_y`、`center_z`、`plane_normal_x`、`plane_normal_y`、`plane_normal_z`；可选：`angle_x`、`angle_y`、`angle_z`、`multiple_objects`、`group_objects`、`repetitions`、`destination`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `transform_type`、`center_x`、`center_y`、`center_z`、`plane_normal_x`、`plane_normal_y`、`plane_normal_z`、`angle_x`、`angle_y`、`angle_z`、`multiple_objects`、`group_objects`、`repetitions`、`destination` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Mirror uses PlaneNormal; rotate uses Angle. Center and components use active X/Y/Z or local U/V/W coordinates. Required plane_normal fields do not define a rotate axis.

## 扫参与优化（`optimization`，11 个）

> 本类辅助参数筛选和优化，不能自行定义物理目标、参数范围或最终结构，停止条件仍由用户决定。

### `analyze-probes` — 分析探针试验结果

- 建议定位：完成“分析探针试验结果”，为用户主导的参数筛选或优化循环提供一次辅助操作。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只分析已提供的探针试验数据，不创建或运行试验。
- 前置与副作用：必须提供 `parameters`、`probes`，并保证引用的工程、对象或文件真实存在；可能写入 Optuna 存储、试验文件、工程副本或仿真结果。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：create-study 或 design-probes → 本工具 → best-study 或 study-terminate-check。
- 接口摘要：当前风险 `read`；必填：`parameters`、`probes`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。研究、trial、参数范围或目标值不一致时停止本轮，不自行改变用户目标。
- 当前 Registry：Analyze probe results: compute main effects and two-way interactions. Input must include the parameter values and the objective value for each probe.

### `ask-study` — 获取下一组优化参数

- 建议定位：完成“获取下一组优化参数”，为用户主导的参数筛选或优化循环提供一次辅助操作。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：不是只读查询：Optuna ask 会为研究创建或预留 trial，成功后不要无故重复调用。
- 前置与副作用：必须提供 `storage_path`、`study_name`，并保证引用的工程、对象或文件真实存在；可能写入 Optuna 存储、试验文件、工程副本或仿真结果。
- 成功与重试：成功后不要重复 ask；应先完成或明确终止已创建的 trial。
- 关联流程：create-study → ask-study → prepare-experiment 或 run-optimization-step → tell-study。
- 接口摘要：当前风险 `read`；必填：`storage_path`、`study_name`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。研究、trial、参数范围或目标值不一致时停止本轮，不自行改变用户目标。
- 当前 Registry：Ask the study for the next trial parameter suggestion.
- 重点审核：当前 Registry 风险值为 read，但实际会持久化 trial；代码回填时应重新核对风险元数据。

### `best-study` — 读取当前最佳试验

- 建议定位：读取与“读取当前最佳试验”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `storage_path`、`study_name`，并保证引用的工程、对象或文件真实存在；可能写入 Optuna 存储、试验文件、工程副本或仿真结果。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：create-study 或 design-probes → 本工具 → best-study 或 study-terminate-check。
- 接口摘要：当前风险 `read`；必填：`storage_path`、`study_name`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。研究、trial、参数范围或目标值不一致时停止本轮，不自行改变用户目标。
- 当前 Registry：Get current best result. For multi-objective returns Pareto front samples.

### `create-study` — 创建或载入优化研究

- 建议定位：完成“创建或载入优化研究”，为用户主导的参数筛选或优化循环提供一次辅助操作。
- 何时使用：用户已经定义参数、范围、目标函数和预算，正在执行筛选或优化循环时。
- 不要用于：不替用户确定物理目标、搜索范围、试验预算或最终停止结论。
- 前置与副作用：必须提供 `storage_path`、`study_name`、`parameters`，并保证引用的工程、对象或文件真实存在；可能写入 Optuna 存储、试验文件、工程副本或仿真结果。
- 成功与重试：成功后不要重复写入；失败时修正明确参数或路径后再重试。
- 关联流程：create-study → ask-study → 运行试验 → tell-study → best-study 或 study-terminate-check。
- 接口摘要：当前风险 `filesystem-write`；必填：`storage_path`、`study_name`、`parameters`；可选：`direction`、`directions`、`value_names`、`constraints`、`sampler`、`n_startup_trials`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：代码回填时保留现有 Schema 对 `parameters`、`direction`、`directions`、`value_names`、`constraints` 的限定。研究、trial、参数范围或目标值不一致时停止本轮，不自行改变用户目标。
- 当前 Registry：Create or load an Optuna optimization study. Supports single-objective, multi-objective (directions), and constraint-enabled studies.

### `design-probes` — 设计参数筛选试验

- 建议定位：完成“设计参数筛选试验”，为用户主导的参数筛选或优化循环提供一次辅助操作。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只生成筛选试验计划，不运行 CST；完整执行使用 run-probe-phase。
- 前置与副作用：必须提供 `parameters`、`max_probes`、`include_center`，并保证引用的工程、对象或文件真实存在；可能写入 Optuna 存储、试验文件、工程副本或仿真结果。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：design-probes → prepare-experiment + run-experiment → analyze-probes。
- 接口摘要：当前风险 `read`；必填：`parameters`、`max_probes`、`include_center`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：几何数值必须服从工具声明的全局或活动坐标系和工程单位。研究、trial、参数范围或目标值不一致时停止本轮，不自行改变用户目标。
- 当前 Registry：Design a Plackett-Burman probe plan to screen parameters. Returns a list of experiments; run each via prepare-experiment + run-experiment, then feed results to analyze-probes.

### `run-optimization-step` — 运行一次优化迭代

- 建议定位：完成“运行一次优化迭代”，为用户主导的参数筛选或优化循环提供一次辅助操作。
- 何时使用：用户已经定义参数、范围、目标函数和预算，正在执行筛选或优化循环时。
- 不要用于：不替用户确定物理目标、搜索范围、试验预算或最终停止结论。
- 前置与副作用：必须提供 `project_path`、`completion_result_paths`、`study_storage`、`study_name`，并保证引用的工程、对象或文件真实存在；可能写入 Optuna 存储、试验文件、工程副本或仿真结果。
- 成功与重试：成功后不要立即重复启动；超时或状态不明时先检查运行状态、日志或结果节点。
- 关联流程：create-study → run-optimization-step（循环）→ best-study 或 study-terminate-check。
- 接口摘要：当前风险 `long-running`；必填：`project_path`、`completion_result_paths`、`study_storage`、`study_name`；可选：`objective`、`sampler`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `project_path`、`completion_result_paths`、`study_storage`、`study_name`、`objective`、`sampler` 的限定。研究、trial、参数范围或目标值不一致时停止本轮，不自行改变用户目标。
- 当前 Registry：Run one optimization iteration: ask Optuna for next parameters, apply them, simulate, compute objective, and report back. Agent inspects the objective_value output to decide whether to stop or continue the loop. Objective spec supports metasurface metrics: {"type": "s11_min_db"} | {"type": "s11_at_freq", "freq": 10} | {"type": "gain_max"} | {"type": "bandwidth", "below_db": -10} | {"type": "amp_at_freq", "result_path": "zmax(1)", "freq": 10, "direction": "maximize"} | {"type": "phase_at_freq", "result_path": "zmax(1)", "freq": 10, "target_deg": 90} | {"type": "expression", "expr": "abs(wrap(phase_deg('zmax(1)', 10) - 90))"}; expression sandbox exposes s11_db/s11_freq, amp_db(path,f), phase_deg(path,f), wrap(x), min/max/len/abs.

### `run-probe-phase` — 运行完整参数筛选阶段

- 建议定位：完成“运行完整参数筛选阶段”，为用户主导的参数筛选或优化循环提供一次辅助操作。
- 何时使用：用户已经定义参数、范围、目标函数和预算，正在执行筛选或优化循环时。
- 不要用于：不替用户确定物理目标、搜索范围、试验预算或最终停止结论。
- 前置与副作用：必须提供 `project_path`、`completion_result_paths`、`parameters`、`study_storage`、`study_name`，并保证引用的工程、对象或文件真实存在；可能写入 Optuna 存储、试验文件、工程副本或仿真结果。
- 成功与重试：成功后不要立即重复启动；超时或状态不明时先检查运行状态、日志或结果节点。
- 关联流程：design-probes、run-experiment、analyze-probes 的批量封装；后续进入优化研究。
- 接口摘要：当前风险 `long-running`；必填：`project_path`、`completion_result_paths`、`parameters`、`study_storage`、`study_name`；可选：`max_probes`、`include_center`、`objective`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `project_path`、`completion_result_paths`、`parameters`、`study_storage`、`study_name`、`max_probes`、`include_center`、`objective` 的限定。研究、trial、参数范围或目标值不一致时停止本轮，不自行改变用户目标。
- 当前 Registry：Run the complete probe phase: design Plackett-Burman probes, simulate each (on a main-file-only working_probe.cst copy; companion dir is recreated by CST on first open), analyze main effects and interactions, then inject results into an Optuna study. Returns top_params, edge_hit, and suggested_algorithm. Objective spec supports metasurface metrics: {"type": "s11_min_db"} | {"type": "s11_at_freq", "freq": 10} | {"type": "gain_max"} | {"type": "bandwidth", "below_db": -10} | {"type": "amp_at_freq", "result_path": "zmax(1)", "freq": 10, "direction": "maximize"} | {"type": "phase_at_freq", "result_path": "zmax(1)", "freq": 10, "target_deg": 90} | {"type": "expression", "expr": "abs(wrap(phase_deg('zmax(1)', 10) - 90))"}; expression sandbox exposes s11_db/s11_freq, amp_db(path,f), phase_deg(path,f), wrap(x), min/max/len/abs.

### `study-add-trials` — 导入已有试验

- 建议定位：完成“导入已有试验”，为用户主导的参数筛选或优化循环提供一次辅助操作。
- 何时使用：用户已经定义参数、范围、目标函数和预算，正在执行筛选或优化循环时。
- 不要用于：不替用户确定物理目标、搜索范围、试验预算或最终停止结论。
- 前置与副作用：必须提供 `storage_path`、`study_name`、`trials`，并保证引用的工程、对象或文件真实存在；可能写入 Optuna 存储、试验文件、工程副本或仿真结果。
- 成功与重试：成功后不要重复写入；失败时修正明确参数或路径后再重试。
- 关联流程：create-study 或 design-probes → 本工具 → best-study 或 study-terminate-check。
- 接口摘要：当前风险 `filesystem-write`；必填：`storage_path`、`study_name`、`trials`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。研究、trial、参数范围或目标值不一致时停止本轮，不自行改变用户目标。
- 当前 Registry：Inject pre-computed trials (e.g. from manual grid scan) into a study. Each trial: {params, values, constraints?}.

### `study-param-importances` — 分析参数重要性

- 建议定位：完成“分析参数重要性”，为用户主导的参数筛选或优化循环提供一次辅助操作。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `storage_path`、`study_name`，并保证引用的工程、对象或文件真实存在；可能写入 Optuna 存储、试验文件、工程副本或仿真结果。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：create-study 或 design-probes → 本工具 → best-study 或 study-terminate-check。
- 接口摘要：当前风险 `read`；必填：`storage_path`、`study_name`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。研究、trial、参数范围或目标值不一致时停止本轮，不自行改变用户目标。
- 当前 Registry：Analyze which parameters most affect the objective. Requires at least 5 completed trials.

### `study-terminate-check` — 检查优化终止条件

- 建议定位：完成“检查优化终止条件”，为用户主导的参数筛选或优化循环提供一次辅助操作。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `storage_path`、`study_name`，并保证引用的工程、对象或文件真实存在；可能写入 Optuna 存储、试验文件、工程副本或仿真结果。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：create-study 或 design-probes → 本工具 → best-study 或 study-terminate-check。
- 接口摘要：当前风险 `read`；必填：`storage_path`、`study_name`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。研究、trial、参数范围或目标值不一致时停止本轮，不自行改变用户目标。
- 当前 Registry：Check if optimization has converged using Optuna's regret-bound evaluator. Returns should_terminate.

### `tell-study` — 回报优化试验结果

- 建议定位：完成“回报优化试验结果”，为用户主导的参数筛选或优化循环提供一次辅助操作。
- 何时使用：用户已经定义参数、范围、目标函数和预算，正在执行筛选或优化循环时。
- 不要用于：只回报已有 trial 的结果，不负责运行 CST 或计算物理目标。
- 前置与副作用：必须提供 `storage_path`、`study_name`、`trial_number`，并保证引用的工程、对象或文件真实存在；可能写入 Optuna 存储、试验文件、工程副本或仿真结果。
- 成功与重试：成功后不要重复写入；失败时修正明确参数或路径后再重试。
- 关联流程：ask-study → 运行并计算目标 → tell-study → best-study 或 study-param-importances。
- 接口摘要：当前风险 `filesystem-write`；必填：`storage_path`、`study_name`、`trial_number`；可选：`value`、`values`、`constraints`、`state`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：代码回填时保留现有 Schema 对 `trial_number`、`value`、`values`、`constraints`、`state` 的限定。研究、trial、参数范围或目标值不一致时停止本轮，不自行改变用户目标。
- 当前 Registry：Report trial result. Provide exactly one of value (single-objective) or values (multi-objective); state is complete or pruned.

## 工程身份与锁定状态（`project_identity`，4 个）

> 本类只确认目标工程和锁状态；不应作为每个普通成功调用前后的固定检查。

### `infer-run-dir` — 推断运行目录

- 建议定位：完成“推断运行目录”，返回后续步骤所需的信息。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：cst-session-inspect → 本工具 → 需要的会话或工程操作。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：Infer run_dir from a projects/working.cst project path.

### `list-open-projects` — 列出已打开的 CST 工程

- 建议定位：读取与“列出已打开的 CST 工程”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 无必填参数，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：cst-session-inspect → 本工具 → 需要的会话或工程操作。
- 接口摘要：当前风险 `read`；必填：无；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：List CST projects visible through DesignEnvironment.connect_to_any().

### `verify-project-identity` — 核对目标工程身份

- 建议定位：完成“核对目标工程身份”，返回后续步骤所需的信息。
- 何时使用：确实存在多个工程、路径歧义或会话归属风险时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：cst-session-inspect → 本工具 → 需要的会话或工程操作。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：Verify the expected project is the sole open CST project before writes.

### `wait-project-unlocked` — 等待工程文件解锁

- 建议定位：完成“等待工程文件解锁”，返回后续步骤所需的信息。
- 何时使用：关闭或保存工程后，下一步必须访问磁盘文件且锁仍存在时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`、`timeout_seconds`、`poll_interval_seconds`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：cst-session-inspect → 本工具 → 需要的会话或工程操作。
- 接口摘要：当前风险 `read`；必填：`project_path`、`timeout_seconds`、`poll_interval_seconds`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：Wait for a project companion directory to have no .lok files.

## 工程配置与求解控制（`project_ops`，35 个）

> 本类配置工程或控制求解器；重点审核边界、激励、端口、网格和同步/异步语义。
> 启动前门槛：必须显式选择当前求解器，完成与该类型匹配的求解器配置，并完成背景/计算域边界设置；端口、激励、监视器和网格再按本次任务需要配置。`inspect-*` 和 `list-*` 只在用户需要核对或排错时调用，不是固定前置。
> `configure-frequency-domain-solver` 自身会切换到 `HF Frequency Domain`；`define-fdsolver-stimulation` 和 `set-fdsolver-extrude-open-bc` 不会切换，只能用于当前频域求解器。`define-solver` 和当前实现的 `set-solver-acceleration` 写入 Solver Object，应先切换到 `HF Time Domain`。

### `capture-3d-view` — 导出 CST 三维视图

- 建议定位：在指定 CST 工程中完成“导出 CST 三维视图”，用于配置或控制本次仿真。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：用于保存截图；需要把 PNG 返回给 Agent 观察时使用 inspect-model-view。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：模型处于需要记录或观察的状态 → 本工具 → inspect-model-view（需要把图像交给 Agent 观察时）或直接使用导出的 PNG。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`；可选：`output_dir`、`filename_prefix`、`view_type`、`preset_name`、`horizontal_rotation_deg`、`vertical_rotation_deg`、`return_image_data`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；输出路径应由调用方明确指定；代码回填时保留现有 Schema 对 `project_path`、`output_dir`、`filename_prefix`、`view_type`、`preset_name`、`horizontal_rotation_deg`、`vertical_rotation_deg`、`return_image_data` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Export the current 3D sheet to PNG. Use a CST reserved view or relative horizontal/vertical rotations from Front.

### `change-parameter` — 修改单个 CST 参数

- 建议定位：在指定 CST 工程中完成“修改单个 CST 参数”，用于配置或控制本次仿真。参数支持数字以及表达式/字符串，但表达式/字符串必须最终可以转换为数字。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：只修改单个参数，不负责运行求解；批量写入使用 define-parameters 或 prepare-experiment。
- 前置与副作用：必须提供 `project_path`、`name`、`value`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：参数名不明确时才使用 list-parameters → 本工具 → save-project，或在全部启动前配置完成后进入 start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`、`name`、`value`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Change one CST parameter in the verified working project.

### `change-solver-type` — 切换求解器类型

- 建议定位：显式切换 CST 当前求解器类型，为后续调用对应的 Solver、FDSolver 或其他求解器专用配置建立上下文。
- 何时使用：用户已经选定求解方法，且后续需要调用该类型的专用配置工具时；应在启动仿真前完成。
- 不要用于：切换类型本身不完成求解器参数、边界、端口、激励或监视器配置。
- 前置与副作用：必须提供 `project_path`、`solver_type`；没有 inspect-project 或 list-parameters 前置。该操作改变当前求解器上下文并写入 History，后续只能使用与之匹配的配置工具。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：用户确定求解器类型 → 本工具 → 对应求解器配置 → define-background / define-boundary（或 define-unit-cell-boundary）→ 端口、激励和监视器 → start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`、`solver_type`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Change the CST solver type.

### `configure-frequency-domain-solver` — 配置频域求解器基础设置

- 建议定位：仅切换 HF Frequency Domain、设置 mesh_method 和激励；不会生成 FDSolver.Reset，也不改精度、扫频或自适应设置。
- 何时使用：已经决定使用高频频域求解器，并已明确网格方法及端口、Floquet 或平面波激励策略时。
- 不要用于：不配置时域求解器；也不替代边界、频率范围、端口/Floquet/平面波源和监视器定义。
- 前置与副作用：必须提供 `project_path`、`mesh_method`、`excitation`；所引用的端口、Floquet 模式或平面波源应已定义。该工具会自行切换到 `HF Frequency Domain`，再写入 FDSolver 网格方法和激励，不需要先调用 change-solver-type。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：先按任务定义普通端口、Unit Cell + Floquet 或 PlaneWave → 本工具 → define-fdsolver-stimulation / set-fdsolver-extrude-open-bc（需要时）→ 完成背景、边界和监视器 → start-simulation / run-experiment。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`mesh_method`、`excitation`；可选：无；关键返回：`project_path`、`solver_type`、`mesh_method`、`excitation`、`untouched_settings`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `project_path`、`excitation` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：仅切换 HF Frequency Domain、设置 mesh_method 和激励；不会生成 FDSolver.Reset，也不改精度、扫频或自适应设置。

### `define-background` — 设置背景材料

- 建议定位：设置背景类型与材料参数（Normal 时显式写出 ε/μ，默认 1.0/1.0 等价 Vacuum）。CST 2022 手册的 Background 对象无读取接口，因此返回 requested 值与 farfield_compatible 判定（基于请求值），并把状态登记为运行时跟踪，供 get-background 返回；无法读回 GUI 中的修改。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：设置背景材料，不设置计算域外扩距离；外扩距离使用 set-background-with-space。
- 前置与副作用：必须提供 `project_path`；没有 inspect-project、list-parameters、实体或材料列表前置。该操作设置计算域背景并写入 History；若需要远场监视器，应使用兼容的 Normal/Vacuum 背景。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无读取工具前置 → 本工具 → set-background-with-space / define-boundary（或 define-unit-cell-boundary）→ 完成匹配的求解器配置 → start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`；可选：`background_type`、`epsilon`、`mu`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `background_type`、`epsilon`、`mu` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：设置背景类型与材料参数（Normal 时显式写出 ε/μ，默认 1.0/1.0 等价 Vacuum）。CST 2022 手册的 Background 对象无读取接口，因此返回 requested 值与 farfield_compatible 判定（基于请求值），并把状态登记为运行时跟踪，供 get-background 返回；无法读回 GUI 中的修改。

### `define-boundary` — 设置通用边界

- 建议定位：设置全部面的通用边界和对称性；该工具不等价于完整的 Unit Cell 或 Floquet 配置，周期单元应使用 define-unit-cell-boundary 并配合 define-floquet-port。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：只配置通用六面边界和对称性，不等价于完整 Unit Cell 与 Floquet 配置。
- 前置与副作用：必须提供 `project_path`；没有 inspect-project、list-parameters 或几何列表前置。该操作设置六个计算域边界面和对称性并写入 History，是启动求解前必须完成的边界设置之一。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无读取工具前置 → 本工具 → 选择求解器并完成匹配配置 → 端口、激励和监视器 → start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`；可选：`face_type`、`symmetry_type`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `face_type`、`symmetry_type` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：设置全部面的通用边界和对称性；该工具不等价于完整的 Unit Cell 或 Floquet 配置。高级周期边界需求应由用户在 CST 图形界面中手动完成。

### `define-fdsolver-stimulation` — 设置频域求解器激励

- 建议定位：依据本机 CST 2022 FDSolver.Stimulation 手册设置激励，不会隐式执行 FDSolver.Reset。该工具可由 MCP Agent 调用，但暴露状态不代表已完成 CST 2022 实机验收。
- 何时使用：当前已经是 `HF Frequency Domain`，且需要单独修改 FDSolver 使用的端口和模式激励时。
- 不要用于：当前为 `HF Time Domain` 或其他求解器时不得调用；本工具也不创建端口或 Floquet 模式。
- 前置与副作用：必须提供 `project_path`、`port`、`mode`；当前求解器必须为 `HF Frequency Domain`，被引用的普通端口或 Floquet 模式必须已存在。该操作只写入 FDSolver.Stimulation，不切换求解器且不执行 FDSolver.Reset。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：configure-frequency-domain-solver → 本工具（需要覆盖激励时）→ 完成边界和监视器 → start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`、`port`、`mode`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `port`、`mode` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：依据本机 CST 2022 FDSolver.Stimulation 手册设置激励，不会隐式执行 FDSolver.Reset。该工具可由 MCP Agent 调用，但暴露状态不代表已完成 CST 2022 实机验收。

### `define-floquet-port` — 配置 Floquet 端口

- 建议定位：配置 Zmin/Zmax Floquet 端口、显式或自动模式、参考面、极化基础和排序。仅公开 getter 可读字段会被验收。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：只用于周期结构 Zmin/Zmax 的 Floquet 端口，不替代普通波导端口。
- 前置与副作用：必须提供 `project_path`、`ports`；周期单元的 X/Y 边界应已通过 define-unit-cell-boundary 配置。该操作配置 Zmin/Zmax Floquet 端口并写入 History。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：define-unit-cell-boundary → 本工具 → configure-frequency-domain-solver（选择含 Floquet 的激励）→ 监视器 → start-simulation / run-experiment。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`ports`；可选：`polarization_basis`、`sort_code`、`sort_frequency`、`sort_theta`、`sort_phi`、`max_order_x`、`max_order_yprime`；关键返回：`project_path`、`requested`、`actual`、`unverified_fields`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `project_path` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：配置 Zmin/Zmax Floquet 端口、显式或自动模式、参考面、极化基础和排序。仅公开 getter 可读字段会被验收。
- 重点审核：CST 2022 官方文档限定 Zmin/Zmax，并说明其用于无限阵列 Unit Cell；请审核模式排序和参考面含义。

### `define-frequency-range` — 设置仿真频率范围

- 建议定位：在指定 CST 工程中完成“设置仿真频率范围”，用于配置或控制本次仿真。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `project_path`、`start_freq`、`end_freq`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：选择求解器类型 → 本工具 → 匹配的求解器、边界、激励和监视器配置 → start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`、`start_freq`、`end_freq`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Set the simulation frequency range.

### `define-mesh` — 设置六面体网格参数

- 建议定位：在指定 CST 工程中完成“设置六面体网格参数”，用于配置或控制本次仿真。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `project_path`、`steps_per_wave_near`、`steps_per_wave_far`、`steps_per_box_near`、`steps_per_box_far`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：选择支持六面体网格的求解器和网格方法 → 本工具 → set-mesh-fpbavoid-nonreg-unite / set-mesh-minimum-step-number（需要时）→ start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`、`steps_per_wave_near`、`steps_per_wave_far`、`steps_per_box_near`、`steps_per_box_far`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Configure the hexahedral mesh parameters.

### `define-parameters` — 批量定义 CST 参数

- 建议定位：在指定 CST 工程中完成“批量定义 CST 参数”，用于配置或控制本次仿真。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：用于成批创建或覆盖参数；只改一个既有参数时使用 change-parameter。
- 前置与副作用：必须提供 `project_path`、`names`、`values`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：用户给出参数名和值 → 本工具 → 使用这些参数完成几何和求解配置；扫参时再进入 prepare-experiment / quick-sweep。
- 接口摘要：当前风险 `write`；必填：`project_path`、`names`、`values`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；`names` 与 `values` 必须一一对应。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Batch-define multiple CST parameters using StoreParameters.

### `define-plane-wave` — 创建平面波源

- 建议定位：创建真实 PlaneWave 源。普通平面波不产生 S 参数；无限周期单元应使用 Unit Cell 与 Floquet。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：普通平面波不会自动产生端口 S 参数；无限周期单元通常使用 Unit Cell 与 Floquet 端口。
- 前置与副作用：必须提供 `project_path`、`normal`、`e_vector`；不依赖实体或材料列表，但应在求解前完成与平面波传播相容的开放边界和求解器激励配置。该操作创建 PlaneWave 源并写入 History。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：define-boundary（开放边界）→ 本工具 → configure-frequency-domain-solver（Plane Wave 激励）或其他兼容求解器配置 → 监视器 → start-simulation / run-experiment。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`normal`、`e_vector`；可选：`polarization`、`reference_frequency`、`handedness`、`phase_difference`、`axial_ratio`；关键返回：`project_path`、`requested`、`actual`、`unverified_fields`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `project_path` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：创建真实 PlaneWave 源。普通平面波不产生 S 参数；无限周期单元应使用 Unit Cell 与 Floquet。

### `define-port` — 创建内部波导端口

- 建议定位：在指定 CST 工程中完成“创建内部波导端口”，用于配置或控制本次仿真。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：用于内部轴对齐波导端口，不用于 Floquet 端口或普通平面波。
- 前置与副作用：必须提供 `project_path`、`port_number`、`x_min`、`x_max`、`y_min`、`y_max`、`z_min`、`z_max`、`orientation`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：几何和端口截面已明确 → 本工具 → 与当前求解器匹配的端口激励配置 → 完成边界和监视器 → start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`、`port_number`、`x_min`、`x_max`、`y_min`、`y_max`、`z_min`、`z_max`、`orientation`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；几何数值必须服从工具声明的全局或活动坐标系和工程单位；代码回填时保留现有 Schema 对 `x_min`、`x_max`、`y_min`、`y_max`、`z_min`、`z_max`、`orientation` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Define an internal axis-aligned waveguide port from global X/Y/Z ranges. Collapse the normal-axis range to the port plane; *min radiates +axis and *max radiates -axis.
- 重点审核：请重点审核 orientation 与端口辐射方向说明。

### `define-solver` — 配置时域求解器

- 建议定位：通过 CST Solver Object 配置高频时域求解器的激励端口、稳态阈值、网格自适应和阻抗归一化等设置；本工具本身不切换求解器类型。
- 何时使用：已经明确选择 `HF Time Domain`，并需要配置时域求解器参数时。
- 不要用于：当前为 `HF Frequency Domain` 时不得调用；频域配置使用 configure-frequency-domain-solver、define-fdsolver-stimulation 等 FDSolver 工具。
- 前置与副作用：必须提供 `project_path`、`stimulation_port`、`steady_state_limit`、`norming_impedance`；应先用 change-solver-type 切换到 `HF Time Domain`，相关端口应已存在。该操作写入 Solver Object 设置和 History。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：change-solver-type（`HF Time Domain`）→ 本工具 → define-background / define-boundary → 端口、监视器与网格配置 → start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`、`stimulation_port`、`steady_state_limit`、`norming_impedance`；可选：`stimulation_mode`、`mesh_adaption`、`auto_norm_impedance`、`calculate_modes_only`、`s_para_symmetry`、`store_td_results`、`run_discretizer_only`、`full_deembedding`、`superimpose_plw`、`use_sensitivity`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Configure the time-domain solver settings.

### `define-unit-cell-boundary` — 配置 Unit Cell 边界

- 建议定位：按 CST 2022 手册配置六面边界和 Unit Cell 扫描角；先校验 X/Y 配对，执行后再通过 getter 读回。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：用于周期单元边界；普通开放、电或磁边界使用 define-boundary。
- 前置与副作用：必须提供 `project_path`、`xmin`、`xmax`、`ymin`、`ymax`、`zmin`、`zmax`；没有 inspect-project 或 list-parameters 前置，但 X/Y 周期边界必须成对且由用户明确扫描角。该操作写入 Unit Cell 边界和 History。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：无读取工具前置 → 本工具 → define-floquet-port → 选择并配置兼容求解器 → 监视器 → start-simulation / run-experiment。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`xmin`、`xmax`、`ymin`、`ymax`、`zmin`、`zmax`；可选：`theta`、`phi`、`direction`；关键返回：`project_path`、`requested`、`actual`、`unverified_fields`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `project_path` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：按 CST 2022 手册配置六面边界和 Unit Cell 扫描角；先校验 X/Y 配对，执行后再通过 getter 读回。
- 重点审核：请重点审核 X/Y 周期配对、扫描角和 Z 面边界组合。

### `get-background` — 读取 Runtime 跟踪的背景状态

- 建议定位：返回本会话运行时跟踪的背景状态（source=runtime_tracked）与 farfield_compatible 判定（远场监视器要求 Normal 且 ε=1、μ=1）。CST 2022 手册的 Background 对象未提供任何读取接口，本工具不调用未文档化的属性读取；没有跟踪状态时返回 background_state_unknown，需先调用 define-background 显式设置背景。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只能返回本 Runtime 会话跟踪的设置，不能读到用户在 CST GUI 中直接改动后的背景值。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：仅在用户要求核对本会话由 define-background 写入的状态或排错时调用；无跟踪状态时直接显式设置背景，不把本工具作为启动前固定步骤。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：返回本会话运行时跟踪的背景状态（source=runtime_tracked）与 farfield_compatible 判定（远场监视器要求 Normal 且 ε=1、μ=1）。CST 2022 手册的 Background 对象未提供任何读取接口，本工具不调用未文档化的属性读取；没有跟踪状态时返回 background_state_unknown，需先调用 define-background 显式设置背景。

### `inspect-boundary` — 读取实际边界状态

- 建议定位：使用 Boundary 六面 getter 和 GetUnitCellScanAngle 读取实际边界状态。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：仅在用户要求核对、存在边界歧义或排错时，于 define-boundary / define-unit-cell-boundary 后调用；不要把它作为每次启动求解前的固定步骤。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：`project_path`、`faces`、`unit_cell_scan`、`ports`、`plane_wave`、`monitors`、`count`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `project_path` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：使用 Boundary 六面 getter 和 GetUnitCellScanAngle 读取实际边界状态。

### `inspect-floquet-ports` — 读取 Floquet 端口状态

- 建议定位：读取 Floquet 端口位置、模式序号/名称、模式列表及考虑模式数；不伪造无 getter 字段。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：仅在用户要求核对或排错时，于 define-unit-cell-boundary / define-floquet-port 后调用；不要作为每次求解的固定前置。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：`project_path`、`faces`、`unit_cell_scan`、`ports`、`plane_wave`、`monitors`、`count`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `project_path` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：读取 Floquet 端口位置、模式序号/名称、模式列表及考虑模式数；不伪造无 getter 字段。

### `inspect-model-view` — 导出并返回三维模型视图

- 建议定位：读取与“导出并返回三维模型视图”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：会生成截图并返回图像数据；只需保存 PNG 时使用 capture-3d-view。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：capture-3d-view（返回图像或已知输出路径）→ 本工具 → 根据用户目标继续建模、记录证据或人工判断；不自动启动求解。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`；可选：`output_dir`、`filename_prefix`、`view_type`、`preset_name`、`horizontal_rotation_deg`、`vertical_rotation_deg`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；输出路径应由调用方明确指定；代码回填时保留现有 Schema 对 `project_path`、`output_dir`、`view_type`、`preset_name`、`horizontal_rotation_deg`、`vertical_rotation_deg` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Export a documented preset or Front-relative 3D view and return the PNG as base64.

### `inspect-plane-wave` — 读取平面波设置

- 建议定位：使用 PlaneWave 公开 getter 读取传播向量、电场向量和极化参数。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：仅在用户要求核对或排错时，于 define-plane-wave 后调用；不要作为每次求解的固定前置。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：`project_path`、`faces`、`unit_cell_scan`、`ports`、`plane_wave`、`monitors`、`count`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `project_path` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：使用 PlaneWave 公开 getter 读取传播向量、电场向量和极化参数。

### `inspect-project` — 检查工程参数与实体

- 建议定位：读取与“检查工程参数与实体”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：仅在用户需要工程概况、存在对象名歧义或排错时调用 → 根据返回内容选择具体建模或配置工具；不自动启动求解。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Open a CST project, list all parameters and entities, then close. Returns parameter names/values and entity names.

### `is-simulation-running` — 检查求解器是否运行

- 建议定位：在指定 CST 工程中完成“检查求解器是否运行”，用于配置或控制本次仿真。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：start-simulation-async → 本工具（仅需即时状态时）→ wait-simulation，或在用户明确要求时 pause-simulation / stop-simulation。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Check whether the CST solver is currently running for the verified working project.

### `list-monitors` — 列出工程监视器

- 建议定位：使用 Monitor 公开 getter 返回名称、类型、域和频率；与结果树扫描工具并存。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：读取 Monitor 对象，不保证相应仿真结果已经生成。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：仅在用户需要核对已有监视器、名称不明确或排错时，于 define-farfield-monitor / set-field-monitor 等工具后调用；不是启动前固定步骤。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：`project_path`、`faces`、`unit_cell_scan`、`ports`、`plane_wave`、`monitors`、`count`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `project_path` 的限定。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：使用 Monitor 公开 getter 返回名称、类型、域和频率；与结果树扫描工具并存。

### `list-parameters` — 列出 CST 参数

- 建议定位：读取与“列出 CST 参数”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：参数名或当前值不明确时调用 → change-parameter / define-parameters / prepare-experiment；已知参数时无需先调用。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：List parameters from the verified CST working project.

### `pause-simulation` — 暂停求解

- 建议定位：在指定 CST 工程中完成“暂停求解”，用于配置或控制本次仿真。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：已有正在运行的求解 → 本工具 → resume-simulation 或 stop-simulation；不得把暂停后再次 start-simulation 作为常规流程。
- 接口摘要：当前风险 `session`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Pause the currently running CST solver.

### `prepare-experiment` — 写入实验参数并保存工程

- 建议定位：在指定 CST 工程中完成“写入实验参数并保存工程”，用于配置或控制本次仿真。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：只写参数、保存并关闭，不运行求解；后续使用 run-experiment。
- 前置与副作用：必须提供 `project_path`、`param_name`、`param_value`、`names`、`values`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：list-parameters → prepare-experiment → run-experiment → 结果导出。
- 接口摘要：当前风险 `write`；必填：`project_path`、`param_name`、`param_value`、`names`、`values`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；`names` 与 `values` 必须一一对应。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Open a CST project, change one or more parameters, confirm, then save and close. Supports batch via names+values arrays. Use before run-experiment.

### `resume-simulation` — 继续求解

- 建议定位：在指定 CST 工程中完成“继续求解”，用于配置或控制本次仿真。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：pause-simulation → 本工具 → wait-simulation 或结果检查；不得对未暂停的求解调用。
- 接口摘要：当前风险 `write`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Resume a paused CST solver.

### `set-fdsolver-extrude-open-bc` — 设置频域求解器开放边界外推

- 建议定位：通过 FDSolver.ExtrudeOpenBC 开启或关闭频域求解器对开放边界的外推设置；本工具不切换求解器类型。
- 何时使用：当前已经是 `HF Frequency Domain`，工程采用开放边界且用户明确需要该频域选项时。
- 不要用于：当前为时域或其他求解器、或工程不使用开放边界时不得把它当作通用边界工具。
- 前置与副作用：必须提供 `project_path`；当前求解器必须为 `HF Frequency Domain`，开放边界应已通过 define-boundary 配置。该操作只写入 FDSolver.ExtrudeOpenBC 和 History。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：configure-frequency-domain-solver → define-boundary（开放边界）→ 本工具 → 其他激励和监视器配置 → start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Enable or disable FD solver extruded open boundary.

### `set-mesh-fpbavoid-nonreg-unite` — 设置 FPBA 非规则合并规避

- 建议定位：在指定 CST 工程中完成“设置 FPBA 非规则合并规避”，用于配置或控制本次仿真。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：选择使用 FPBA 的兼容求解器和网格方法 → define-mesh → 本工具（确有需要时）→ start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Enable or disable mesh FPBA non-regular unite avoidance.

### `set-mesh-minimum-step-number` — 设置最小网格步数

- 建议定位：在指定 CST 工程中完成“设置最小网格步数”，用于配置或控制本次仿真。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `project_path`、`num_steps`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：选择与本设置兼容的求解器和网格方法 → define-mesh → 本工具（确有需要时）→ start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`、`num_steps`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Set the minimum mesh step number.

### `set-solver-acceleration` — 设置求解器并行与硬件加速

- 建议定位：当前实现通过 Solver Object 配置线程数、分布式计算、MPI 和硬件加速，应作为时域求解器配置，而不是跨求解器通用设置。
- 何时使用：当前已经是 `HF Time Domain`，且用户明确需要调整该求解器的计算资源时。
- 不要用于：当前为 `HF Frequency Domain` 时不得调用；频域求解器资源设置不能从本工具名称推断为已覆盖。
- 前置与副作用：必须提供 `project_path`、`use_parallelization`、`max_threads`；应先用 change-solver-type 切换到 `HF Time Domain`。该操作写入 Solver Object 和 History。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：change-solver-type（`HF Time Domain`）→ define-solver → 本工具（需要时）→ 完成边界、激励和监视器 → start-simulation / run-experiment。
- 接口摘要：当前风险 `write`；必填：`project_path`、`use_parallelization`、`max_threads`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Configure solver parallelization and hardware acceleration.

### `start-simulation` — 同步启动并等待求解

- 建议定位：同步运行 CST 求解器并阻塞到结束；仅当 CST 的 run_solver 返回 True 才报告 success。失败时返回 solver_run_failed，并附本次求解写入 Result 日志的 CST 原始报错文本。
- 何时使用：模型完成，当前求解器已显式选择且对应配置、背景/边界、频率范围、必要端口/激励和所需监视器均已完成时。
- 不要用于：同步阻塞到求解调用返回；需要立即返回时使用 start-simulation-async。
- 前置与副作用：必须提供 `project_path`；启动前必须完成求解器选择、与当前类型匹配的求解器配置和边界相关设置。端口、激励、监视器和网格按本次任务需要完成；这些要求是工作流门槛，不要求额外调用 inspect-* 作固定复查。该操作同步占用 CST 会话直到返回。
- 成功与重试：成功后不要立即重复启动；超时或状态不明时先检查运行状态、日志或结果节点。
- 关联流程：求解器选择 → 匹配的求解器配置 → 背景/边界 → 端口、激励、监视器与网格 → 本工具 → 结果发现和导出。
- 接口摘要：当前风险 `long-running`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：同步运行 CST 求解器并阻塞到结束；仅当 CST 的 run_solver 返回 True 才报告 success。失败时返回 solver_run_failed，并附本次求解写入 Result 日志的 CST 原始报错文本。

### `start-simulation-async` — 异步启动求解

- 建议定位：异步启动 CST 求解器；返回成功只表示启动调用完成，不代表求解成功。
- 何时使用：与 start-simulation 相同的启动前配置均已完成，但调用方需要立即返回并在后续等待求解时。
- 不要用于：成功只表示启动调用完成，不代表求解成功；必须结合 wait-simulation、日志或结果验收。
- 前置与副作用：必须提供 `project_path`；启动前必须完成求解器选择、与当前类型匹配的求解器配置和边界相关设置。端口、激励、监视器和网格按本次任务需要完成；不要求额外调用 inspect-* 作固定复查。该操作异步占用 CST 会话。
- 成功与重试：成功后不要立即重复启动；超时或状态不明时先检查运行状态、日志或结果节点。
- 关联流程：求解器选择 → 匹配的求解器配置 → 背景/边界 → 端口、激励、监视器与网格 → 本工具 → wait-simulation → 结果检查。
- 接口摘要：当前风险 `long-running`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：异步启动 CST 求解器；返回成功只表示启动调用完成，不代表求解成功。
- 重点审核：请确认“启动成功不等于求解成功”的表述。

### `stop-simulation` — 停止求解

- 建议定位：在指定 CST 工程中完成“停止求解”，用于配置或控制本次仿真。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：接口未返回错误时信任 CST 已执行；成功后不要重复写入同一操作。
- 关联流程：已有正在运行或暂停的求解 → 本工具 → wait-simulation 确认已停止；修正设置后是否重新启动由用户决定。
- 接口摘要：当前风险 `session`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：Stop the currently running CST solver.

### `wait-simulation` — 等待求解停止

- 建议定位：轮询直到求解器不再运行或超时；running=false 只表示停止，不能证明求解成功。
- 何时使用：模型基本完成，用户已经确定相应求解、激励、边界、网格或运行控制需求时。
- 不要用于：running=false 只表示求解器停止，不证明求解成功；完整验收使用 run-experiment。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会修改指定 CST 工程的内存状态或 History；是否落盘取决于后续保存流程。
- 成功与重试：成功后不要立即重复启动；超时或状态不明时先检查运行状态、日志或结果节点。
- 关联流程：start-simulation-async → 本工具 → 检查求解日志和结果节点；返回“已停止”本身不等于求解成功。
- 接口摘要：当前风险 `long-running`；必填：`project_path`；可选：`timeout_seconds`、`poll_interval_seconds`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。接口返回错误时依据对象名、参数或 CST 原始文本修正；未返回错误则不追加常规读回检查。
- 当前 Registry：轮询直到求解器不再运行或超时；running=false 只表示停止，不能证明求解成功。
- 重点审核：请确认“停止不等于成功”的表述。

## 结果发现、读取与导出（`results`，22 个）

> 本类读取已保存结果或导出文件；完整 ResultTree 路径是主要依据，导出文件属于需要确认实际产物的必要操作。

### `analyze-metasurface-sparameters` — 离线分析超表面 S 参数

- 建议定位：完全离线读取多个 export-sparameter JSON，计算复数幅相、R/T/A、PCR、目标相位误差和被动性，并写出非空 JSON。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：只离线分析已导出的通道文件，不调用 CST；R/T/A 通道求和与相位参考规则本轮只记录、不修正。
- 前置与副作用：必须提供 `channels`、`output_path`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：多个 export-sparameter 文件 → 本工具 → generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`channels`、`output_path`；可选：`target_phases`、`passivity_tolerance`；关键返回：`output_path`、`file_size`、`run_id`、`frequency_range_ghz`、`frequency_count`、`channel_count`、`summary`、`warning_count`、`warnings`。
- 参数与失败：输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：完全离线读取多个 export-sparameter JSON，计算复数幅相、R/T/A、PCR、目标相位误差和被动性，并写出非空 JSON。
- 重点审核：R/T/A 通道求和与相位参考规则暂不修正；请只审核文字边界。

### `export-current-density` — 导出电流密度

- 建议定位：导出实际 ResultTree 中的电流密度节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不用于发现结果节点；路径未知时先调用相应 list-* 工具。
- 前置与副作用：必须提供 `project_path`、`result_path`、`file_path`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`result_path`、`file_path`；可选：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`；关键返回：`project_path`、`output_path`、`output_file`、`file_size`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径；输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：导出实际 ResultTree 中的电流密度节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。

### `export-e-field` — 导出电场结果

- 建议定位：导出实际 ResultTree 中的电场节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不用于发现结果节点；路径未知时先调用相应 list-* 工具。
- 前置与副作用：必须提供 `project_path`、`result_path`、`file_path`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`result_path`、`file_path`；可选：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`；关键返回：`project_path`、`output_path`、`output_file`、`file_size`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径；输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：导出实际 ResultTree 中的电场节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。

### `export-h-field` — 导出磁场结果

- 建议定位：导出实际 ResultTree 中的磁场节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不用于发现结果节点；路径未知时先调用相应 list-* 工具。
- 前置与副作用：必须提供 `project_path`、`result_path`、`file_path`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`result_path`、`file_path`；可选：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`；关键返回：`project_path`、`output_path`、`output_file`、`file_size`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径；输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：导出实际 ResultTree 中的磁场节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。

### `export-power-flow` — 导出功率流

- 建议定位：导出实际 ResultTree 中的功率流节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不用于发现结果节点；路径未知时先调用相应 list-* 工具。
- 前置与副作用：必须提供 `project_path`、`result_path`、`file_path`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`result_path`、`file_path`；可选：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`；关键返回：`project_path`、`output_path`、`output_file`、`file_size`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径；输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：导出实际 ResultTree 中的功率流节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。

### `export-power-loss-density` — 导出功率损耗密度

- 建议定位：导出实际 ResultTree 中的功率损耗密度节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不用于发现结果节点；路径未知时先调用相应 list-* 工具。
- 前置与副作用：必须提供 `project_path`、`result_path`、`file_path`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`result_path`、`file_path`；可选：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`；关键返回：`project_path`、`output_path`、`output_file`、`file_size`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径；输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：导出实际 ResultTree 中的功率损耗密度节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。

### `export-sparameter` — 导出单个 S 参数节点

- 建议定位：按真实 ResultTree 节点导出一条 S 参数曲线。可直接指定 result_path，或使用响应端口、激励端口及可选模式；支持 S1,1 和 SZmin(1),Zmax(1) 等 CST 2022 名称。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不用于发现结果节点；路径未知时先调用相应 list-* 工具。
- 前置与副作用：必须提供 `project_path`、`run_id`、`output_path`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：list-sparameter-results → export-sparameter → analyze-metasurface-sparameters。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`run_id`、`output_path`；可选：`result_path`、`response_port`、`excitation_port`、`response_mode`、`excitation_mode`；关键返回：`project_path`、`result_path`、`run_id`、`output_path`、`point_count`、`result_metric`、`s11_metric`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径；`run_id=0` 的含义按该接口当前说明处理；输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：按真实 ResultTree 节点导出一条 S 参数曲线。可直接指定 result_path，或使用响应端口、激励端口及可选模式；支持 S1,1 和 SZmin(1),Zmax(1) 等 CST 2022 名称。

### `export-surface-current` — 导出表面电流

- 建议定位：导出实际 ResultTree 中的表面电流节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不用于发现结果节点；路径未知时先调用相应 list-* 工具。
- 前置与副作用：必须提供 `project_path`、`result_path`、`file_path`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`result_path`、`file_path`；可选：`mode`、`step_x`、`step_y`、`step_z`、`point_file`、`subvolume`、`file_type`、`csv_separator`；关键返回：`project_path`、`output_path`、`output_file`、`file_size`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径；输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：导出实际 ResultTree 中的表面电流节点；完整 result_path 为唯一依据，支持 CST 2022 ASCIIExport 的采样、点文件、子体积和 CSV 选项。

### `export-touchstone` — 导出 Touchstone 网络参数

- 建议定位：使用 CST 2022 TOUCHSTONE Object 导出完整 S/Y/Z 网络矩阵；端口模式顺序由 CST 文件头给出。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不用于发现结果节点；路径未知时先调用相应 list-* 工具。
- 前置与副作用：必须提供 `project_path`、`output_base_path`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → export-touchstone → 外部网络分析工具。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`output_base_path`；可选：`parameter_type`、`data_format`、`frequency_range`、`fmin`、`fmax`、`impedance`、`renormalize`、`sample_count`、`use_ar_results`；关键返回：`project_path`、`output_path`、`output_file`、`file_size`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：使用 CST 2022 TOUCHSTONE Object 导出完整 S/Y/Z 网络矩阵；端口模式顺序由 CST 文件头给出。

### `export-voltage-result` — 导出电压结果

- 建议定位：按实际 0D/1D ResultTree 完整路径导出电压结果，不生成固定监视器编号。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不用于发现结果节点；路径未知时先调用相应 list-* 工具。
- 前置与副作用：必须提供 `project_path`、`result_path`、`file_path`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`result_path`、`file_path`；可选：无；关键返回：`project_path`、`output_path`、`output_file`、`file_size`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径；输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：按实际 0D/1D ResultTree 完整路径导出电压结果，不生成固定监视器编号。

### `generate-report` — 生成 HTML 结果报告

- 建议定位：完成“生成 HTML 结果报告”，取得已有仿真结果或可供后续处理的文件。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `data_dir`、`output_html`、`page_title`、`modules`、`split`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`data_dir`、`output_html`、`page_title`、`modules`、`split`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：Generate a modular HTML report from exported S11, farfield, and audit files. Supports --modules and --split.

### `get-1d-result` — 读取并序列化 0D/1D 结果

- 建议定位：读取与“读取并序列化 0D/1D 结果”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只适用于精确 0D/1D ResultTree 路径；二维场数据使用 get-2d-result 或专用导出工具。
- 前置与副作用：必须提供 `project_path`、`treepath`、`module_type`、`run_id`、`load_impedances`、`export_path`、`allow_interactive`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`treepath`、`module_type`、`run_id`、`load_impedances`、`export_path`、`allow_interactive`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径；`run_id=0` 的含义按该接口当前说明处理；代码回填时保留现有 Schema 对 `run_id`、`allow_interactive` 的限定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：Read an exact 0D/1D result-tree path with cst.results and serialize its saved data to JSON.

### `get-2d-result` — 读取并序列化 2D 结果

- 建议定位：读取与“读取并序列化 2D 结果”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：仅在当前 cst.results 实际提供 get_result2d_item 时使用；CST 2022 官方 Python 文档未列出该方法。
- 前置与副作用：必须提供 `project_path`、`treepath`、`module_type`、`export_path`、`allow_interactive`、`subproject_treepath`、`include_data`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`、`treepath`、`module_type`、`export_path`、`allow_interactive`、`subproject_treepath`、`include_data`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：Serialize 2D data only when the installed cst.results API exposes get_result2d_item; CST 2022 does not document it.
- 重点审核：CST 2022 官方 cst.results 页面列出 get_result_item，但未列出 get_result2d_item，必须保留兼容性限制。

### `get-parameter-combination` — 读取 Run ID 的参数组合

- 建议定位：读取与“读取 Run ID 的参数组合”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`、`run_id`、`module_type`、`allow_interactive`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `read`；必填：`project_path`、`run_id`、`module_type`、`allow_interactive`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；`run_id=0` 的含义按该接口当前说明处理；代码回填时保留现有 Schema 对 `run_id` 的限定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：Read the parameter combination for a result run ID.

### `get-version-info` — 读取 cst.results 版本信息

- 建议定位：读取与“读取 cst.results 版本信息”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 无必填参数，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `read`；必填：无；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：Read cst.results version information.

### `list-field-results` — 列出场结果节点

- 建议定位：使用 CST 2022 ResultTree.GetTreeResults 枚举 2D/3D 节点、官方 Result Type 和关联文件。
- 何时使用：求解完成后，需要发现可导出的 2D/3D 场结果完整路径时。
- 不要用于：只枚举 2D/3D 场节点，不导出场数据。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：run-experiment → list-field-results → 对应 export-* 工具 → plot-exported-file。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：`project_path`、`count`、`results`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：使用 CST 2022 ResultTree.GetTreeResults 枚举 2D/3D 节点、官方 Result Type 和关联文件。

### `list-result-items` — 列出结果树节点

- 建议定位：读取与“列出结果树节点”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：用于发现结果树节点，不读取节点数据；读取数据使用 get-1d-result/get-2d-result 或导出工具。
- 前置与副作用：必须提供 `project_path`、`module_type`、`filter_type`、`allow_interactive`、`subproject_treepath`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `read`；必填：`project_path`、`module_type`、`filter_type`、`allow_interactive`、`subproject_treepath`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：List result tree items from a project path.

### `list-run-ids` — 列出结果 Run ID

- 建议定位：读取与“列出结果 Run ID”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`、`treepath`、`module_type`、`allow_interactive`、`skip_nonparametric`、`max_mesh_passes_only`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `read`；必填：`project_path`、`treepath`、`module_type`、`allow_interactive`、`skip_nonparametric`、`max_mesh_passes_only`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：List CST result run IDs from a project path.

### `list-sparameter-results` — 列出 S 参数结果节点

- 建议定位：枚举实际 ResultTree 中的普通端口与 Floquet S 参数节点及可用 Run ID。允许工程同时在 CST 中打开；此时读取最近保存到磁盘的工程状态。
- 何时使用：求解完成后，需要发现真实 S 参数 ResultTree 路径和可用 Run ID 时。
- 不要用于：只枚举 S 参数节点与 Run ID，不导出曲线。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：run-experiment → list-sparameter-results → export-sparameter 或 get-1d-result。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：`project_path`、`count`、`results`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：枚举实际 ResultTree 中的普通端口与 Floquet S 参数节点及可用 Run ID。允许工程同时在 CST 中打开；此时读取最近保存到磁盘的工程状态。

### `list-subprojects` — 列出结果子工程

- 建议定位：读取与“列出结果子工程”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`、`allow_interactive`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `read`；必填：`project_path`、`allow_interactive`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：List subprojects from a CST results project by explicit project_path.

### `open-results-project` — 验证结果工程可读取

- 建议定位：完成“验证结果工程可读取”，取得已有仿真结果或可供后续处理的文件。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只验证结果 API 能打开工程，不列举结果、Run ID 或实际数据。
- 前置与副作用：必须提供 `project_path`、`allow_interactive`、`subproject_treepath`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `read`；必填：`project_path`、`allow_interactive`、`subproject_treepath`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：Validate that cst.results can open a project path.

### `plot-exported-file` — 绘制已导出结果文件

- 建议定位：完成“绘制已导出结果文件”，取得已有仿真结果或可供后续处理的文件。
- 何时使用：仿真结果已经保存，且已知或可先发现对应 ResultTree 节点时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `file_path`、`output_html`、`page_title`，并保证引用的工程、对象或文件真实存在；会在指定位置生成或覆盖导出文件，但不修改用户的几何设计。
- 成功与重试：确认返回的导出文件存在且非空；成功后不重复导出，除非用户要求覆盖。
- 关联流程：run-experiment → 相应 list-* 工具 → 本工具 → plot-exported-file 或 generate-report。
- 接口摘要：当前风险 `filesystem-write`；必填：`file_path`、`output_html`、`page_title`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：输出路径应由调用方明确指定。节点不存在时先枚举真实结果树；导出文件缺失或为空时才按必要产物检查处理。
- 当前 Registry：Render an exported JSON result or CST farfield ASCII/TXT file to an HTML preview.

## 任务与运行目录（`run`，2 个）

> 本类建立 Runtime 的任务与运行目录，不创建 CST 模型。

### `get-run-context` — 读取标准运行上下文

- 建议定位：读取与“读取标准运行上下文”相关的现有信息，返回 Agent 下一步选择所需的数据。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `task_path`、`run_id`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：init-task → prepare-run → get-run-context 或 record-stage。
- 接口摘要：当前风险 `read`；必填：`task_path`、`run_id`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`run_id=0` 的含义按该接口当前说明处理。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：Read standard run context through cst_runtime.

### `prepare-run` — 创建标准运行目录

- 建议定位：完成“创建标准运行目录”，保存或返回 Runtime 工作流所需的信息。
- 何时使用：需要建立可追溯的 Runtime 任务、日志、证据或运行目录时。
- 不要用于：不代表 CST 已执行建模或求解，也不替代实际工程文件和结果节点。
- 前置与副作用：必须提供 `task_path`，并保证引用的工程、对象或文件真实存在；会写入 Runtime 工作区、日志、状态文件或报告。
- 成功与重试：成功后不要重复写入；失败时修正明确参数或路径后再重试。
- 关联流程：init-task → prepare-run → get-run-context 或 record-stage。
- 接口摘要：当前风险 `filesystem-write`；必填：`task_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。写入失败时保留原错误和上下文，修正明确输入后重试。
- 当前 Registry：Create a standard run workspace through cst_runtime.

## CST 会话管理（`session_manager`，6 个）

> 本类管理 CST 会话；已有会话归属不明确时必须先让用户确认 PID。

### `create-blank-project` — 创建空白 CST 工程

- 建议定位：完成“创建空白 CST 工程”，使 Agent 在明确的工程与会话边界内继续工作。
- 何时使用：需要建立、确认、恢复或结束指定工程的 CST 会话时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会打开、附着、保存或关闭会话，具体副作用以动作和返回状态为准。
- 成功与重试：成功后不要重复打开、附着或关闭；状态不明时使用会话检查，不盲目重试。
- 关联流程：create-blank-project → define-units → 建模与求解配置 → save-project。
- 接口摘要：当前风险 `write`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。遇到多个候选 PID、归属不明或锁未释放时停止自动操作并询问用户。
- 当前 Registry：Create a new blank CST project at the specified path.

### `cst-session-close` — 关闭指定 CST 工程会话

- 建议定位：完成“关闭指定 CST 工程会话”，使 Agent 在明确的工程与会话边界内继续工作。
- 何时使用：需要建立、确认、恢复或结束指定工程的 CST 会话时。
- 不要用于：不得关闭或杀死 Runtime 不拥有且用户未授权的外部 Design Environment。
- 前置与副作用：必须提供 `project_path`、`save`、`wait_unlock`、`timeout_seconds`、`poll_interval_seconds`，并保证引用的工程、对象或文件真实存在；会打开、附着、保存或关闭会话，具体副作用以动作和返回状态为准。
- 成功与重试：成功后不要重复打开、附着或关闭；状态不明时使用会话检查，不盲目重试。
- 关联流程：save-project（如需）→ cst-session-close → wait-project-unlocked（仅必要时）。
- 接口摘要：当前风险 `session`；必填：`project_path`、`save`、`wait_unlock`、`timeout_seconds`、`poll_interval_seconds`；可选：`kill_processes`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。遇到多个候选 PID、归属不明或锁未释放时停止自动操作并询问用户。
- 当前 Registry：Close the expected CST project, optionally wait for locks to clear, then inspect the environment.

### `cst-session-inspect` — 检查 CST 会话与进程状态

- 建议定位：完成“检查 CST 会话与进程状态”，使 Agent 在明确的工程与会话边界内继续工作。
- 何时使用：用户明确需要这些信息来选择下一步、解释结果或排查具体问题时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会打开、附着、保存或关闭会话，具体副作用以动作和返回状态为准。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：根据用户任务在同类工具前后使用；不自动扩展工作流。
- 接口摘要：当前风险 `read`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。遇到多个候选 PID、归属不明或锁未释放时停止自动操作并询问用户。
- 当前 Registry：Central session/process gate: inspect processes, locks, open projects, and reattach readiness.

### `cst-session-open` — 打开指定 CST 工程

- 建议定位：通过中央会话管理器打开 CST 工程。默认只自动接管本次启动后唯一新增的 PID；若需要接管已有或归属不明确的会话，首次调用会返回候选 PID，调用方必须先询问用户，再同时提供 confirm_existing_session_takeover=true 与用户确认的 existing_session_pid。
- 何时使用：需要建立、确认、恢复或结束指定工程的 CST 会话时。
- 不要用于：只有本次启动后唯一新增的 PID 可自动接管；已有或归属不明会话必须先让用户确认。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会打开、附着、保存或关闭会话，具体副作用以动作和返回状态为准。
- 成功与重试：成功后不要重复打开、附着或关闭；状态不明时使用会话检查，不盲目重试。
- 关联流程：cst-session-inspect → cst-session-open；完成后 save-project 或 cst-session-close。
- 接口摘要：当前风险 `session`；必填：`project_path`；可选：`confirm_existing_session_takeover`、`existing_session_pid`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `confirm_existing_session_takeover`、`existing_session_pid` 的限定。遇到多个候选 PID、归属不明或锁未释放时停止自动操作并询问用户。
- 当前 Registry：通过中央会话管理器打开 CST 工程。默认只自动接管本次启动后唯一新增的 PID；若需要接管已有或归属不明确的会话，首次调用会返回候选 PID，调用方必须先询问用户，再同时提供 confirm_existing_session_takeover=true 与用户确认的 existing_session_pid。

### `cst-session-reattach` — 重新附着已打开工程

- 建议定位：重新附着已打开的 CST 工程。首次调用只返回候选 PID；调用方询问用户后，必须同时传入确认标志和用户选择的 PID。
- 何时使用：需要建立、确认、恢复或结束指定工程的 CST 会话时。
- 不要用于：仅用于重新附着已有会话，不用于创建新工程或打开未启动的工程。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会打开、附着、保存或关闭会话，具体副作用以动作和返回状态为准。
- 成功与重试：成功后不要重复打开、附着或关闭；状态不明时使用会话检查，不盲目重试。
- 关联流程：cst-session-inspect → 用户确认 PID → cst-session-reattach。
- 接口摘要：当前风险 `session`；必填：`project_path`；可选：`confirm_existing_session_takeover`、`existing_session_pid`；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；代码回填时保留现有 Schema 对 `confirm_existing_session_takeover`、`existing_session_pid` 的限定。遇到多个候选 PID、归属不明或锁未释放时停止自动操作并询问用户。
- 当前 Registry：重新附着已打开的 CST 工程。首次调用只返回候选 PID；调用方询问用户后，必须同时传入确认标志和用户选择的 PID。

### `save-project` — 保存 CST 工程

- 建议定位：完成“保存 CST 工程”，使 Agent 在明确的工程与会话边界内继续工作。
- 何时使用：需要建立、确认、恢复或结束指定工程的 CST 会话时。
- 不要用于：不要把该工具扩展到说明之外的 CST 对象或工作流。
- 前置与副作用：必须提供 `project_path`，并保证引用的工程、对象或文件真实存在；会打开、附着、保存或关闭会话，具体副作用以动作和返回状态为准。
- 成功与重试：成功后不要重复打开、附着或关闭；状态不明时使用会话检查，不盲目重试。
- 关联流程：根据用户任务在同类工具前后使用；不自动扩展工作流。
- 接口摘要：当前风险 `filesystem-write`；必填：`project_path`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。遇到多个候选 PID、归属不明或锁未释放时停止自动操作并询问用户。
- 当前 Registry：Save the verified CST working project.

## 仿真工作流（`simulation`，1 个）

> 本类运行求解并以新 Run ID 和非空结果节点验收；不会替用户判断设计指标是否达标。

### `run-experiment` — 运行并验收一次仿真

- 建议定位：运行求解并等待完成；必须以指定 0D/1D 结果节点共同出现的新 Run ID 和非空数据验收。求解前结果节点尚不存在视为空基线（首次仿真的正常初始状态，支持由本次仿真生成节点）；不执行任何结果导出，返回通用 result_metrics；S1,1 仅保留兼容 s11_metric。
- 何时使用：用户已经给出工程、目标节点以及本次操作所需参数后。
- 不要用于：负责求解完成与结果节点验收，不执行导出，也不判断设计指标是否达标。
- 前置与副作用：必须提供 `project_path`、`completion_result_paths`、`timeout_seconds`；启动前必须完成求解器选择、与当前类型匹配的求解器配置和边界相关设置，并按目标结果定义端口、激励和监视器。只读 inspect-* 不作为固定前置。该操作启动求解并占用 CST 会话。
- 成功与重试：成功后不要立即重复启动；超时或状态不明时先检查运行状态、日志或结果节点。
- 关联流程：求解器选择 → 匹配的求解器配置 → 背景/边界 → 端口、激励、监视器与网格 → prepare-experiment（仅扫参时）→ 本工具 → list-* results → export-*。
- 接口摘要：当前风险 `long-running`；必填：`project_path`、`completion_result_paths`、`timeout_seconds`；可选：无；关键返回：`project_path`、`run_id`、`completion_result_paths`、`result_metrics`、`s11_metric`、`solver_completed`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。写入失败时保留原错误和上下文，修正明确输入后重试。
- 当前 Registry：运行求解并等待完成；必须以指定 0D/1D 结果节点共同出现的新 Run ID 和非空数据验收。求解前结果节点尚不存在视为空基线（首次仿真的正常初始状态，支持由本次仿真生成节点）；不执行任何结果导出，返回通用 result_metrics；S1,1 仅保留兼容 s11_metric。

## 复合工作流（`workflow`，2 个）

> 本类封装重复性批处理；具体单元设计、参数范围、目标频率和停止条件仍由用户决定。

### `build-array` — 批量构建阵列

- 建议定位：按普通 code 和受控 builder 批量构建 CST 阵列；元素坐标是参考模板的相对平移量。brick-v1 的 origin 是最小角点，如使用中心坐标应由调用方预先换算。
- 何时使用：用户已经给出工程、目标节点以及本次操作所需参数后。
- 不要用于：只按用户提供的单元定义与坐标重复建模，不生成阵列综合方案或自动选择单元。
- 前置与副作用：必须提供 `project_path`、`units`、`elements`，并保证引用的工程、对象或文件真实存在；会执行该接口声明的写入操作。
- 成功与重试：成功后不要重复写入；失败时修正明确参数或路径后再重试。
- 关联流程：create-component 或单元定义 → build-array → save-project → 求解配置。
- 接口摘要：当前风险 `write`；必填：`project_path`、`units`、`elements`；可选：`summary`；关键返回：`project_path`、`groups_built`、`instances_created`、`reference_objects`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件。写入失败时保留原错误和上下文，修正明确输入后重试。
- 当前 Registry：按普通 code 和受控 builder 批量构建 CST 阵列；元素坐标是参考模板的相对平移量。brick-v1 的 origin 是最小角点，如使用中心坐标应由调用方预先换算。

### `quick-sweep` — 运行通用参数扫描

- 建议定位：运行参数扫描并导出 JSON、CSV 和 NPZ 结果。
- 何时使用：用户已经给出工程、目标节点以及本次操作所需参数后。
- 不要用于：适用于用户已给出参数范围和目标结果节点的通用扫描，不内置任何特定单元结构。
- 前置与副作用：必须提供 `project_path`、`parameters`、`target_freq_ghz`，并保证引用的工程、对象或文件真实存在；会启动求解或批处理并占用 CST 会话。
- 成功与重试：成功后不要立即重复启动；超时或状态不明时先检查运行状态、日志或结果节点。
- 关联流程：list-parameters 或用户给定范围 → quick-sweep → 分析 JSON/CSV/NPZ。
- 接口摘要：当前风险 `long-running`；必填：`project_path`、`parameters`、`target_freq_ghz`；可选：`result_path`、`output_dir`、`continue_on_error`、`restore_parameters`；关键返回：`output_dir`、`sweep_time`、`total_steps`、`successful_steps`、`failed_steps`、`records`、`exported_files`、`errors`。
- 参数与失败：`project_path` 必须指向明确的 .cst 文件；结果路径必须使用实际 ResultTree 完整路径；输出路径应由调用方明确指定；带 _ghz 后缀的频率单位为 GHz。写入失败时保留原错误和上下文，修正明确输入后重试。
- 当前 Registry：运行参数扫描并导出 JSON、CSV 和 NPZ 结果。

## Runtime 工作区（`workspace`，3 个）

> 本类初始化或检查 Runtime 工作区，不安装 CST，也不代替真实 CST 兼容性验收。

### `health-check` — 检查 Runtime 环境

- 建议定位：只读检查 Python、工作区、CST 库和导入状态；不会初始化、安装或修改配置。
- 何时使用：首次接入 Runtime、环境发生变化或导入失败时。
- 不要用于：只读信息不能证明后续写入或求解已经完成，也不应作为每次成功调用后的固定复查。
- 前置与副作用：必须提供 `workspace`，并保证引用的工程、对象或文件真实存在；通常无 CST 模型副作用。
- 成功与重试：只读失败可在修正路径或筛选条件后重试；成功后无需为了确认而重复调用。
- 关联流程：health-check → init-workspace（需要时）→ init-task。
- 接口摘要：当前风险 `read`；必填：`workspace`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。路径、ID 或筛选条件无效时修正输入后重试；无数据不能推断 CST 已失败。
- 当前 Registry：只读检查 Python、工作区、CST 库和导入状态；不会初始化、安装或修改配置。

### `init-task` — 初始化 Runtime 任务

- 建议定位：完成“初始化 Runtime 任务”，保存或返回 Runtime 工作流所需的信息。
- 何时使用：需要建立可追溯的 Runtime 任务、日志、证据或运行目录时。
- 不要用于：不代表 CST 已执行建模或求解，也不替代实际工程文件和结果节点。
- 前置与副作用：必须提供 `workspace`、`task_id`、`source_project`、`goal`、`title`、`force`，并保证引用的工程、对象或文件真实存在；会写入 Runtime 工作区、日志、状态文件或报告。
- 成功与重试：成功后不要重复写入；失败时修正明确参数或路径后再重试。
- 关联流程：init-workspace → init-task → prepare-run。
- 接口摘要：当前风险 `filesystem-write`；必填：`workspace`、`task_id`、`source_project`、`goal`、`title`、`force`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。写入失败时保留原错误和上下文，修正明确输入后重试。
- 当前 Registry：Create a task.json and runs directory inside a runtime workspace.

### `init-workspace` — 初始化 Runtime 工作区

- 建议定位：完成“初始化 Runtime 工作区”，保存或返回 Runtime 工作流所需的信息。
- 何时使用：需要建立可追溯的 Runtime 任务、日志、证据或运行目录时。
- 不要用于：不代表 CST 已执行建模或求解，也不替代实际工程文件和结果节点。
- 前置与副作用：必须提供 `workspace`，并保证引用的工程、对象或文件真实存在；会写入 Runtime 工作区、日志、状态文件或报告。
- 成功与重试：成功后不要重复写入；失败时修正明确参数或路径后再重试。
- 关联流程：health-check → init-workspace → init-task → prepare-run。
- 接口摘要：当前风险 `filesystem-write`；必填：`workspace`；可选：无；关键返回：当前仅统一状态或错误外壳。
- 参数与失败：参数名称和允许值以当前 Schema 为准；不从模型名称猜测物理含义。写入失败时保留原错误和上下文，修正明确输入后重试。
- 当前 Registry：Initialize a minimal CST runtime workspace in an empty or existing directory.

## 审核完成后的处理

1. 合并重复信息，把每个工具压缩成适合 Tool Registry 的短说明。
2. 将中文审核稿润色并翻译为英文，参数名称、单位、坐标和边界保持一致。
3. 只修改 Registry 元数据及必要的元数据测试，不借机修改 CST 执行代码。
4. 再次核对 Agent 暴露工具清单和 MCP Worker 可发现性。
