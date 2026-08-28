# 安装指南

本文档说明 CST_MCP 的项目内双 Python 环境、Codex 插件安装、其他 MCP 客户端接入和最小验证方法。

## 架构与目录

MCP 协议层和 CST 自动化层必须使用不同的 Python 版本，但两者都可以由 uv 管理：

```text
Codex / 其他 MCP 客户端
    │ MCP stdio
    ▼
.envs/mcp      Python 3.12，运行 cst-mcp
    │ JSONL stdin/stdout
    ▼
.envs/cst39    Python 3.9，运行 cst_runtime.worker
    │ CST Python API / VBA
    ▼
CST Studio Suite 2022+
```

默认目录均位于项目根目录：

| 目录 | 用途 | 是否入库 |
| --- | --- | --- |
| `.envs/mcp` | MCP 服务的 Python 3.12 虚拟环境 | 否 |
| `.envs/cst39` | CST Worker 的 Python 3.9 虚拟环境 | 否 |
| `.python` | uv 下载和管理的基础 Python | 否 |
| `.uv-cache` | 本项目的 uv 下载与构建缓存 | 否 |

环境隔离仍然必要：MCP 层不得直接导入 `cst_runtime`，Python 3.9 Worker 也不承担 MCP 协议服务。统一由 uv 管理，只是统一了解释器下载、依赖锁定和虚拟环境创建方式，并没有把两个运行环境合并。

## 前置条件

