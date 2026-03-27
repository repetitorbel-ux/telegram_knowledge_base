param(
    [Parameter(Mandatory = $false)]
    [string]$EnvFilePath = "./.env",
    [Parameter(Mandatory = $false)]
    [ValidateSet("local", "production")]
    [string]$Mode = "local"
)

$ErrorActionPreference = "Stop"

function Add-Failure {
    param([string]$Message)
    Write-Host "[FAIL] $Message"
    $script:HasFailures = $true
}

function Add-Pass {
    param([string]$Message)
    Write-Host "[PASS] $Message"
}

function Read-EnvFile {
    param([string]$Path)

    $map = @{}
    foreach ($rawLine in Get-Content -Path $Path) {
        $line = $rawLine.Trim()
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line.StartsWith("#")) { continue }
        if (-not $line.Contains("=")) { continue }

        $parts = $line.Split("=", 2)
        $key = $parts[0].Trim()
        $value = $parts[1].Trim()
        if (-not [string]::IsNullOrWhiteSpace($key)) {
            $map[$key] = $value
        }
    }
    return $map
}

$HasFailures = $false
Write-Host "SECTION2_ENV_CHECK: START"
Write-Host "Env file: $EnvFilePath"
Write-Host "Mode: $Mode"

if (-not (Test-Path -LiteralPath $EnvFilePath)) {
    Add-Failure "Env file not found"
    Write-Host "SECTION2_ENV_CHECK: FAIL"
    exit 1
}
Add-Pass "Env file exists"

$envMap = Read-EnvFile -Path $EnvFilePath

$required = @(
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_ALLOWED_USER_ID",
    "DATABASE_URL",
    "BACKUP_DIR",
    "PG_DUMP_BIN",
    "PG_RESTORE_BIN"
)

foreach ($key in $required) {
    if (-not $envMap.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($envMap[$key])) {
        Add-Failure "$key is missing or empty"
    } else {
        Add-Pass "$key is present"
    }
}

if ($envMap.ContainsKey("TELEGRAM_BOT_TOKEN")) {
    $token = $envMap["TELEGRAM_BOT_TOKEN"]
    if ($token -match "__SET_IN_SECRET_MANAGER__|^changeme$|^your_token_here$|^replace_me$|^replace-with-real-token$") {
        Add-Failure "TELEGRAM_BOT_TOKEN still has placeholder value"
    } else {
        Add-Pass "TELEGRAM_BOT_TOKEN is not a placeholder"
    }
}

if ($envMap.ContainsKey("TELEGRAM_ALLOWED_USER_ID")) {
    $allowedUser = $envMap["TELEGRAM_ALLOWED_USER_ID"]
    if ($allowedUser -notmatch "^\d+$") {
        Add-Failure "TELEGRAM_ALLOWED_USER_ID must be numeric"
    } else {
        Add-Pass "TELEGRAM_ALLOWED_USER_ID has numeric format"
    }
}

if ($envMap.ContainsKey("DATABASE_URL")) {
    $dbUrl = $envMap["DATABASE_URL"]
    if ($dbUrl -match "__DB_USER__|__DB_PASSWORD__|__DB_HOST__|__DB_NAME__") {
        Add-Failure "DATABASE_URL still has placeholder fragments"
    } elseif ($dbUrl -match "/test($|[/?])|_test($|[/?])") {
        Add-Failure "DATABASE_URL looks test-like"
    } elseif ($Mode -eq "production" -and $dbUrl -match "localhost|127\.0\.0\.1") {
        Add-Failure "DATABASE_URL looks local-like for production mode"
    } else {
        Add-Pass "DATABASE_URL format is valid for selected mode"
    }
}

if ($envMap.ContainsKey("BACKUP_DIR")) {
    $backupDir = $envMap["BACKUP_DIR"]
    if (-not (Test-Path -LiteralPath $backupDir)) {
        Add-Failure "BACKUP_DIR path does not exist: $backupDir"
    } else {
        Add-Pass "BACKUP_DIR exists"
    }
}

if ($envMap.ContainsKey("PG_DUMP_BIN")) {
    $dumpBin = $envMap["PG_DUMP_BIN"]
    if (-not (Get-Command $dumpBin -ErrorAction SilentlyContinue)) {
        Add-Failure "PG_DUMP_BIN is not available in PATH: $dumpBin"
    } else {
        Add-Pass "PG_DUMP_BIN is available"
    }
}

if ($envMap.ContainsKey("PG_RESTORE_BIN")) {
    $restoreBin = $envMap["PG_RESTORE_BIN"]
    if (-not (Get-Command $restoreBin -ErrorAction SilentlyContinue)) {
        Add-Failure "PG_RESTORE_BIN is not available in PATH: $restoreBin"
    } else {
        Add-Pass "PG_RESTORE_BIN is available"
    }
}

if ($IsLinux -or $IsMacOS) {
    try {
        $item = Get-Item -LiteralPath $EnvFilePath
        if ($item.UnixFileMode -eq "-rw-------") {
            Add-Pass "Env file permissions are 600 ($($item.UnixFileMode))"
        } else {
            Add-Failure "Env file permissions should be 600, got $($item.UnixFileMode)"
        }
    } catch {
        Write-Host "[INFO] Could not evaluate Unix file mode in this environment."
    }
} else {
    Write-Host "[INFO] Unix permission check skipped on non-Unix platform."
}

if ($HasFailures) {
    Write-Host "SECTION2_ENV_CHECK: FAIL"
    exit 1
}

Write-Host "SECTION2_ENV_CHECK: PASS"
exit 0
