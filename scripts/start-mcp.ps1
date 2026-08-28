[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$pluginRoot = Split-Path -Parent $PSScriptRoot
$environmentRoot = $env:CST_MCP_HOME
if ([string]::IsNullOrWhiteSpace($environmentRoot)) {
    $environmentRoot = $pluginRoot
}
$environmentRoot = [System.IO.Path]::GetFullPath($environmentRoot)

$env:UV_PROJECT_ENVIRONMENT = Join-Path $environmentRoot ".envs\mcp"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $environmentRoot ".python"
$env:UV_CACHE_DIR = Join-Path $environmentRoot ".uv-cache"

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

& uv run --project $pluginRoot --python 3.12 cst-mcp
exit $LASTEXITCODE
