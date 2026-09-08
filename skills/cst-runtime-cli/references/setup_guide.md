# cst-runtime Worker 初始化手册

`cst-runtime` 只能在 CST 兼容的 Python 3.9 Worker 中运行。MCP 服务使用独立的 Python 3.12 环境，并通过 stdin/stdout JSONL 调用该 Worker。两个环境都由 uv 管理，但不得共用虚拟环境。

## 部署前提与路径

本指南的一键部署依赖完整 CST_MCP 仓库。仓库根目录应包含 `scripts/setup-environments.ps1`、`scripts/start-mcp.ps1`、`mcp_server/` 和 `skills/cst-runtime-cli/scripts/`。单独复制完整 Skill 文件夹只取得工作流资源和 Runtime 源码，不包含仓库根目录的启动脚本或 MCP 服务。

已有部署时复用现有解释器和连接；需要从零部署时，先取得完整仓库。下列相对命令均在该仓库根目录执行，不在 Skill 目录或待仿真的工程目录执行。若设置了 `CST_MCP_HOME`，它指向环境和默认配置所在目录，不替代源码仓库位置。

## 创建环境与启动 MCP

仅在用户要求部署或修复环境时执行；一般建模任务不重复同步依赖。系统需先安装 uv，安装方法见其[官方安装说明](https://docs.astral.sh/uv/getting-started/installation/)。

```powershell
# 1. 创建 .envs/mcp 和 .envs/cst39
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-environments.ps1

# 2. 在 .cst_config.json 配置 project.cst_path；Worker 默认采用下列相对路径
#    runtime.worker_python = .envs\cst39\Scripts\python.exe

# 3. 由 cst-mcp 启动 Worker；不要在 Python 3.12 环境中导入 cst_runtime
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-mcp.ps1
```

部署验收只需确认 Worker 为 Python 3.9、能够导入 CST 接口，以及配置路径指向实际安装目录。环境就绪不等于真实 CST 建模或求解通过。

## 环境隔离说明

`cst_runtime` 可安装到 Python 3.9 环境，MCP 也可通过 Worker 的 `PYTHONPATH` 指定其源码；不要将它安装到 MCP 的 Python 3.12 环境。

- 可用 `bootstrap.py` 将它复制至工作区的 `.cst_runtime/`，并在配置中设置 `runtime.source_path`
- 复制后的包仍必须由 Python 3.9 worker 使用；不要把它添加到 MCP 的 `pyproject.toml`
- MCP 调用由 `cst-mcp` 拉起 Worker；直接 CLI 调用使用 Python 3.9 解释器执行 `python -m cst_runtime`

## 入口模式

| 模式 | 命令 | 条件 | 原理 |
|------|------|------|------|
| 环境初始化 | `scripts\setup-environments.ps1` | 系统中的 uv | 创建隔离的 Python 3.12 与 3.9 环境 |
| 可选部署 | `& <Python-3.9绝对路径> <skill-root>\scripts\bootstrap.py --skill-path <skill-root>\scripts` | 已部署 Python 3.9 | 在目标工作区复制 Runtime |
| 生产 | `scripts\start-mcp.ps1` | Python 3.12 + 3.9 | MCP 通过 Worker executable 启动 Python 3.9 Runtime |

只有创建 `.cst_runtime` 副本的 `bootstrap.py` 在目标工作区运行，解释器与 Skill 路径使用绝对路径。它会替换该工作区已有的 Runtime 副本，仅在明确授权的部署或更新范围内执行；环境创建和 MCP 启动仍使用完整仓库中的脚本。

脚本把 uv 下载的 Python 放在项目 `.python`，虚拟环境放在 `.envs`，缓存放在 `.uv-cache`。Conda `cst39` 仅作为旧配置兼容回退。

## CST 版本与许可证

本仓库以 CST Studio Suite 2022 为支持基线，需要本机安装与有效商业许可证。周期边界、Floquet、Plane Wave 和频域求解器设置构造器目前仅支持 2022；其他版本须按具体工具和目标版本手册确认，不能因版本较新就宣称兼容。

下面仅为安装路径示例，请在 `.cst_config.json` 中填写本机实际的 `python_cst_libraries` 目录：
```
D:\Program Files (x86)\CST Studio Suite 2022\AMD64\python_cst_libraries
```

## 常见问题

### health-check 报 Python 版本不匹配
运行 `.envs\cst39\Scripts\python.exe --version` 确认 Worker 为 Python 3.9；若环境放在其他位置，请同步设置 `CST_MCP_HOME` 或 `runtime.worker_python`。

### CST 导入验证失败
确认目标 CST 版本与 Worker 兼容，且 `python_cst_libraries` 路径正确；只有需要安装或修复接口库时才执行下面的命令。
可指定自定义路径：
```powershell
& .\.envs\cst39\Scripts\python.exe -m cst_runtime install-cst-libraries --cst-path "D:\CST\AMD64\python_cst_libraries"
```

### uv sync 失败
确认项目根目录和 `skills/cst-runtime-cli/scripts` 中的 `pyproject.toml` 均存在，并检查网络、代理或 uv 镜像。不要手工让两个项目指向同一个 `UV_PROJECT_ENVIRONMENT`。
