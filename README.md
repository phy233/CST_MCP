# CST MCP / Runtime CLI

CST Studio Suite 自动化 CLI、MCP 与 AI Agent 辅助基础设施。Runtime Registry 提供建模、仿真、结果读取、参数优化、远场导出、History 和审计能力，并通过统一 JSON 契约与运行时守卫控制 CST 调用。CLI 工具不等于 MCP 暴露面；只有明确标记为 `agent` 的工具才会注册到 MCP。

仓库同时提供 AI Agent Skills，使 Agent 能理解 CST 调用边界、超表面任务语境和受控优化流程。工具链仍可独立使用、作为 Skill 集成，或作为 Python 包二次开发。

> **CST 许可证要求**：本工具不包含 CST Studio Suite，也不提供或绕过 CST 许可证。使用者必须自行安装受支持的 CST Studio Suite，并持有与实际功能相匹配的合法、有效许可证；能否启动求解器、HPC 或其他许可功能以本机 CST 许可状态为准。

---

## 项目定位与人机分工

本项目把 MCP 和 Agent 定位为超表面设计工作的**辅助者**，目标是让 AI 能接入 CST，并在用户已经给出任务方向和约束后承担耗时、重复且适合结构化执行的工作。

Agent 适合协助：

- 只读检查现有 CST 工程并整理参数、实体、边界、激励和结果状态；
- 基于当前工程和可见证据提出单元结构或参数调整建议，并明确区分事实、推断和待验证假设；
- 按用户确认的模板完成重复建模、参数替换和结果整理；
- 在用户给定目标、变量范围、约束、预算和停止条件后，协助扫参、灵敏度探测和优化迭代；
- 保存工具交互、History 关联和阶段结论，便于用户复核。

人类用户仍负责：

- 确定应用目标、总体结构路线、主要物理机制、材料与制造条件；
- 决定参数范围、评价指标、计算成本和可接受的设计权衡；
- 审查 Agent 建议，并对高成本仿真、不可逆操作和最终工程结论作出决定；
- 对设计的物理正确性、工程可实现性和最终交付结果负责。

本项目不定位为“通用超表面端到端设计”或“全自动超表面设计”系统。Agent 不应在需求缺失时替用户补全总体方案，也不应把未经人工审查的候选、仿真提交状态或局部指标写成最终设计结论。

---

## 核心能力

| 分类               | 代表工具                                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------------------------- |
| **几何建模** | `define-brick`, `define-cylinder`, `boolean-subtract`, `change-material`, `transform-shape`         |
| **工程操作** | `change-parameter`, `define-port`, `define-mesh`, `inspect-project`, `capture-3d-view`              |
| **结果读取** | `list-sparameter-results`, `export-sparameter`, `list-field-results`, `export-touchstone`       |
| **优化**     | `create-study`, `ask-study`, `tell-study`, `run-probe-phase`, `run-optimization-step`               |
| **会话管理** | `cst-session-open`, `cst-session-close`, `cst-session-quit`, `create-blank-project`, `save-project` |
| **远场**     | `export-farfield-grid`, `export-farfield-cut`, `inspect-farfield-monitors`, `inspect-model-view`      |
| **工作区**   | `init-workspace`, `init-task`, `health-check`, `health-repair`, `install-cst-libraries`               |
| **项目身份** | `verify-project-identity`, `infer-run-dir`, `wait-project-unlocked`, `list-open-projects`             |
| **审计**     | `record-stage`, `update-status`, `stage-evidence`                                                       |
| **DOE**      | `design-probes`, `analyze-probes`                                                                         |
| **运行**     | `prepare-run`, `get-run-context`                                                                          |
| **Agent 辅助** | 工程检查、单元修改建议、重复建模、受控扫参与优化编排、结果汇总和审计                                      |

Registry 工具各含严格 JSON Schema 定义，未知字段会被拒绝，输出格式以通用 `OperationResult` 为基础。工具数量和分类由 Registry 动态生成，不在文档中手工维护；可用 `devkit/tools/generate_agent_tools_list.py` 生成 Agent 暴露面快照 `tools-list.json`。

---

## 架构

### 统一契约

所有命令的输入输出格式一致：

