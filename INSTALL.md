# 安装指南

本文档记录 CST_MCP 的完整安装与验证流程。

## 架构：高低版本 Python 隔离

本项目采用**双进程、双 Python 版本**隔离架构，两层通过 JSON-RPC（stdin/stdout）通信：

```
MCP 客户端 (Claude Desktop / opencode / ...)
    │  stdio (MCP 协议)
    ▼
┌─────────────────────────────────────────────────┐
│ MCP 层 — 高版本 Python (≥3.12)                   │
│   .venv (uv 管理, 当前为 CPython 3.14)           │
│   mcp_server/ → FastMCP, 注册 20 个工具          │
│   mcp_server/proxy.py → 启动并管理 Worker 子进程 │
└─────────────────────────────────────────────────┘
    │  配置的 Python 3.9 worker executable -m cst_runtime.worker
    │  JSON-RPC over stdin/stdout
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
| Miniconda / Anaconda | 任意                                | `C:\Users\14163\miniconda3`                                               |
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
    "source_path": "D:\\workspace\\.cst_runtime"
  },
  "project": {
    "cst_path": "D:\\Program Files (x86)\\CST Studio Suite 2022\\AMD64\\python_cst_libraries"
  }
}
```

### 2. 在现代 Python 环境中安装 `cst-mcp`

```powershell
# Python 3.12+；uv 可自行下载受管解释器
cd D:\My_Program\Python\CST_MCP
uv sync --extra dev
uv run cst-mcp
```

`cst-mcp` 不安装 `cst-runtime`，也不直接导入它。两者唯一连接是 `runtime.worker_python` 指定的可执行文件，以及进程间 stdin/stdout JSON-RPC。

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
# 1. MCP Server 冒烟测试：应输出 20 个工具
uv run python -c "from mcp_server.server import create_mcp_server; import asyncio; m = create_mcp_server(); print(len(asyncio.run(m.list_tools())))"

# 2. 端到端测试：真实拉起 cst39 Worker，测试 JSON-RPC、会话保持、崩溃自重启
uv run python tests\verify_mcp.py

# 3. 完整测试套件
uv run pytest tests\ -v
```

预期结果：

- `verify_mcp.py`：Worker 启动成功，`list_open` 返回 `{'status': 'success', ...}`；kill 后自动重启（PID 变化）

## MCP 客户端配置示例

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

> 客户端进程需要能找到 `uv` 与 `conda`（均已在用户 PATH 中）。若客户端在 PATH 修改前已启动，需重启客户端。

## 常见问题

### Worker 启动超时（`Timeout waiting for cst_worker.py to initialize`）

1. 确认 `conda` 在 PATH：`conda --version`
2. 确认 `cst39` 环境存在：`conda env list`
3. 确认 cst39 能导入 CST 库：
   ```powershell
   C:\Users\14163\miniconda3\envs\cst39\python.exe -c "import sys; sys.path.insert(0, r'D:\Program Files (x86)\CST Studio Suite 2022\AMD64\python_cst_libraries'); import cst.interface; print('OK')"
   ```

### `uv sync` 报 Python 版本不足

系统 Python 为 3.11 时 uv 会自动下载受管 Python，无需手动安装。若下载失败，检查网络或配置镜像。

### 交互式测试脚本

`tests/test_cst_connection.py`、`test_open_save.py`、`test_geometry.py` 是**手动脚本**（含 `input()` 等待、会启动真实 CST GUI），不是 pytest 用例，需单独运行：

```powershell
uv run python tests\test_cst_connection.py
```
