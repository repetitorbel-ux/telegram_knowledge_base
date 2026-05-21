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

function Test-TelegramApiTcpConnect {
    param(
        [int]$TimeoutMs = 5000
    )

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $async = $client.BeginConnect("api.telegram.org", 443, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne($TimeoutMs)) {
            return $false
        }

        $client.EndConnect($async)
        return $true
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Get-EnvFileValue {
    param(
        [string]$Path,
        [string]$Name
    )

    if (-not (Test-Path $Path)) {
        return $null
    }

    $line = Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue |
        Where-Object { $_ -match "^\s*$([regex]::Escape($Name))\s*=" } |
        Select-Object -Last 1

    if (-not $line) {
        return $null
    }

    return ($line -replace "^\s*$([regex]::Escape($Name))\s*=\s*", "").Trim().Trim('"').Trim("'")
}

function Get-DatabaseEndpoint {
    param(
        [string]$DatabaseUrl
    )

    if (-not $DatabaseUrl) {
        return $null
    }

    $withoutScheme = $DatabaseUrl -replace "^[^:]+://", ""
    $authority = ($withoutScheme -split "/", 2)[0]
    if ($authority -match "@") {
        $authority = ($authority -split "@")[-1]
    }

    $hostName = $authority
    $port = 5432
    if ($authority -match "^(?<host>.+):(?<port>\d+)$") {
        $hostName = $Matches["host"]
        $port = [int]$Matches["port"]
    }

    [pscustomobject]@{
        Host = $hostName
        Port = $port
    }
}

function Test-TcpConnect {
    param(
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutMs = 3000
    )

    $client = $null
    try {
        $client = [System.Net.Sockets.TcpClient]::new()
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne($TimeoutMs)) {
            return $false
        }

        $client.EndConnect($async)
        return $true
    } catch {
        return $false
    } finally {
        if ($client) {
            $client.Dispose()
        }
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
            if (Test-TelegramApiTcpConnect) {
                Add-Content -LiteralPath $logFile -Value "[$ts] Loopback-like DNS address accepted because TCP connect to api.telegram.org:443 succeeded (likely proxified resolution)."
            } else {
                $badLoopback = $true
                Add-Content -LiteralPath $logFile -Value "[$ts] DNS check failed: loopback address detected for api.telegram.org and TCP connect probe failed"
            }
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

    $databaseUrl = Get-EnvFileValue -Path (Join-Path $RepoRoot ".env") -Name "DATABASE_URL"
    $databaseEndpoint = Get-DatabaseEndpoint -DatabaseUrl $databaseUrl
    if (-not $databaseEndpoint) {
        Add-Content -LiteralPath $logFile -Value "[$ts] DB check failed: DATABASE_URL not found or invalid"
        exit 1
    }

    if (-not (Test-TcpConnect -HostName $databaseEndpoint.Host -Port $databaseEndpoint.Port)) {
        Add-Content -LiteralPath $logFile -Value "[$ts] DB check failed: PostgreSQL is unreachable at $($databaseEndpoint.Host):$($databaseEndpoint.Port)"
        if ($MaxRestartAttempts -gt 0 -and $attempt -ge $MaxRestartAttempts) {
            Add-Content -LiteralPath $logFile -Value "[$ts] Max restart attempts reached during DB precheck. Exiting launcher."
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
