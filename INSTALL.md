# 安装指南

本文档记录 CST_MCP 的完整安装与验证流程。

## 架构：高低版本 Python 隔离

本项目采用**双进程、双 Python 版本**隔离架构，两层通过 JSONL（stdin/stdout）通信：

```
MCP 客户端 (Claude Desktop / opencode / ...)
    │  stdio (MCP 协议)
    ▼
┌─────────────────────────────────────────────────┐
│ MCP 层 — 高版本 Python (≥3.12)                   │
│   .venv (uv 管理, 当前为 CPython 3.14)           │
│   mcp_server/ → FastMCP, 动态注册 agent 工具     │
│   mcp_server/proxy.py → 启动并管理 Worker 子进程 │
└─────────────────────────────────────────────────┘
    │  配置的 Python 3.9 worker executable -m cst_runtime.worker
    │  JSONL over stdin/stdout
    ▼
┌─────────────────────────────────────────────────┐
│ CST Core 层 — 低版本 Python (3.9)                │
│   conda 环境 cst39                               │
│   cst_runtime.worker（由 worker executable 启动） │
│   → Registry / tools → cst_runtime.lib.*         │
│   → cst_runtime.core.* → CST COM / VBA / Results │
│   → cst.interface (COM) → CST Studio Suite       │
└─────────────────────────────────────────────────┘
```

- **MCP 层**只负责 MCP 协议与工具注册，**禁止**直接 import `cst_runtime`（见 `proxy.py`  docstring）。
- **公开业务边界**固定为 `cst_runtime.lib`；tools、CLI pipeline 和 workflow 禁止跨层调用 `core`。
- **CST Core 层**必须用能导入 CST `python_cst_libraries` 的低版本 Python（CST 2022 对应 Python 3.9），因此固定在 conda 环境 `cst39` 中运行。
- Worker 启动时从 `.cst_config.json` 读取 `cst_path` 并注入 `sys.path`，从而 `import cst.interface`；MCP 进程只读取配置并创建子进程，不会导入 runtime。

## 前置条件

| 组件                 | 版本要求                            | 本机路径（参考）                                                            |
| -------------------- | ----------------------------------- | --------------------------------------------------------------------------- |
| CST Studio Suite     | 2022+（含`python_cst_libraries`） | `D:\Program Files (x86)\CST Studio Suite 2022\AMD64\python_cst_libraries` |
| Miniconda / Anaconda | 任意                                | `C:\Users\<用户名>\miniconda3`                                            |
| conda 环境`cst39`  | Python 3.9                          | `conda create -n cst39 python=3.9`                                        |
| uv 包管理器          | 任意                                | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"`              |

## 两套安装流程

### 1. 在 CST Python 3.9 环境中部署 `cst-runtime`

```powershell
# 仅首次创建 worker 环境
conda create -n cst39 python=3.9 -y

# 获取该环境的解释器路径，并持久配置给 MCP 服务
$env:CST_WORKER_PYTHON = "C:\Users\<用户名>\miniconda3\envs\cst39\python.exe"

# 可选：部署一份 runtime 工作区副本；不要使用 uv 执行此命令
& $env:CST_WORKER_PYTHON .\bootstrap.py --skill-path .\skills\cst-runtime-cli\scripts
```

若使用部署后的副本，在 `.cst_config.json` 增加 `runtime.source_path`；否则默认使用仓库内 `skills/cst-runtime-cli/scripts`。worker executable 必须是 **Python 3.9**，不可填 `.venv\Scripts\python.exe`。

```json
{
  "runtime": {
    "worker_python": "C:\\Users\\<用户名>\\miniconda3\\envs\\cst39\\python.exe",
    "source_path": "D:\\workspace\\.cst_runtime",
    "long_run_threshold_seconds": 600,
    "simulation_timeout": 1200,
    "session_timeout": 300
  },
  "project": {
    "cst_path": "D:\\Program Files (x86)\\CST Studio Suite 2022\\AMD64\\python_cst_libraries"
  }
}
```

超时预算三键（均可省缺，省缺值即上例）：

- `long_run_threshold_seconds`（默认 600）：长任务分界。solver 实际运行达到该秒数时，
  run-experiment / wait-simulation 返回 `long_run_relinquish` 终态信号并保留 CST 继续运行；
