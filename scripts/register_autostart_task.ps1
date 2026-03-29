param(
    [string]$TaskName = "tg-kb-bot",
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$PwshExe = "C:\Program Files\PowerShell\7\pwsh.exe"
)

$ErrorActionPreference = "Stop"

$startScript = Join-Path $RepoRoot "scripts\start_bot_local.ps1"
if (-not (Test-Path $startScript)) {
    throw "Start script not found: $startScript"
}

if (-not (Test-Path $PwshExe)) {
    throw "PowerShell executable not found: $PwshExe"
}

$taskCommand = "`"$PwshExe`" -NoProfile -ExecutionPolicy Bypass -File `"$startScript`""

schtasks /Create `
    /TN $TaskName `
    /SC ONLOGON `
    /TR $taskCommand `
    /RL LIMITED `
    /F | Out-Null
$createExit = $LASTEXITCODE

if ($createExit -ne 0) {
    throw "Failed to create/update task '$TaskName' (exit code $createExit)."
}

schtasks /Query /TN $TaskName | Out-Null
$queryExit = $LASTEXITCODE

if ($queryExit -ne 0) {
    throw "Task '$TaskName' could not be queried after creation (exit code $queryExit). Check local permissions."
}

Write-Host "Task '$TaskName' created/updated and query check passed."
schtasks /Query /TN $TaskName
