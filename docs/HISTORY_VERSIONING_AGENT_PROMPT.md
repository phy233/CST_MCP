# CST History 版本管理与恢复机制实现任务

你需要在 `D:\My_Program\Python\CST_MCP` 中设计并实现 CST History 的记录、差异比较、检查点、断点恢复和安全回退机制。请先完整审计现有代码与文档，同时阅读CST 2022.5官方帮助文档(`D:\Program Files (x86)\CST Studio Suite 2022\Online Help`)，再按下面的范围分阶段实施。不要把任务简化成说明文档，也不要直接设计成“一键完成全部工作”的黑盒流程。

## 一、用户目标和偏好

用户的长期目标是让 AI 分步骤协助设计、修改和仿真超表面，而不是执行不可调整的“一键工作流”。History 机制应服务于以下目标：

1. 每一步 CST 操作都有明确记录，可以查看此前做了什么。
2. 能比较任意两个状态之间新增、删除、移动或修改了哪些 History 块和 VBA 指令。
3. 中断后可以判断上一步是否已经提交、是否执行成功，以及应该继续、重试还是人工处理。
4. 能建立轻量 History 检查点；必要时能从已知基线在新的工程副本中重放，而不是冒险原地破坏当前工程。
5. 尽量复用 CST 自己的 VBA 编译和运行时检查，以及项目现有的错误网关。不要扩展成试图在 Python 侧完整理解所有 CST VBA 的大型静态检查器。
6. 不要重复编写大段 VBA 对象、方法和示例手册；新增文档应链接现有 API/兼容性文档，只说明版本管理机制特有的内容。
7. Skills 和文档必须支持逐步命令：查看状态、创建快照、比较、记录、生成恢复计划、在新副本中恢复。不要只提供一个内部参数不可见的总工作流命令。
8. 保存 Agent 与 MCP 的交互记录，使一次设计任务中的“Agent 请求了什么工具、MCP 收到什么参数、返回什么结果、对应哪次 History 变化”能够串联查看。

## 二、已经完成的 CST 2022.5 真机验证

以下内容已经在 CST Studio Suite 2022.5（版本字符串 `2022.5 Release from 2022-06-03`）上通过真实工程副本验证，不要再把它们写成猜测：

1. `project.modeler._GetHistory()` 存在且可调用。
2. 返回值类型为 Python `dict`。
3. 空 History 的实测形态是：

   ```python
   {"list": None}
   ```
4. 提交一个 History 块后，实测形态类似：

   ```python
   {
       "list": [
           {
               "name": "History 标签",
               "contents": "完整 VBA 文本",
               "version": "2022.5|31.0.1|20220603",
               "error": False,
               "exclude": False,
               "has_undo": False,
               "hide": False,
           }
       ]
   }
   ```
5. `contents` 包含提交给 `add_to_history()` 的完整实际 VBA，包括项目错误网关的包装代码和原始业务 VBA。
6. History 标签和原始 `StoreParameter` 业务指令均能从返回结构中准确找到。
7. 这次实验没有调用 `_ResizeHistory`、`_TryToUndoNTimes`，也没有验证任何私有写入或撤销接口。
8. `_GetHistory()` 表示线性的 **History List**，不是界面中单个实体依赖关系的 **History Tree**。版本管理第一阶段只针对 History List。

相关实验代码仍保留在：

- `skills/cst-runtime-cli/scripts/cst_runtime/core/history_probe.py`
- `skills/cst-runtime-cli/scripts/cst_runtime/worker.py` 中的 `_test_cst2022_history_export_probe` 内部动作
- `skills/cst-runtime-cli/tests/test_cst2022_history_export_probe.py`

实验生成的 `.cst_runtime/evidence/...` 临时证据已经删除，因此实现时应以代码、上述已确认结构和新的离线夹具为依据。

## 三、必须先完成的只读审计

在修改代码前，先阅读并报告以下内容：

1. `skills/cst-runtime-cli/scripts/cst_runtime/core/error_gateway.py` 中 `submit_vba_history()` 的调用链、成功和失败信封、operation ID、VBA 摘要、状态文件生命周期。
2. `skills/cst-runtime-cli/scripts/cst_runtime/core/identity.py` 的精确工程附着规则。
3. 当前 workspace/task/run、audit、evidence、session 和 CLI 注册结构，找出 History 数据最合适的归属层，不要平行搭建第二套运行记录系统。
4. MCP server、proxy、Python 3.9 Worker 的请求与响应调用链，找出能够统一记录 Agent→MCP 请求和 MCP→Agent 返回的中间层。不要在每个工具 handler 中分别复制日志代码。
5. 当前 Agent、CLI-only 和内部能力的暴露策略。History 私有接口在完成契约、离线测试、文档和真机验收前，不得直接加入 Agent/MCP 白名单。
6. CST 2022 Online Help 中 History List、History Tree、`add_to_history()` 和 `full_history_rebuild()` 的官方说明。报告中必须区分：
   - 官方手册事实；
   - 当前代码事实；
   - 本提示提供的 CST 2022.5 真机事实；
   - 尚未验证的推断。

