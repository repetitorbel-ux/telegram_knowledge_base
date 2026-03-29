param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$LogDir = "logs",
    [int]$MaxLogAgeMinutes = 30
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

try {
    $botProcesses = Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match "^python(\.exe)?$" -and
            $_.CommandLine -match "kb_bot\.main"
        }
}
catch {
    # Fallback for restricted environments where CIM access is denied.
    $botProcesses = Get-Process -Name python,python3 -ErrorAction SilentlyContinue
}

if (-not $botProcesses) {
    Write-Host "RUNTIME_CHECK: FAIL (bot process not found)"
    exit 1
}

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
if ($age -gt $MaxLogAgeMinutes) {
    Write-Host "RUNTIME_CHECK: FAIL (latest log is stale: $([int]$age) min)"
    exit 1
}

Write-Host "RUNTIME_CHECK: PASS"
Write-Host "Process count: $($botProcesses.Count)"
Write-Host "Latest log: $($latestLog.FullName)"
Write-Host "Latest log age (min): $([int]$age)"
