param(
    [string]$TaskName = "tg-kb-bot",
    [string]$HealthcheckTaskName = "tg-kb-bot-healthcheck",
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$PwshExe = "C:\Program Files\PowerShell\7\pwsh.exe",
    [int]$HealthcheckIntervalMinutes = 5
)

$ErrorActionPreference = "Stop"

$startScript = Join-Path $RepoRoot "scripts\start_bot_local.ps1"
$watchdogScript = Join-Path $RepoRoot "scripts\runtime_watchdog_restart.ps1"
if (-not (Test-Path $startScript)) {
    throw "Start script not found: $startScript"
}
if (-not (Test-Path $watchdogScript)) {
    throw "Watchdog script not found: $watchdogScript"
}

if (-not (Test-Path $PwshExe)) {
    throw "PowerShell executable not found: $PwshExe"
}

if ($HealthcheckIntervalMinutes -lt 1) {
    throw "HealthcheckIntervalMinutes must be >= 1."
}

$taskCommand = "`"$PwshExe`" -NoProfile -ExecutionPolicy Bypass -File `"$startScript`""
$watchdogCommand = "`"$PwshExe`" -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$watchdogScript`" -TaskName `"$TaskName`" -RepoRoot `"$RepoRoot`""

function Test-TaskExists {
    param(
        [string]$Name
    )

    schtasks /Query /TN $Name | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Get-TaskVerbose {
    param(
        [string]$Name
    )

    return schtasks /Query /TN $Name /V /FO LIST 2>$null
}

$mainTaskExistsBefore = Test-TaskExists -Name $TaskName

schtasks /Create `
    /TN $TaskName `
    /SC ONLOGON `
    /TR $taskCommand `
    /RL LIMITED `
    /F | Out-Null
$mainCreateExit = $LASTEXITCODE

if ($mainCreateExit -ne 0) {
    if (-not $mainTaskExistsBefore) {
        throw "Failed to create task '$TaskName' (exit code $mainCreateExit)."
    }

    $mainInfo = (Get-TaskVerbose -Name $TaskName) -join "`n"
    if ($mainInfo -match [Regex]::Escape($startScript)) {
        Write-Warning "Task '$TaskName' already exists and could not be overwritten (exit code $mainCreateExit). Existing command points to start script; keeping as is."
    } else {
        throw "Task '$TaskName' exists but could not be updated (exit code $mainCreateExit), and current command does not match expected '$startScript'."
    }
}

schtasks /Query /TN $TaskName | Out-Null
$mainQueryExit = $LASTEXITCODE
if ($mainQueryExit -ne 0) {
    throw "Task '$TaskName' could not be queried after configuration (exit code $mainQueryExit). Check local permissions."
}

$healthTaskExistsBefore = Test-TaskExists -Name $HealthcheckTaskName

schtasks /Create `
    /TN $HealthcheckTaskName `
    /SC MINUTE `
    /MO $HealthcheckIntervalMinutes `
    /TR $watchdogCommand `
    /RL LIMITED `
    /F | Out-Null
$healthCreateExit = $LASTEXITCODE

if ($healthCreateExit -ne 0) {
    if (-not $healthTaskExistsBefore) {
        throw "Failed to create task '$HealthcheckTaskName' (exit code $healthCreateExit)."
    }

    $healthInfo = (Get-TaskVerbose -Name $HealthcheckTaskName) -join "`n"
    if ($healthInfo -match [Regex]::Escape("runtime_watchdog_restart.ps1")) {
        Write-Warning "Task '$HealthcheckTaskName' already exists and could not be overwritten (exit code $healthCreateExit). Existing command points to watchdog script; keeping as is."
    } else {
        throw "Task '$HealthcheckTaskName' exists but could not be updated (exit code $healthCreateExit), and current command does not match expected watchdog script."
    }
}

schtasks /Query /TN $HealthcheckTaskName | Out-Null
$healthQueryExit = $LASTEXITCODE
if ($healthQueryExit -ne 0) {
    throw "Task '$HealthcheckTaskName' could not be queried after configuration (exit code $healthQueryExit). Check local permissions."
}

Write-Host "Task '$TaskName' created/updated."
Write-Host "Task '$HealthcheckTaskName' created/updated."
Write-Host "Query checks passed."
schtasks /Query /TN $TaskName
schtasks /Query /TN $HealthcheckTaskName