- **入参**：JSON Schema 校验，支持 `--args-file <json>`、`--args-json`、stdin、直接标志四种传参方式
- **返回值**：`{status: "success"|"error", message?, ...}` 字典结构，零异常控制流
- **Python fast fail**：返回值是可 JSON 序列化的 `OperationResult` 字典；需要立即中止时调用 `.raise_for_error()`，读取单个字段时调用 `.unwrap("字段名")`
- **审计落盘**：每次调用自动写入 `stages/` + `logs/production_chain.md`

业务调用严格遵循 `MCP / CLI → Registry / tools → lib → core → CST`。`lib` 是唯一稳定公开 API；CST 版本、COM、VBA、History、底层对象和结果树细节均留在 `core`。

### 双层命令

- **原子工具**：单步操作，可独立调用；准确数量由 Registry 动态清册生成，不在文档中手工维护。
- **管道**：编排示例，将原子工具组合为多步流程（如 `inspect-project`、`prepare-experiment`、`run-experiment`）。

管道仅为使用参考，用户可完全按自己的策略编排工作流。

### 守卫层（Gateway）

内建 10+ 个运行时安全护栏，拦截已知 CST 陷阱：

| 陷阱 | 表现                                          | 保护                                |
| ---- | --------------------------------------------- | ----------------------------------- |
| T2   | 改参后未重建模型直接仿真                      | 拦截并提示`next_action`           |
| T3   | 远场导出后 save 损坏工程                      | 强制`save=False`                  |
| T4   | S11 复数据当 dB 用                            | `20*log10(hypot(real,imag))` 转换 |
| T5   | modeler/results session 混用                  | 拒绝跨 session 操作                 |
| T8   | Abs(E) 当增益证据                             | 拒绝非增益量                        |
| T13  | `StoreDoubleParameter` 只改参数表不重建模型 | 操作成功但附加警告                  |

每个 trap 触发时附带 `cst_raw` 上下文和 `next_action` 指导，帮助 agent 自动恢复。

> ⚠️ 守卫层基于已知模式设计，不能穷举所有设计风险。复杂工作流仍需人工审查物理假设、结果和权限边界，但这不要求对无错误的普通 VBA 调用重复读回。

### 接口成功信任原则

当前公开 MCP / CLI 接口已经通过结构化错误网关报告 VBA 执行结果。只要接口没有返回错误并给出成功状态，Agent 应充分相信 CST 已成功执行对应 VBA，不要仅为再次证明执行成功而重复进行执行前查询或执行后读回。参数、材料、普通几何、布尔操作、边界、端口、监视器和求解器配置均默认遵循这一原则。

必要检查只保留在操作本身承诺可观察产物或流程仍未完成的边界，例如确认结果导出文件存在且非空、等待异步求解结束并取得结果，或在超时、传输错误和返回状态不明确后判断副作用再决定是否重试。删除、覆盖、关闭等操作的目标和授权确认属于权限边界，不是对 CST 成功返回的重复验证。

“VBA 已成功执行”只说明 CST 接受并完成了所请求的操作，不自动证明单元设计、物理假设或最终指标正确；这些科学判断仍由结果和用户审查决定。

### 双 Session 模型

- **Modeler session**（COM 读写，`cst.interface`）：建模、仿真、参数变更
- **Results session**（只读，`cst.results`）：结果读取、S11/远场导出

严格隔离，禁止混用。仿真后关闭 modeler session，另开 results session 读取数据。

### 本地报告引擎

全内联 HTML/SVG/WebGL 报告，零 JS/CDN 外部依赖。支持 S11 多迹叠加折线图、3D 远场方向图（预计算顶点）、2D 热力图、迭代时间线、收敛分析。

---

## 扩展开发

当前 Registry 不是能力上限。只要目标 CST 版本文档明确支持对应 VBA 或 COM API，即可通过开发包扩展为 CLI 命令；未经审核的能力保持 `cli_only` 或 `experimental`。

### 手工增强路径（现有工具修改）

改函数签名 + 同步 JSON Schema。新参数带默认值，向后兼容。

### 开发参考

`devkit/references/` 包含 VBA、CST Python API、lib 门面和工具开发指南；测试体系说明见 [测试指南](docs/development/testing.md)。

---

## 快速开始

本仓库使用两套彼此隔离、但都由 uv 管理的项目内环境，详细步骤见 [INSTALL.md](INSTALL.md)：

1. `.envs/cst39`：Python 3.9，仅运行能导入 CST 库的 `cst-runtime` Worker；
2. `.envs/mcp`：Python 3.12，仅运行 `cst-mcp`，通过 stdin/stdout JSONL 与 Worker 通信。