不要因为实验代码已经存在就跳过架构审计，也不要启动 CST 来完成这一阶段。

## 四、建议的数据模型

请根据现有项目风格调整命名，但至少表达以下信息：

### 1. HistoryBlock

- 在线性列表中的序号；
- `name`；
- 原始 `contents`；
- `version`；
- `error`、`exclude`、`hide`、`has_undo`；
- CST 未来版本可能增加的未知字段，必须原样保留；
- 原始 `contents` 的 SHA-256。

### 2. HistorySnapshot

- 本地 schema 版本；
- 精确工程身份和工程路径；
- CST 版本及能力探测结果；
- 捕获时间；
- 有序 HistoryBlock 列表；
- 原始快照哈希；
- 父快照或父提交 ID；
- 捕获原因和关联 operation ID。

### 3. HistoryCommit / OperationRecord

- 唯一 ID；
- 父记录 ID；
- 操作意图；
- History 标签；
- 原始业务 VBA；
- 业务 VBA SHA-256；
- 实际网关 VBA 或对应快照中的实际块；
- 提交前和提交后快照 ID；
- `pending / submitted / succeeded / failed / reconciled / ambiguous` 状态；
- CST 错误信封；
- 时间戳、CST 版本、工程身份；
- 相关证据文件路径。

### 4. MCPInteractionRecord

- 唯一 interaction ID 和关联 ID；
- task、run、workspace，以及客户端实际提供的 Agent 标识；
- MCP server 名称和版本；
- 工具名称；
- Agent 发给 MCP 的原始工具参数；
- MCP 返回给 Agent 的原始结果或统一错误信封；
- 请求开始、结束时间和耗时；
- 关联的 operation ID、工程身份、before/after History snapshot；
- `requested / running / succeeded / failed / timeout / transport_error` 状态。

### 5. AgentWorkNote

MCP 服务端不能自动看到 Agent 的完整对话、计划和内部推理。对于工具调用之外仍需保存的计划、决定、用户确认和阶段结论，提供显式的工作记录结构：

- note ID、时间戳和类别；
- Agent 主动提交的简短可见说明；
- 关联 task/run、interaction ID、operation ID 和 snapshot ID；
- 用户确认或人工处置结论；
- 不要求、也不得声称记录 Agent 的隐藏思维过程。

### 6. Append-only Journal

History 操作、MCP 交互和 AgentWorkNote 应进入同一条可关联的追加式事件流，或者复用项目现有追加式审计机制。不得通过覆盖旧记录来假装操作从未发生。每条事件至少包含事件 ID、事件类型、关联 ID、结果和时间戳；涉及 CST 修改时再包含 operation ID 与前后快照哈希。

## 五、只保存和比较原始 History

`_GetHistory()` 的原始返回值是唯一 History 事实来源。不要建立语义视图，不要尝试去掉错误网关包装，也不要对 VBA 做语义规范化。

实现必须满足：

- 忠实保存 `_GetHistory()` 返回的全部字段和完整 `contents`；
- `contents` 中的换行、空白、operation ID、状态文件名、局部变量和网关代码都原样保留；
- 可以用确定字段顺序的 UTF-8 JSON 作为快照容器，但不得改变 VBA 字符串本身；
- 哈希必须基于原始字段和原始 VBA；
- 用户查看 diff 时直接展示 CST 导出的原始 VBA 差异；
- 如果原始 VBA 因网关 operation ID 不同而产生较多差异，应如实展示，不额外维护“降噪版”或“语义版”。

## 六、Diff 设计要求

不能只比较整个字符串是否不同。至少输出：

1. History 块新增、删除、移动、修改和未变化；
2. 每个修改块的字段变化；
3. 原始 `contents` 的统一 diff；
4. 快照级摘要，例如块数量变化和原始哈希；
5. 对重名 History 块、重复内容和顺序变化有确定行为。

不要只用 `name` 当唯一键。建议综合序号、内容哈希、相邻块信息或序列匹配算法识别移动和修改，并为歧义匹配明确返回 `ambiguous`。

## 七、提交记录与断点恢复

将 History 记录接入 `submit_vba_history()` 的正常调用链，但不要破坏现有错误处理：