- `simulation_timeout`（默认 1200）：MCP 传输层硬兜底，必须大于长任务分界。超 10 小时的
  单次求解请调大该值（如 39600），否则按 detached 协议分离后只读取证结果；
- `session_timeout`（默认 300）：cst-session-open/close 等会话类操作的预算。

语义细节见 [docs/architecture/error-handling.md](docs/architecture/error-handling.md) 的
"长任务双态终止协议（L1/L2）"节。

### 2. 在现代 Python 环境中安装 `cst-mcp`

```powershell
# Python 3.12+；uv 可自行下载受管解释器
cd D:\My_Program\Python\CST_MCP
uv sync --extra dev
uv run cst-mcp
```

`cst-mcp` 不安装 `cst-runtime`，也不直接导入它。两者唯一连接是 `runtime.worker_python` 指定的可执行文件，以及进程间 stdin/stdout JSONL。

## 安装步骤

```powershell
# 1. 安装 uv（用于 cst-mcp 的现代 Python 环境；若未安装）
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. 创建并配置 Python 3.9 worker（仅供 cst-runtime 使用）
conda create -n cst39 python=3.9 -y

# 3. 在 .cst_config.json 中同时设置 runtime.worker_python 和 project.cst_path

# 4. 创建高版本虚拟环境并仅安装 cst-mcp 依赖
cd D:\My_Program\Python\CST_MCP
uv sync --extra dev
```

`uv sync` 会：自动下载 CPython 3.12+ → 创建 `.venv` → 安装 `mcp[cli]`、`pytest` 等依赖 → 以可编辑方式安装 `cst-mcp`（生成 `.venv\Scripts\cst-mcp.exe` 入口）。它不会安装或运行 `cst-runtime`。

## 验证

```powershell
# 1. MCP Server 冒烟测试：应输出当前 Runtime Registry 中全部 agent 工具
uv run python -c "from mcp_server.server import create_mcp_server; import asyncio; m = create_mcp_server(); print(len(asyncio.run(m.list_tools())))"

# 2. 端到端测试：真实拉起 cst39 Worker，测试 JSONL、会话保持、崩溃自重启
uv run python -m pytest mcp_server\tests -q -m worker_proxy

# 3. 完整测试套件（分层命令详见 docs/development/testing.md）
uv run python -m pytest -q
```

预期结果：

- `worker_proxy` 用例：Worker 启动成功，`list_open` 返回 `{'status': 'success', ...}`；kill 后自动重启（PID 变化）

## 独立 MCP 客户端配置示例（非 Codex 插件方式）

Claude Desktop（`claude_desktop_config.json`）或其他 MCP 客户端：

```json
{
  "mcpServers": {
    "cst-runtime": {
      "command": "uv",
      "args": ["run", "--directory", "D:\\My_Program\\Python\\CST_MCP", "cst-mcp"]
    }
  }
}
```

> 该段仅供不支持插件的 MCP 客户端使用。Codex 插件用户不应再单独注册同名 `cst-runtime`，否则会同时加载两份服务。客户端进程需要能找到 `uv`，并有权限执行配置的 Python 3.9 Worker；若环境或配置在客户端启动后才修改，需重启客户端。

## 插件优先的 Skill 安装与获取验证

### 同一插件中的 MCP 工具与 Skill

- `.codex-plugin/plugin.json` 声明四个 Skill，并通过 `mcpServers` 指向根目录 `.mcp.json`；
- `.mcp.json` 由插件作用域执行 `uv run cst-mcp`，Runtime Registry 仍动态决定 Agent 实际取得的工具；
- Skill 发现和 MCP 进程启动是同一插件的两个组件，仍需分别验收：Skill 可见不代表本机 Worker 配置正确，工具连接成功也不代表具体 CST 仿真已经执行。

### 默认方式：安装仓库插件

仓库根目录的 `.codex-plugin/plugin.json` 把 `./skills/` 和 `./.mcp.json` 作为插件组件，`.agents/plugins/marketplace.json` 则把 `cst-mcp` 指向 Git 仓库根目录。Codex 用户默认通过插件取得全部四个 Skill 与 `cst-runtime` 工具服务：

```powershell
codex plugin marketplace add phy233/CST_MCP
codex plugin add cst-mcp@cst-mcp
```