统一由 uv 管理不等于共用环境。不要在 MCP 的 Python 3.12 环境中执行 `python -m cst_runtime`。

```powershell
# 创建或更新两个项目内环境
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-environments.ps1

# 启动 MCP；它会使用 .envs/cst39 中的 Worker
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-mcp.ps1
```

---

## 安装与集成

### 方式 A（默认）：Codex / ChatGPT 插件

仓库根目录已经是一个可分发插件：`.codex-plugin/plugin.json` 同时声明 `./skills/` 与 `./.mcp.json`。安装 `cst-mcp` 插件后，Codex 从同一插件取得四个 Skill，并由插件作用域启动 `cst-runtime` MCP 服务，不再需要单独执行 `codex mcp add cst-runtime`。

插件不会打包机器相关路径。首次启动 Codex 前，按 [INSTALL.md](INSTALL.md) 创建 `.envs/mcp`、`.envs/cst39` 和 `.cst_config.json`，并把 `CST_MCP_HOME` 指向项目根目录。启动脚本直接使用该目录中已部署的 Python 环境；`uv` 仅用于环境安装和更新。

```powershell
# 添加本仓库提供的 marketplace，然后安装插件
codex plugin marketplace add phy233/CST_MCP
codex plugin add cst-mcp@cst-mcp
```

安装或更新后重启 Codex 并新建任务，再确认四个 Skill 与插件作用域的 `cst-runtime` 工具均可见。CST 2022 路径仍按 [INSTALL.md](INSTALL.md) 在本机配置，避免把开发机绝对路径写入插件包。

### 方式 B：独立 Skill 源码（跨平台回退）

顶层 `skills/` 同时保留为规范源文件。OpenCode 等不支持 OpenAI 插件清单的平台，或不希望使用插件的用户，可以把所需的完整 Skill 文件夹复制或链接到该客户端规定的发现位置。对于 Codex，手动回退位置为：

| 作用域 | Codex 发现位置 | 适用场景 |
| --- | --- | --- |
| 当前仓库 | `<仓库根目录>/.agents/skills/<skill-name>` | 仅在本仓库内使用并随团队共享 |
| 当前用户 | `%USERPROFILE%\.agents\skills\<skill-name>` | 在本机多个仓库中使用 |
| 其他 Agent | 以相应客户端的 Skill 文档为准 | OpenCode、Cursor、Claude Code 等跨平台回退 |

