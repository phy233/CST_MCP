# cst-runtime Worker 初始化手册

`cst-runtime` 只能在 CST 兼容的 Python 3.9 Worker 中运行。MCP 服务使用独立的 Python 3.12 环境，并通过 stdin/stdout JSONL 调用该 Worker。两个环境都由 uv 管理，但不得共用虚拟环境。

## 自动流程

在项目根目录执行：

```powershell
# 1. 创建 .envs/mcp 和 .envs/cst39
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-environments.ps1

# 2. 在 .cst_config.json 配置 project.cst_path；Worker 默认采用下列相对路径
#    runtime.worker_python = .envs\cst39\Scripts\python.exe

# 3. 由 cst-mcp 启动 Worker；不要在 Python 3.12 环境中导入 cst_runtime
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-mcp.ps1
```

- Python 版本（必须为 3.9）
- CST `python_cst_libraries` 导入验证
- `.cst_config.json` 的 CST 库路径，以及需要覆盖默认值时的 Worker 和 Runtime source 配置

## 环境隔离说明

`cst_runtime` 是由 Python 3.9 worker 通过 `PYTHONPATH` 载入的本地模块，不是提供给现代 Python 安装的 pip 包。

- 可用 `bootstrap.py` 将它复制至工作区的 `.cst_runtime/`，并在配置中设置 `runtime.source_path`
- 复制后的包仍必须由 Python 3.9 worker 使用；不要把它添加到 MCP 的 `pyproject.toml`
- 生产调用由 `cst-mcp` 拉起 Worker，而不是由 MCP 的 Python 3.12 环境执行 `python -m cst_runtime`

## 入口模式

| 模式 | 命令 | 条件 | 原理 |
|------|------|------|------|
| 环境初始化 | `scripts\setup-environments.ps1` | 系统中的 uv | 创建隔离的 Python 3.12 与 3.9 环境 |
| 可选部署 | `.envs\cst39\Scripts\python.exe <skill-root>\scripts\bootstrap.py` | Python 3.9 | 复制 Runtime 到独立工作区 |
| 生产 | `scripts\start-mcp.ps1` | Python 3.12 + 3.9 | MCP 通过 Worker executable 启动 Python 3.9 Runtime |

> 部署命令应在目标工作区运行；生产调用由 MCP 服务启动配置好的 Worker。

## uv 与 Python 安装

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-environments.ps1
```

脚本把 uv 下载的 Python 放在项目 `.python`，虚拟环境放在 `.envs`，缓存放在 `.uv-cache`。Conda `cst39` 仅作为旧配置兼容回退。

### CST Studio Suite 2022+

需 GUI 安装 + 商业许可（本仓库以 CST 2022 为基线，新版同样可用）。安装后确认 `python_cst_libraries` 目录存在于：
```
D:\Program Files (x86)\CST Studio Suite 2022\AMD64\python_cst_libraries
```

## 常见问题

### health-check 报 Python 版本不匹配
运行 `.envs\cst39\Scripts\python.exe --version` 确认 Worker 为 Python 3.9；若环境放在其他位置，请同步设置 `CST_MCP_HOME` 或 `runtime.worker_python`。

### pyproject.toml 创建失败
检查工作区目录写权限，或手动创建空 `pyproject.toml` 后重试。

### CST 导入验证失败
确认 CST Studio Suite 2022（或更高版本）已安装，`python_cst_libraries` 路径正确。
可指定自定义路径：
```powershell
& .\.envs\cst39\Scripts\python.exe -m cst_runtime install-cst-libraries --cst-path "D:\CST\AMD64\python_cst_libraries"
```

### uv sync 失败
确认项目根目录和 `skills/cst-runtime-cli/scripts` 中的 `pyproject.toml` 均存在，并检查网络、代理或 uv 镜像。不要手工让两个项目指向同一个 `UV_PROJECT_ENVIRONMENT`。