1. 提交前先原子写入 `pending` 意图记录，并捕获 before snapshot。
2. 正常调用现有错误网关，让 CST 编译和执行 VBA。
3. 无论成功或失败，在仍可连接 CST 时尽量捕获 after snapshot。
4. 成功时记录 `succeeded`、before/after 哈希、业务 VBA 摘要和实际 History 块。
5. 已收到明确 CST/VBA 错误时记录 `failed`，保留现有统一错误信封。
6. Worker 崩溃、进程中断或只留下 `pending/submitted` 时，恢复逻辑应：
   - 精确附着目标工程；
   - 重新读取 History；
   - 根据标签、业务摘要、实际块和 before 哈希判断 `not_applied / applied / ambiguous`；
   - 只有 `not_applied` 且用户明确要求时才允许重试；
   - `ambiguous` 时绝对不能自动重复提交。
7. 日志写入使用临时文件加原子替换，或者项目已有的可靠追加机制，避免半个 JSON 文件。

## 八、Agent 与 MCP 交互记录

交互记录不是只在 History 提交时写一次，而应覆盖所有通过 MCP 调用的工具。优先在统一 dispatch/proxy/server 边界实现，要求如下：

1. 收到工具请求时先追加 `tool_requested`，保存原始工具名称和原始参数。
2. 工具开始执行时记录 `tool_running`，并生成可贯穿 Worker 调用的 interaction ID。
3. 工具完成后追加 `tool_succeeded` 或 `tool_failed`，保存原始返回值或统一错误信封及耗时。
4. Worker 超时、退出、响应 ID 不匹配和传输错误也必须结束对应 interaction，不能永远停留在 running。
5. 如果工具触发 History 修改，通过 operation ID 将 MCP interaction、before snapshot、HistoryCommit 和 after snapshot 关联起来。
6. 只读工具同样记录，但不强行创建 History snapshot。
7. 大型结果不应被静默截断。若现有日志不适合内嵌，可把完整 payload 写入独立内容寻址文件，在事件中保存路径、大小和 SHA-256。
8. 不主动读取或记录环境变量、凭据和 MCP 调用范围之外的信息；对于实际工具 payload 则保持原始记录，不建立语义摘要替代原文。
9. MCP 无法自动取得的 Agent 计划、关键选择和用户确认，由 Agent 按 Skills 约定显式调用工作记录接口，例如 `record-agent-note`。该接口记录 Agent 主动提供的文本，不声称保存隐藏推理。
10. 提供按 task、run、project、interaction ID、operation ID 和时间范围查询的能力，使用户可以从某个 History 块追溯到触发它的 Agent/MCP 调用，也能从一次 MCP 调用定位其 CST 结果。

建议的事件顺序是：

```text
agent_note（可选）
→ tool_requested
→ tool_running
→ history_operation_pending（若会修改 History）
→ history_before_snapshot
→ CST/VBA 执行
→ history_after_snapshot
→ history_operation_succeeded/failed
→ tool_succeeded/failed
→ agent_note（可选的阶段结论）
```

## 九、检查点与 reverse 的分级边界

第一阶段不要使用尚未验证的私有写接口原地改写 CST History。将功能分级：

### A. 轻量 History 检查点

保存结构化 HistorySnapshot、操作日志和父子关系。它适合 diff、审计、恢复判断和生成重放计划，但不承诺包含求解结果、外部导入文件或全部非 History 状态。

### B. 物理工程检查点

保存 `.cst` 与对应伴随目录的完整一致副本。必须复用现有 session/lock/identity 机制，在文件已保存且可安全复制的边界执行。不能只复制 `.cst` 而遗漏伴随目录，也不能复制仍在不一致写入状态的工程。

### C. reverse / checkout

MVP 应先实现：

- `restore-plan`：只生成恢复计划，不改变 CST；
- `checkout-new-copy`：从已知物理检查点或干净基线创建新副本，并按已验证顺序重放业务 VBA；
- 每个重放步骤继续使用现有错误网关并生成新的记录；
- 某一步失败立即停止，保留可检查的中间副本。

暂时禁止：

- 在当前工程上调用 `_ResizeHistory()`；
- 调用 `_TryToUndoNTimes()`；
- 使用 `RemoveBlocksFromHistory`、`ReplaceContentOfHistoryBlock` 等未验证能力；
- 把“移动 HEAD 指针”描述成 CST 工程已经被恢复；
- 自动覆盖原工程或自动删除求解结果。

这些私有写入能力若未来需要，必须单独写最小真机实验、单独授权、使用工程副本并保存证据。

## 十、分步骤接口与 Skills 文档

最终用户接口应保持可组合、可检查，至少覆盖以下动作；具体名称可按当前 CLI 规范调整：

