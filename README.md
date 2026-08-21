# CST Runtime CLI

CST Studio Suite 自动化 CLI、MCP 与 AI Agent 基础设施。Runtime Registry 提供建模、仿真、结果读取、参数优化、远场导出、History 和审计能力，并通过统一 JSON 契约与运行时守卫控制 CST 调用。CLI 工具不等于 MCP 暴露面；只有明确标记为 `agent` 的工具才会注册到 MCP。

项目同时以 AI 工具 skill 形式发布，但工具链本身是通用设计——可独立使用、作为 skill 集成、或作为 Python 包二次开发。

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

> ⚠️ 守卫层基于已知模式设计，不能穷举所有 CST 异常。复杂工作流仍需在关键节点人工复核。

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

本仓库有两套必须隔离的安装流程，详细步骤见 [INSTALL.md](INSTALL.md)：

1. `cst-runtime` 仅部署并运行在能导入 CST 库的 **Python 3.9** worker 中；不要用 `uv` 或现代 Python 安装它。
2. `cst-mcp` 安装在 **Python 3.12+** 的现代虚拟环境中；它只通过配置的 worker executable 和 stdin/stdout JSONL 与 runtime 通信。

先完成 `INSTALL.md` 中的 worker 配置后，再由 MCP 客户端调用工具。不要在 MCP 的 `.venv` 中执行 `python -m cst_runtime`。

```powershell
# 安装现代 Python 环境中的 MCP 服务
uv sync --extra dev

# 使用配置的 Python 3.9 worker 部署 runtime（仅在需要工作区副本时）
& $env:CST_WORKER_PYTHON .\bootstrap.py --skill-path <skill-root>\scripts

# 启动 MCP 服务；它会自动启动 Python 3.9 worker
uv run cst-mcp
```

---

## 参考工程

`skills/cst-runtime-cli/tests/refs/ref_0/ref_0.cst` — 四脊喇叭天线，8-12 GHz，含完整建模历史（VBA 737 行）。用于在真实 CST 上验证工具和管道。不含仿真结果缓存，可仿真生成或从工作区获取缓存。

---

## 安装与集成

### 方式 A：AI 工具 skill

解压到对应工具的 skills 目录：

| AI 工具                         | 路径                                                             |
| ------------------------------- | ---------------------------------------------------------------- |
| OpenCode / Cursor / Claude Code | `%USERPROFILE%\.config\opencode\skills\`（或其他工具对应路径） |

解压后按需要安装 `cst-mcp`、`cst-runtime-cli`、`cst-metasurface-design` 和 `cst-runtime-optimization` Skill；Runtime 代码随 `cst-runtime-cli` 提供。

### 方式 B：直接 CLI 使用

```powershell
git clone https://github.com/anomalyco/cst-runtime-cli.git
cd cst-runtime-cli
# 必须是 CST 兼容的 Python 3.9，不是 uv 创建的现代 .venv
& $env:CST_WORKER_PYTHON skills/cst-runtime-cli/scripts/bootstrap.py --skill-path skills/cst-runtime-cli/scripts
$env:PYTHONPATH = "$PWD\\.cst_runtime"
& $env:CST_WORKER_PYTHON -m cst_runtime list-tools
```

### 方式 C：Python 包

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
cst-runtime-cli/
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

MIT