- Windows PowerShell；
- [uv](https://docs.astral.sh/uv/getting-started/installation/)；
- CST Studio Suite 2022 或更高版本及有效许可证；
- CST 安装目录中的 `AMD64\python_cst_libraries`。

## 一次性创建环境

在仓库根目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-environments.ps1
```

开发者需要 pytest 时使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-environments.ps1 -IncludeDev
```

脚本会分别同步两个 uv 项目：根目录 `pyproject.toml` 对应 Python 3.12 MCP，`skills/cst-runtime-cli/scripts/pyproject.toml` 对应 Python 3.9 Worker。Worker 默认安装 `sweep`、`optimization` 和 `report` 三组可选依赖，因为当前 Registry 中的相关工具都需要保留。

若确实需要把环境放到其他固定目录，可传入 `-EnvironmentRoot <绝对路径>`；同时把同一路径设置为 `CST_MCP_HOME`，避免插件与手工启动使用不同环境。

## 本机配置

项目根目录的 `.cst_config.json` 不入 Git，因为 CST 安装位置属于机器配置。推荐写法：

```json
{
  "runtime": {
    "worker_python": ".envs\\cst39\\Scripts\\python.exe",
    "long_run_threshold_seconds": 600,
    "simulation_timeout": 1200,
    "session_timeout": 300
  },
  "project": {
    "cst_path": "D:\\Program Files (x86)\\CST Studio Suite 2022\\AMD64\\python_cst_libraries"
  }
}
```

`runtime.worker_python` 和可选的 `runtime.source_path` 如果是相对路径，均相对 `.cst_config.json` 所在目录解析。因此 Codex 即使从插件缓存启动，也不会把路径错误地解释成缓存目录。

环境变量的优先级高于配置文件：

- `CST_MCP_HOME`：环境和默认配置所在的固定根目录；
- `CST_MCP_CONFIG`：显式指定配置文件；
- `CST_WORKER_PYTHON`：显式指定 Python 3.9 解释器；
- `CST_PYTHON_LIBS`：显式指定 CST Python 库目录。

未显式配置 Worker 时，MCP 会先查找配置目录下的 `.envs/cst39/Scripts/python.exe`，再兼容探测旧的 Conda `cst39` 环境。Conda 只是向后兼容回退，不再是默认安装要求。

## 本地启动与最小验证

```powershell
# 查看两个解释器版本
& .\.envs\mcp\Scripts\python.exe --version
& .\.envs\cst39\Scripts\python.exe --version

# 验证 Worker 能导入 CST 接口；不启动 CST
& .\.envs\cst39\Scripts\python.exe -c "import sys; sys.path.insert(0, r'D:\Program Files (x86)\CST Studio Suite 2022\AMD64\python_cst_libraries'); import cst.interface; print('OK')"

# 启动 MCP；正常情况下保持 stdio 等待客户端
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-mcp.ps1
```

开发者只运行与本次修改相关的测试，不要求每次执行全量或真实 CST 测试：

```powershell
& .\.envs\mcp\Scripts\python.exe -m pytest mcp_server\tests\test_mcp_server.py -q
```

## Codex 插件安装（默认分发方式）

仓库根目录是一个插件包：`.codex-plugin/plugin.json` 同时声明 `./skills/` 和 `./.mcp.json`。安装后，四个 Skill 与 `cst-runtime` MCP 服务来自同一插件，不要再注册第二份同名 MCP。

先把工程目录写入当前用户环境，使插件缓存复用本项目内的环境和配置：

```powershell
$projectRoot = (Resolve-Path .).Path
[Environment]::SetEnvironmentVariable("CST_MCP_HOME", $projectRoot, "User")
```

随后安装插件：

```powershell
codex plugin marketplace add phy233/CST_MCP
codex plugin add cst-mcp@cst-mcp
```

环境变量修改后需要完全退出并重启 Codex，再新建任务验收。旧任务已经完成工具发现，不用于判断冷启动是否成功。

### 冷启动验收

在新任务中分别确认：

1. `/skills` 或 `$` 选择器能看到 `cst-mcp`、`cst-metasurface-design`、`cst-runtime-cli` 和 `cst-runtime-optimization`；
2. 工具目录能看到插件提供的 `cst-runtime` 工具；工具数由 Runtime Registry 动态决定，不用 README 中的固定数字验收；
3. 调用只读的 `list-tools` 或 `describe-tool` 能得到结构化结果。

Skill 可见只证明工作流文档成功分发；MCP 工具可见只证明服务连接和 Registry 获取成功；两者都不等于真实 CST 建模或求解已经通过。

## 不支持插件的平台

OpenCode 等不支持 OpenAI 插件分发的平台，可以继续使用仓库顶层 `skills/` 作为规范源文件。必须复制或链接完整 Skill 文件夹，包括 `references/` 和 `scripts/`，不能只复制 `SKILL.md`。

独立 MCP 客户端可直接调用启动脚本：

```json
{
  "mcpServers": {
    "cst-runtime": {
      "command": "powershell.exe",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "D:\\My_Program\\Python\\CST_MCP\\scripts\\start-mcp.ps1"
      ]
    }
  }
}
```

## Runtime 工作区副本（可选）

默认直接使用插件或仓库中的 `skills/cst-runtime-cli/scripts`。只有不支持插件打包、需要独立部署或进行恢复操作时，才用 Python 3.9 创建 `.cst_runtime` 工作区副本：

```powershell
& .\.envs\cst39\Scripts\python.exe .\bootstrap.py --skill-path .\skills\cst-runtime-cli\scripts
```

使用副本时，在 `.cst_config.json` 中配置 `runtime.source_path`。不要把副本加入 Git，也不要把 Runtime 安装进 MCP 的 Python 3.12 环境。

## 常见问题

### uv 找不到或下载 Python 失败

`uv` 命令本身需要先安装在系统中；项目内管理的是 Python、虚拟环境和缓存。若下载失败，检查网络、代理或 uv 镜像配置。Python 3.9 已结束官方生命周期，但 uv 仍可安装对应解释器；本项目保留它是为了兼容 CST 2022。

### Worker 启动失败

先确认 `.envs/cst39/Scripts/python.exe` 存在，再检查 `.cst_config.json` 的 `project.cst_path`。只有接口返回错误、超时或结果产物缺失时才进一步诊断；普通成功返回不需要重复进行执行前和执行后检查。

### 修改环境变量后 Codex 仍使用旧值

Windows 图形程序会继承启动时的环境快照。关闭所有 Codex 窗口和后台进程后重新启动，再新建任务。若仍失败，检查 `CST_MCP_HOME` 是否指向包含 `.envs` 和 `.cst_config.json` 的同一目录。
