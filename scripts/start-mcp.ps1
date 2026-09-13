[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$sourceRoot = Split-Path -Parent $PSScriptRoot
$environmentRoot = $env:CST_MCP_HOME
if ([string]::IsNullOrWhiteSpace($environmentRoot)) {
    $environmentRoot = $sourceRoot
}
$environmentRoot = [System.IO.Path]::GetFullPath($environmentRoot)

$mcpPython = Join-Path $environmentRoot ".envs\mcp\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $mcpPython -PathType Leaf)) {
    throw "找不到 MCP Python 环境：$mcpPython。请先运行 scripts/setup-environments.ps1。"
}

if ([string]::IsNullOrWhiteSpace($env:CST_MCP_CONFIG)) {
    $localConfig = Join-Path $environmentRoot ".cst_config.json"
    if (Test-Path -LiteralPath $localConfig -PathType Leaf) {
        $env:CST_MCP_CONFIG = $localConfig
    }
}
if ([string]::IsNullOrWhiteSpace($env:CST_WORKER_PYTHON)) {
    $localWorker = Join-Path $environmentRoot ".envs\cst39\Scripts\python.exe"
    if (Test-Path -LiteralPath $localWorker -PathType Leaf) {
        $env:CST_WORKER_PYTHON = $localWorker
    }
}

# 启动时只使用已部署环境，避免多客户端连接时更新正在使用的可执行文件。
# 从脚本所属源码目录运行模块，使仓库和插件分别加载自身的 MCP 源码。
Push-Location -LiteralPath $sourceRoot
try {
    & $mcpPython -m mcp_server
    $mcpExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $mcpExitCode
