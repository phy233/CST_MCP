[CmdletBinding()]
param(
    [string]$EnvironmentRoot,
    [switch]$IncludeDev
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($EnvironmentRoot)) {
    $EnvironmentRoot = $projectRoot
}
$EnvironmentRoot = [System.IO.Path]::GetFullPath($EnvironmentRoot)

$savedProjectEnvironment = $env:UV_PROJECT_ENVIRONMENT
$savedPythonInstallDir = $env:UV_PYTHON_INSTALL_DIR
$savedCacheDir = $env:UV_CACHE_DIR

try {
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $EnvironmentRoot ".python"
    $env:UV_CACHE_DIR = Join-Path $EnvironmentRoot ".uv-cache"

    $env:UV_PROJECT_ENVIRONMENT = Join-Path $EnvironmentRoot ".envs\mcp"
    $mcpArgs = @("sync", "--project", $projectRoot, "--python", "3.12")
    if ($IncludeDev) {
        $mcpArgs += @("--extra", "dev")
    }
    & uv @mcpArgs
    if ($LASTEXITCODE -ne 0) {
        throw "uv sync failed for the MCP Python 3.12 environment: $LASTEXITCODE"
    }

    $runtimeProject = Join-Path $projectRoot "skills\cst-runtime-cli\scripts"
    $env:UV_PROJECT_ENVIRONMENT = Join-Path $EnvironmentRoot ".envs\cst39"
    $runtimeArgs = @(
        "sync", "--project", $runtimeProject, "--python", "3.9",
        "--extra", "sweep", "--extra", "optimization", "--extra", "report"
    )
    if ($IncludeDev) {
        $runtimeArgs += @("--extra", "dev")
    }
    & uv @runtimeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "uv sync failed for the CST Worker Python 3.9 environment: $LASTEXITCODE"
    }

    Write-Host "MCP environment: $(Join-Path $EnvironmentRoot '.envs\mcp')"
    Write-Host "Worker environment: $(Join-Path $EnvironmentRoot '.envs\cst39')"
    Write-Host "uv-managed Python: $(Join-Path $EnvironmentRoot '.python')"
}
finally {
    $env:UV_PROJECT_ENVIRONMENT = $savedProjectEnvironment
    $env:UV_PYTHON_INSTALL_DIR = $savedPythonInstallDir
    $env:UV_CACHE_DIR = $savedCacheDir
}
