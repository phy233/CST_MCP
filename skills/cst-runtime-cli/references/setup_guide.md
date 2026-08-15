# cst-runtime Worker 初始化手册

`cst-runtime` 只能在 CST 兼容的 Python 3.9 worker 中运行。MCP 服务使用独立的 Python 3.12+ 环境，并通过 stdin/stdout JSONL 调用该 worker；两者不得共用虚拟环境。

## 自动流程

在工作目录（测试区或任务目录）执行，不在 skill 目录：

```powershell
# 1. 确认当前解释器确为 Python 3.9
python --version

# 2. 由 Python 3.9 部署 runtime；不要使用 uv 或 MCP 的 .venv
python <skill-root>\scripts\bootstrap.py --skill-path <skill-root>\scripts

# 3. 在 .cst_config.json 配置 runtime.source_path、runtime.worker_python 和 project.cst_path
# 4. 由 cst-mcp 启动 worker；不要在现代 Python 中导入 cst_runtime
```

- Python 版本（必须为 3.9）
- CST `python_cst_libraries` 导入验证
- `.cst_config.json` 的 worker executable 与 runtime source 配置

## 环境隔离说明

`cst_runtime` 是由 Python 3.9 worker 通过 `PYTHONPATH` 载入的本地模块，不是提供给现代 Python 安装的 pip 包。

- 可用 `bootstrap.py` 将它复制至工作区的 `.cst_runtime/`，并在配置中设置 `runtime.source_path`
- 复制后的包仍必须由 Python 3.9 worker 使用；不要把它添加到 MCP 的 `pyproject.toml`
- 生产调用由 `cst-mcp` 拉起 worker，而不是由 `uv run python -m cst_runtime` 拉起

## 入口模式

| 模式 | 命令 | 条件 | 原理 |
|------|------|------|------|
| 部署 | `python <skill-root>\scripts\bootstrap.py` | Python 3.9 | 复制 runtime 到供 worker 使用的位置 |
| 生产 | `uv run cst-mcp` | Python 3.12+ | MCP 通过 worker executable 启动 Python 3.9 runtime |

> 部署命令应在目标工作区运行；生产调用由 MCP 服务启动配置好的 Worker。

## 上下游工具安装

### Python 3.9（仅 cst-runtime worker）

```powershell
# 静默安装（仅当前用户）
conda create -n cst39 python=3.9 -y
```

Python 安装后若 `python` 仍不可用，注销重登录或手动刷新 PATH。

### Python 3.12+ 与 uv（仅 cst-mcp）

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### CST Studio Suite 2022+

需 GUI 安装 + 商业许可（本仓库以 CST 2022 为基线，新版同样可用）。安装后确认 `python_cst_libraries` 目录存在于：
```
D:\Program Files (x86)\CST Studio Suite 2022\AMD64\python_cst_libraries
```

## 常见问题

### health-check 报 Python 版本不匹配
运行 `python --version` 确认 worker 为 Python 3.9；若不是，请改用 `.cst_config.json` 中的 `runtime.worker_python`。

### pyproject.toml 创建失败
检查工作区目录写权限，或手动创建空 `pyproject.toml` 后重试。

### CST 导入验证失败
确认 CST Studio Suite 2022（或更高版本）已安装，`python_cst_libraries` 路径正确。
可指定自定义路径：
```powershell
python -m cst_runtime install-cst-libraries --cst-path "D:\CST\AMD64\python_cst_libraries"
```

### uv sync 失败
这是 cst-mcp 的独立安装步骤；确认项目根目录的 `pyproject.toml` 存在、Python ≥3.12、网络正常。不要在 runtime 工作区执行它。