插件清单使用可移植的 `uv run cst-mcp`，不会写入开发机绝对路径。`.mcp.json` 通过 `env_vars` 白名单转发 `CST_MCP_CONFIG`、`CST_WORKER_PYTHON`、`SystemRoot` 和 `windir`；后两项用于保证 Windows 上由 Codex 启动的 Python 子进程能够取得系统目录。首次启动 Codex 前，设置前两项机器相关变量；以下 PowerShell 示例写入当前用户环境，修改后需完全退出并重新启动 Codex：

```powershell
$configPath = (Resolve-Path .\.cst_config.json).Path
[Environment]::SetEnvironmentVariable("CST_MCP_CONFIG", $configPath, "User")
[Environment]::SetEnvironmentVariable("CST_WORKER_PYTHON", "C:\Users\<用户名>\miniconda3\envs\cst39\python.exe", "User")
```

项目内 `.codex/config.toml` 只保留 `plugins."cst-mcp".mcp_servers.cst-runtime` 下的启用状态和工具审批策略，不再声明独立的 `[mcp_servers.cst-runtime]`。插件安装后应重启 Codex 并新建任务；旧任务不作为冷启动发现验收。

### 回退方式：直接安装 Skill 源文件

仓库内的顶层 `skills/` 仍是唯一规范源码，同时也是插件实际打包的目录。OpenCode 等不支持 OpenAI 插件清单的平台，按各自客户端文档，把所需的完整 Skill 文件夹复制或链接到其原生发现位置。Codex 也可以使用以下手动回退位置：

| 作用域 | 发现位置 |
| --- | --- |
| 当前仓库 | `<仓库根目录>/.agents/skills/<skill-name>` |
| 当前用户 | `%USERPROFILE%\.agents\skills\<skill-name>` |

必须保留 Skill 文件夹内的 `references/` 和 `scripts/`。不要只复制 `SKILL.md`，也不要同时通过插件、仓库级目录和用户级目录安装同名副本。手动安装后若选择器未更新，重启客户端并新建任务再检查。

建议按任务安装：

- 普通 MCP 操作：`cst-mcp`；
- 超表面单元建议和重复建模：`cst-mcp` + `cst-metasurface-design`；
- 扫参或优化：在上述组合上增加 `cst-runtime-optimization`；
- 直接 CLI、部署、恢复或 CLI-only 操作：增加 `cst-runtime-cli`。

### 冷启动验收

安装或更新后，新建一个 Codex 任务并分别检查：

1. **Skill 获取**：在 `/skills` 或 `$` 选择器中能够看到已安装的 Skill；显式输入 `$cst-mcp` 时能加载对应说明。
2. **MCP 工具获取**：客户端工具目录中能够看到由 `cst-mcp` 插件提供的 `cst-runtime` 工具。工具数量由当前 Runtime Registry 动态决定，不以 README 中的固定数字验收。
3. **路由边界**：超表面任务可组合加载 `cst-metasurface-design`；优化意图可组合加载 `cst-runtime-optimization`；纯理论讨论不应因为出现普通 RF 术语而自动调用 CST。

| 现象 | 结论与下一步 |
| --- | --- |
| MCP 工具可见，四个 Skill 不可见 | MCP 已连接；检查插件是否安装并启用，或检查独立 Skill 回退路径 |
| Skill 可见，MCP 工具不可见 | Skill 已安装，但 MCP 客户端配置、进程或连接仍需检查 |
| 两者都可见 | Agent 已同时取得工作流说明和工具接口；这仍不等于真实 CST 仿真已经通过 |
| 插件安装后 Skill 仍不可见 | 确认插件未被禁用、marketplace 指向 `cst-mcp`，然后在新任务中复查 |
| 同名 Skill 出现多次 | 插件和手动发现位置存在重复安装；保留一种分发方式后重启客户端 |

## 常见问题

### Worker 启动超时（`Timeout waiting for cst_worker.py to initialize`）

1. 确认 `.cst_config.json` 的 `runtime.worker_python` 指向 Python 3.9。
2. 确认 Worker 可执行：`& $env:CST_WORKER_PYTHON --version`。
3. 确认 Worker 能导入 CST 库：
   ```powershell
   & $env:CST_WORKER_PYTHON -c "import sys; sys.path.insert(0, r'D:\Program Files (x86)\CST Studio Suite 2022\AMD64\python_cst_libraries'); import cst.interface; print('OK')"
   ```

### `uv sync` 报 Python 版本不足

系统 Python 为 3.11 时 uv 会自动下载受管 Python，无需手动安装。若下载失败，检查网络或配置镜像。
