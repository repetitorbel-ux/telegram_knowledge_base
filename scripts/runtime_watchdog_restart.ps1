param(
    [string]$TaskName = "tg-kb-bot",
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$LogDir = "logs"
)

$ErrorActionPreference = "Stop"

Set-Location $RepoRoot

$logPath = Join-Path $RepoRoot $LogDir
if (-not (Test-Path $logPath)) {
    New-Item -ItemType Directory -Path $logPath | Out-Null
}

$watchdogLog = Join-Path $logPath "watchdog.log"

function Write-WatchdogLog {
    param(
        [string]$Message
    )

    $ts = (Get-Date).ToString("s")
    Add-Content -LiteralPath $watchdogLog -Value "[$ts] $Message"
}

$pythonProcesses = Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -match "^python(\.exe)?$" -and
        $_.CommandLine -match "kb_bot\.main"
    }

$launcherProcesses = Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -match "^pwsh(\.exe)?$" -and
        $_.CommandLine -match "start_bot_local\.ps1"
    }

$botProcesses = @($pythonProcesses) + @($launcherProcesses)
if ($botProcesses.Count -gt 0) {
    Write-WatchdogLog "bot is running (process count: $($botProcesses.Count)); no restart required"
    exit 0
}

Write-WatchdogLog "bot process not found; starting scheduled task '$TaskName'"
schtasks /Run /TN $TaskName | Out-Null
$runExit = $LASTEXITCODE

if ($runExit -ne 0) {
    Write-WatchdogLog "failed to start task '$TaskName' (exit code $runExit)"
    throw "Failed to start task '$TaskName' (exit code $runExit)."
}

Write-WatchdogLog "start signal sent to task '$TaskName'"