应复制或链接整个 Skill 文件夹，不能只复制 `SKILL.md`，因为部分流程还依赖 `references/` 或 `scripts/`。这一步只安装工作流资源，不会创建 Python 环境或连接 MCP。使用本项目的一键部署流程还需保留完整 CST_MCP 仓库，根目录的 `scripts/setup-environments.ps1` 和 `scripts/start-mcp.ps1` 不在独立 Skill 内；已有环境则可继续复用。不要同时通过插件和手动路径安装同名副本。详细安装见 [INSTALL.md](INSTALL.md#codex-插件安装默认分发方式)，获取检查见[冷启动验收](INSTALL.md#冷启动验收)。官方结构规则见 [OpenAI Build skills](https://developers.openai.com/plugins/build/skills) 与 [Package your plugin](https://developers.openai.com/plugins/build/plugins)。

推荐组合如下：

| Skill | 作用 | 何时安装 |
| --- | --- | --- |
| `cst-mcp` | 已连接 MCP 时的工具调用和安全边界 | 使用 MCP 的基础 Skill |
| `cst-metasurface-design` | 超表面单元建议、建模语境和设计迭代边界 | 超表面/FSS/周期单元任务；通常与 `cst-mcp` 配合 |
| `cst-runtime-optimization` | 受控扫参、灵敏度探测、优化记录和早停 | 需要减轻多轮仿真负担时；与 `cst-mcp` 或 `cst-runtime-cli` 配合 |
| `cst-runtime-cli` | Runtime 部署、环境诊断和 CLI-only 运维 | 明确直接使用 CLI 或 MCP 未暴露所需操作时 |

四个 Skill 采用一套规范正文，不提供会产生重复触发的独立英文副本；需要英文匹配时，在同一 `description` 中维护必要的英文领域关键词。插件分发与跨平台回退均引用顶层 `skills/`，它是唯一规范来源。

### 方式 C：直接 CLI 使用

```powershell
git clone https://github.com/phy233/CST_MCP.git
cd CST_MCP
# 先由 uv 创建隔离的 Python 3.9 Worker 环境
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-environments.ps1
& .\.envs\cst39\Scripts\python.exe skills/cst-runtime-cli/scripts/bootstrap.py --skill-path skills/cst-runtime-cli/scripts
$env:PYTHONPATH = "$PWD\\.cst_runtime"
& .\.envs\cst39\Scripts\python.exe -m cst_runtime list-tools
```

### 方式 D：Python 包

```python
from cst_runtime.lib.session import open_project, close_project
from cst_runtime.lib.results import get_1d_result

opened = open_project("C:\\path\\model.cst").raise_for_error()
data = get_1d_result(
    "C:\\path\\model.cst",
    "1D Results\\S-Parameters\\S1,1",
).raise_for_error()
```

---

## 项目结构

```
CST_MCP/
├── .codex-plugin/
│   └── plugin.json                      # 默认插件入口，声明 Skills 与 MCP 服务
├── .mcp.json                            # 插件作用域的 cst-runtime 启动清单
├── .agents/plugins/
│   └── marketplace.json                 # 仓库 marketplace 与远端根插件入口
├── devkit/                              # 扩展开发工具包
│   ├── references/                      # VBA/CST API 官方参考、开发流程指南
│   └── tools/
│       └── generate_agent_tools_list.py # 生成 agent 暴露面快照 tools-list.json
│
├── skills/
│   ├── cst-mcp/                         # MCP 调用边界 Skill
│   ├── cst-metasurface-design/          # 超表面领域设计 Skill
│   ├── cst-runtime-cli/                 # Runtime CLI 基础设施 Skill
│   │   ├── SKILL.md                     # 精简入口与参考资料路由
│   │   ├── scripts/
│   │   │   ├── bootstrap.py             # 部署引导
│   │   │   ├── pyproject.toml           # 包定义
│   │   │   └── cst_runtime/             # 全部源码
│   │   │       ├── cli/                 # 分发层（dispatch + pipeline 编排）
│   │   │       ├── core/                # CST 交互、守卫、会话和兼容层
│   │   │       ├── tools/               # Registry 工具定义与 Schema
│   │   │       ├── render/              # 自包含 HTML/SVG/WebGL 报告
│   │   │       └── analysis/            # 远场解析与平坦度分析
│   │   ├── references/                  # CLI、故障、History 与部署说明
│   │   └── tests/
│   │       ├── refs/ref_0/              # 参考工程（四脊喇叭天线，8-12 GHz）
│   │       └── ...                      # 合约测试、架构不变式、管道合约
│   │
│   └── cst-runtime-optimization/        # 分步骤优化 Skill
│
└── docs/                                # 用户、架构、兼容性、测试与历史归档
```

## 文档索引

| 文档 | 内容 |
| --- | --- |
| [INSTALL.md](INSTALL.md) | 双 Python 环境安装与验证 |
| [docs/guides/stepwise-cst-workflow.md](docs/guides/stepwise-cst-workflow.md) | 分步骤检查、修改、验证和记录流程 |
| [skills/cst-metasurface-design/SKILL.md](skills/cst-metasurface-design/SKILL.md) | 超表面设计、仿真与结果判断 |
| [docs/architecture/error-handling.md](docs/architecture/error-handling.md) | Runtime、Worker、MCP 与 CST 错误处理边界 |
| [docs/architecture/mcp-exposure.md](docs/architecture/mcp-exposure.md) | Agent 与 CLI-only 工具暴露策略 |
| [docs/compatibility/cst-2022.md](docs/compatibility/cst-2022.md) | CST 2022 兼容性与验收状态 |
| [docs/development/testing.md](docs/development/testing.md) | 离线、Worker 与显式真机测试 |
| [devkit/README.md](devkit/README.md) | 工具维护和扩展开发入口 |
| [docs/archive/README.md](docs/archive/README.md) | 已完成审计、实验和旧 API 快照 |

## License

本项目代码采用 [MIT License](LICENSE)。原始代码版权归 `bbl21` 所有，后续修改版权归 `phy233` 所有；发布和再分发时必须保留 LICENSE 中的版权声明与许可文本。

本项目基于 [bbl21/cst-runtime-cli](https://github.com/bbl21/cst-runtime-cli) 的 MIT 许可代码继续开发。CST Studio Suite 及其许可证不属于本项目，也不包含在本项目的 MIT 授权范围内。
