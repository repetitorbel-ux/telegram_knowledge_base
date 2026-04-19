param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$LogDir = "logs",
    [int]$MaxLogAgeMinutes = 30
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$logPath = Join-Path $RepoRoot $LogDir
if (-not (Test-Path $logPath)) {
    Write-Host "RUNTIME_CHECK: FAIL (log directory not found: $logPath)"
    exit 1
}

$latestLog = Get-ChildItem -Path $logPath -File -Filter "bot_*.log" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $latestLog) {
    Write-Host "RUNTIME_CHECK: FAIL (no bot log files found)"
    exit 1
}

$age = (New-TimeSpan -Start $latestLog.LastWriteTime -End (Get-Date)).TotalMinutes

$tailLines = Get-Content -LiteralPath $latestLog.FullName -Tail 50 -ErrorAction SilentlyContinue
$logHasPollingMarkers = $tailLines | Where-Object {
    $_ -match "Start polling" -or
    $_ -match "Run polling for bot" -or
    $_ -match "Update id=.*handled"
}
$logHasExitMarker = $tailLines | Where-Object {
    $_ -match "Bot process exited with code" -or
    $_ -match "Max restart attempts reached"
}

$processMode = "direct"

try {
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
}
catch {
    $botProcesses = @()
    $processMode = "log_fallback"
}

if (-not $botProcesses) {
    if ($age -gt $MaxLogAgeMinutes) {
        Write-Host "RUNTIME_CHECK: FAIL (latest log is stale: $([int]$age) min)"
        Write-Host "Latest log: $($latestLog.FullName)"
        exit 1
    }

    if ($logHasPollingMarkers -and -not $logHasExitMarker) {
        Write-Host "RUNTIME_CHECK: PASS"
        Write-Host "Process count: unavailable (using fresh polling log fallback)"
        Write-Host "Latest log: $($latestLog.FullName)"
        Write-Host "Latest log age (min): $([int]$age)"
        Write-Host "Detection mode: $processMode"
        exit 0
    }

    Write-Host "RUNTIME_CHECK: FAIL (bot process not found)"
    Write-Host "Latest log: $($latestLog.FullName)"
    Write-Host "Latest log age (min): $([int]$age)"
    exit 1
}

Write-Host "RUNTIME_CHECK: PASS"
Write-Host "Process count: $($botProcesses.Count)"
Write-Host "Latest log: $($latestLog.FullName)"
Write-Host "Latest log age (min): $([int]$age)"
Write-Host "Detection mode: $processMode"