1. 查看 CST History 能力和版本支持状态；
2. 导出当前 History snapshot；
3. 查看当前 History 状态和未完成 operation；
4. 列出 History log；
5. 比较两个 snapshot/commit；
6. 创建轻量 History checkpoint；
7. 创建物理工程 checkpoint；
8. 生成 restore plan；
9. 用户确认后在新工程副本中执行 checkout/replay；
10. 将 `ambiguous` 操作标记为人工确认后的 `reconciled`；
11. 查看 Agent/MCP interaction log；
12. 查看一次 interaction 关联的 History 前后变化；
13. 显式追加 Agent 工作说明、用户确认或人工处置结论。

更新 `skills/cst-runtime-cli/SKILL.md` 及必要文档，增加面向非软件工程用户的逐步示例。文档必须明确：

- History List 与 History Tree 的区别；
- 快照、提交记录、物理检查点、求解结果之间的区别；
- “可以重放 VBA”不等于“能够无损恢复全部 CST 工程结果”；
- CST 2022.5 已实测，其他版本需要能力探测和真机验收；
- 每一步会不会修改 CST、会不会保存工程、会不会生成副本。
- MCP 自动记录的是工具边界的请求和返回，不包含 Agent 的完整聊天或隐藏推理；
- AgentWorkNote 是 Agent 主动提交的工作说明，不应包装成系统自动获取的思维过程。

不要复制现有 VBA API 文档的大段内容，使用链接和交叉引用。

## 十一、测试要求

先完成离线测试，不启动 CST：

1. `{ "list": None }`；
2. 单块和多块 History；
3. Unicode 标签和 VBA；
4. CRLF/LF、空白、网关变量和 operation ID 在原始 VBA 中不被改写；
5. 未知字段保留；
6. 重名块、重复内容、移动、修改和歧义匹配；
7. 原始哈希稳定性，以及任意原始字符变化会改变对应哈希；
8. pending 日志的正常恢复、已应用、未应用和 ambiguous 分支；
9. 原子写失败不能损坏上一份有效记录；
10. MCP 成功、业务错误、Worker 超时、Worker 退出、传输错误都生成完整的 interaction 结束事件；
11. interaction ID、operation ID 和前后 History snapshot 能双向关联；
12. 大型原始请求/结果使用内容寻址文件时，路径、大小和 SHA-256 正确且内容不被截断；
13. AgentWorkNote 只保存显式传入文本，不伪造或推断隐藏推理；
14. 私有 History 能力不得意外暴露给 MCP Agent；
15. 现有 `submit_vba_history()` 错误契约不得回归。

本提示本身不授权再次启动 CST。离线实现和审核完成后，如果确实需要真机回归，先向用户说明要验证的单一问题、会修改什么副本、如何关闭及保留哪些证据，得到明确许可后只运行对应的最小集成测试。

## 十二、工作区和修改约束

当前仓库不是干净工作区。`skills/cst-runtime-cli/tests/refs/ref_0/` 下已有用户的 CST 基准工程变化和新增结果文件。必须遵守：

1. 不得 reset、checkout、删除、格式化或暂存这些现有变化。
2. 真机测试永远复制源工程和伴随目录，只操作副本。
3. 不得使用 `git add .`。
4. 单次修改保持小而可审查，不做大规模重构；不要删除超过 1000 行代码。
5. 所有注释、文档和用户可见说明使用简体中文。
6. 未经用户要求不要创建 Git commit；如被要求提交，应按职责拆分中文 commit，并先运行限定路径的 staged diff 检查。

## 十三、交付顺序

请按以下顺序推进，并在每一阶段报告具体文件和验证结果：

1. 只读架构审计和拟复用组件清单；
2. 数据契约、存储布局和恢复状态机设计；
3. 只读 `_GetHistory()` 适配器、原始 snapshot、原始哈希和 diff；
4. 统一 MCP interaction journal 和显式 AgentWorkNote；
5. 追加式 History operation journal 与 `submit_vba_history()` 集成，并建立 interaction 关联；
6. checkpoint 和只生成计划的 restore 功能；
7. 在新副本中重放的 checkout 功能；
8. Skills、用户文档和迁移说明；
9. 离线测试、暴露策略测试和限定路径差异复核；
10. 单独列出仍需真机验证的事项，不得把离线通过描述为 CST 真机通过。

最终报告必须回答：实现了什么、哪些操作只读、哪些会修改副本、哪些私有接口仍未使用、如何处理崩溃后的 ambiguous 状态、当前恢复能覆盖什么和不能覆盖什么、Agent/MCP 自动记录了哪些边界和哪些内容必须由 Agent 显式提交，以及全部测试命令和结果。
