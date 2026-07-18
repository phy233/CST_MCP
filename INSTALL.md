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
    │  conda run -n cst39 python cst_worker.py
    │  JSON-RPC over stdin/stdout
    ▼
┌─────────────────────────────────────────────────┐
│ CST Core 层 — 低版本 Python (3.9)                │
│   conda 环境 cst39                               │
│   skills/cst-runtime-cli/scripts/cst_worker.py   │
│   → cst_runtime.lib.* / cst_runtime.core.*       │
│   → cst.interface (COM) → CST Studio Suite       │
└─────────────────────────────────────────────────┘
```

- **MCP 层**只负责 MCP 协议与工具注册，**禁止**直接 import `cst_runtime`（见 `proxy.py`  docstring）。
- **CST Core 层**必须用能导入 CST `python_cst_libraries` 的低版本 Python（CST 2022 对应 Python 3.9），因此固定在 conda 环境 `cst39` 中运行。
- Worker 启动时从 `.cst_config.json` 读取 `cst_path` 并注入 `sys.path`，从而 `import cst.interface`。

## 前置条件

| 组件 | 版本要求 | 本机路径（参考） |
|------|----------|------------------|
| CST Studio Suite | 2022+（含 `python_cst_libraries`） | `D:\Program Files (x86)\CST Studio Suite 2022\AMD64\python_cst_libraries` |
| Miniconda / Anaconda | 任意 | `C:\Users\14163\miniconda3` |
| conda 环境 `cst39` | Python 3.9 | `conda create -n cst39 python=3.9` |
| uv 包管理器 | 任意 | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` |

## 关键：conda 必须加入用户 PATH

MCP 层通过 `mcp_server/proxy.py` 执行以下命令启动 Worker：

```python
cmd_str = f'conda run -n cst39 --no-capture-output python "{worker_script}"'
```

这要求 **`conda` 命令在 PATH 中可解析**。MCP 客户端（Claude Desktop 等）以服务方式拉起 MCP Server 时继承的是用户登录环境，因此必须**永久加入用户 PATH**（仅当前会话临时设置会在客户端重启后失效）。

将以下两项加入用户环境变量 `Path`：

```
C:\Users\14163\miniconda3\condabin
C:\Users\14163\miniconda3\Scripts
```

> 注意：**不要**加入 `C:\Users\14163\miniconda3` 根目录，否则 base 环境的 `python.exe` 会遮蔽系统已有的 Python。

PowerShell 一键执行（永久生效）：

```powershell
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$toAdd = @("C:\Users\14163\miniconda3\condabin", "C:\Users\14163\miniconda3\Scripts")
$entries = $userPath -split ';' | Where-Object { $_ }
foreach ($p in $toAdd) { if ($entries -notcontains $p) { $entries += $p } }
[Environment]::SetEnvironmentVariable("Path", ($entries -join ';'), "User")
```

修改后**重启 MCP 客户端**（或注销重登）使其继承新 PATH。

## 安装步骤

```powershell
# 1. 安装 uv（若未安装）
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. 创建低版本 Worker 环境（若 cst39 不存在）
conda create -n cst39 python=3.9 -y

# 3. 确认 .cst_config.json 指向本机 CST 库路径
#    {"project": {"cst_path": "<CST安装目录>\\AMD64\\python_cst_libraries"}}

# 4. 创建高版本虚拟环境并安装依赖（uv 自动下载 Python ≥3.12）
cd D:\My_Program\Python\CST_MCP
uv sync --extra dev
```

`uv sync` 会：自动下载 CPython 3.12+（当前解析为 3.14）→ 创建 `.venv` → 安装 `mcp[cli]`、`pytest` 等 44 个包 → 以可编辑方式安装本项目（生成 `.venv\Scripts\cst-mcp.exe` 入口）。

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

- `verify_mcp.py`：Worker 启动成功，`list_open` 返回 `{'status': 'success', ...}`；kill 后自动重启（PID 变化）。
- `pytest`：**12 passed, 13 failed 为当前已知正常状态**。13 个失败全部在 `tests/test_mcp_server.py`，原因是该测试文件仍引用旧版 adapter API（`list_available_tools` / `TOOL_SPECS` / `_wrap_lib_function` / `cst_runtime_root`），与当前实现不匹配——属于待修复的测试代码，**不是安装问题**。

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
