param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$PythonExe = "python",
    [string]$LogDir = "logs",
    [int]$RestartDelaySec = 20,
    [int]$MaxRestartAttempts = 0
)

$ErrorActionPreference = "Stop"

Set-Location $RepoRoot

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $LogDir "bot_$stamp.log"

# Prevent stale proxy env vars from breaking Telegram API connectivity.
foreach ($name in @("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")) {
    Remove-Item "Env:$name" -ErrorAction SilentlyContinue
}
$env:NO_PROXY = "*"

Write-Host "Starting bot from $RepoRoot"
Write-Host "Log file: $logFile"

function Get-TelegramApiAddresses {
    try {
        return [System.Net.Dns]::GetHostAddresses("api.telegram.org")
    } catch {
        return @()
    }
}

$attempt = 0
while ($true) {
    $attempt += 1
    $ts = (Get-Date).ToString("s")
    Add-Content -LiteralPath $logFile -Value "[$ts] launcher attempt #$attempt"

    $addresses = Get-TelegramApiAddresses
    $badLoopback = $false
    if (-not $addresses -or $addresses.Count -eq 0) {
        $badLoopback = $true
        Add-Content -LiteralPath $logFile -Value "[$ts] DNS check failed: api.telegram.org unresolved"
    } else {
        $resolved = ($addresses | ForEach-Object { $_.IPAddressToString }) -join ", "
        Add-Content -LiteralPath $logFile -Value "[$ts] DNS api.telegram.org -> $resolved"
        if ($addresses | Where-Object { $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and $_.IPAddressToString -like '127.*' }) {
            $badLoopback = $true
            Add-Content -LiteralPath $logFile -Value "[$ts] DNS check failed: loopback address detected for api.telegram.org"
        }
    }

    if ($badLoopback) {
        if ($MaxRestartAttempts -gt 0 -and $attempt -ge $MaxRestartAttempts) {
            Add-Content -LiteralPath $logFile -Value "[$ts] Max restart attempts reached during DNS precheck. Exiting launcher."
            exit 1
        }
        Add-Content -LiteralPath $logFile -Value "[$ts] Sleeping $RestartDelaySec sec before retry."
        Start-Sleep -Seconds $RestartDelaySec
        continue
    }

    & $PythonExe -m kb_bot.main *>> $logFile
    $exitCode = $LASTEXITCODE
    $tsExit = (Get-Date).ToString("s")
    Add-Content -LiteralPath $logFile -Value "[$tsExit] Bot process exited with code $exitCode"

    if ($MaxRestartAttempts -gt 0 -and $attempt -ge $MaxRestartAttempts) {
        Add-Content -LiteralPath $logFile -Value "[$tsExit] Max restart attempts reached. Exiting launcher."
        exit $exitCode
    }

    Add-Content -LiteralPath $logFile -Value "[$tsExit] Restarting in $RestartDelaySec sec."
    Start-Sleep -Seconds $RestartDelaySec
}
