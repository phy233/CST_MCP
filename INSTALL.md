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
CST Studio Suite 2022（支持基线）
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
- CST Studio Suite 2022 及有效许可证；其他版本须按具体工具核对兼容性，不保证向上兼容；
- CST 安装目录中的 `AMD64\python_cst_libraries`。

当前周期边界、Floquet、Plane Wave 和频域求解器设置构造器仅支持 CST 2022；其他版本的能力边界见 [CST 兼容性记录](docs/compatibility/cst-2022.md#当前状态2026-08-核查结论)。

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
3. 首次接入时调用只读的 `health-check`（`workspace` 传空字符串）能得到结构化结果。`tools/list` 是 MCP 的工具发现协议请求，不是名为 `list-tools` 的业务工具。

Skill 可见只证明工作流文档成功分发；MCP 工具可见只证明服务连接和 Registry 获取成功；两者都不等于真实 CST 建模或求解已经通过。

## OpenCode 接入（1.18.23）

本节依据 [OpenCode 官方 MCP 文档](https://opencode.ai/docs/mcp-servers/)与 [配置文档](https://opencode.ai/docs/config/)，适用于 OpenCode 1.18.23。该版本使用 `mcp.<服务名>`、命令数组 `command`、环境变量对象 `environment` 和 `enabled`。仓库的 `.mcp.json` 是 Codex 插件配置，其中的 `args`、`env_vars`、`startup_timeout_sec` 和 `tool_timeout_sec` 不能原样复制到 OpenCode。

### 配置位置与启动命令

1. 先按本文完成双 Python 环境与 `.cst_config.json` 配置；已有部署可以复用。
2. 打开 [配置示例](examples/opencode.jsonc)，将其中所有 `D:/path/to/CST_MCP` 替换为实际仓库的绝对路径。
3. 将示例合并到 `%USERPROFILE%\.config\opencode\opencode.jsonc`，使本机各项目均可使用；只想在一个项目使用时，合并到该项目根目录的 `opencode.jsonc`。保留已有模型、权限、其他 MCP 和 Skills 路径；已有 `cst-runtime` 条目直接更新，不另起名称重复注册。
4. 在 OpenCode 中重新连接 `cst-runtime`；若当前会话未重新读取配置，重启 OpenCode 后打开新会话。

OpenCode 的安装目录只用于启动应用，不是 MCP 配置目录。例如应用可以安装在 `D:\Program Files (x86)\OpenCode`，而用户配置仍在上面的用户目录。命令数组中的 `-File` 指向 **CST_MCP 仓库**的 `scripts/start-mcp.ps1`；带空格的路径保持为一个数组元素，不要额外加入引号字符。

启动脚本通过自身位置确定源码目录，并使用 `CST_MCP_HOME`、`CST_MCP_CONFIG` 和 `CST_WORKER_PYTHON` 选择固定环境。因此从其他工程目录启动 OpenCode 也能连接同一服务。脚本直接运行 `.envs/mcp/Scripts/python.exe -m mcp_server`，不在连接时执行 `uv sync` 或更新依赖，避免其他客户端占用环境中的程序文件而导致启动失败。`uv` 仅用于安装和更新环境；无需把 Runtime 安装到 OpenCode 目录，也无需合并 Python 3.12 与 Python 3.9 环境。

### Skills 与长任务超时

示例的 `skills.paths` 直接指向仓库的 `skills` 目录，OpenCode 按需加载四个完整 Skill 及其参考资料、脚本。这一字段由 [1.18.23 配置定义](https://github.com/anomalyco/opencode/blob/v1.18.23/packages/core/src/v1/config/config.ts)支持。已配置这个路径时，不要再复制同名技能。其他安装方式见 [OpenCode Skills 文档](https://opencode.ai/docs/skills/)。

示例的 `timeout: 3600000` 单位为毫秒，即客户端最多等待一小时。官方 MCP 页面主要以获取工具列表解释该字段；[1.18.23 的 MCP 实现](https://github.com/anomalyco/opencode/blob/v1.18.23/packages/opencode/src/mcp/index.ts)还将同一值作为工具请求超时，并优先于 `experimental.mcp_timeout`。因此不能仅把它设置为很短的连接超时，否则长时间求解可能先被客户端中断。该版本共用这一数值，启动异常时也可能等待较久。

服务端仍按 `.cst_config.json` 的 `runtime.request_timeout`、`session_timeout` 和 `simulation_timeout` 管理每类请求；默认仿真传输上限为 1200 秒，长任务分界为 600 秒。客户端的一小时等待上限不改变服务端分界，也不承诺仿真在一小时内完成。如果提高服务端预算，应让客户端等待时间继续留有余量。

收到 `terminal=true` 或 `await_user_decision=true` 时，按现有 `cst-mcp` Skill 停止本回合的后续 CST 调用，报告求解器是否仍在运行并等待用户决定恢复。`long_run_relinquish` 不等于仿真失败，不应自动重新启动求解。

[OpenCode V2 文档](https://opencode.ai/v2/docs/mcp-servers)采用 `mcp.servers`、`disabled` 和分项超时对象；这些字段不属于本节的 1.18.23 配置示例。升级后应按实际客户端版本重新核对，不能混用两种配置结构。

### 连接验证

- 在 OpenCode 的 MCP 列表中确认 `cst-runtime` 已连接；另装了 CLI 时，可在目标项目目录执行 `opencode mcp list`。桌面应用的 `OpenCode.exe` 不等同于独立 CLI。
- 确认工具列表成功加载；首次接入时调用只读的 `health-check`，参数为 `{"workspace": ""}`。工具数量以当前 Registry 为准；不要把协议请求 `tools/list` 当成名为 `list-tools` 的业务工具。
- 确认能发现 `cst-mcp`、`cst-metasurface-design`、`cst-runtime-cli` 和 `cst-runtime-optimization`，且读取位置来自本仓库。

以上只证明配置、工具连接与技能发现。真实 CST 建模、求解和结果导出，以及具体模型能否正确完成工作流，需要单独验收；配置接入本身不要求启动 CST。普通成功返回仍按现有规则信任，不增加重复的 CST 执行前后检查。

## 其他 MCP 客户端与独立 Skills

OpenCode 等不支持 OpenAI 插件分发的平台，可以继续使用仓库顶层 `skills/` 作为规范源文件。必须复制或链接完整 Skill 文件夹，包括 `references/` 和 `scripts/`，不能只复制 `SKILL.md`。

独立安装 Skill 不等于部署 Runtime 或连接 MCP。首次使用本文的环境创建和启动命令时，需要另外取得完整 CST_MCP 仓库，并在该仓库根目录运行；`scripts/setup-environments.ps1`、`scripts/start-mcp.ps1` 和 MCP 服务源码不包含在单个 Skill 文件夹中。已有部署可复用其环境和连接，`CST_MCP_HOME` 指向环境与默认配置所在目录。

采用 `mcpServers` / `command` / `args` 格式的客户端可参考下面的启动配置；具体字段以该客户端文档为准。这不是 OpenCode 配置，OpenCode 请使用上一节的专用示例。

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
