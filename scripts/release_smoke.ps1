param(
    [switch]$SkipTests,
    [ValidateSet("docker", "external")]
    [string]$DatabaseMode = "docker"
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Host "[release-smoke] $Name..."
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "[release-smoke] Step failed: $Name (exit code $LASTEXITCODE)"
    }
}

if ($DatabaseMode -eq "docker") {
    Invoke-Step "Starting PostgreSQL container" { docker compose up -d postgres }
}
else {
    Write-Host "[release-smoke] Using external/local PostgreSQL from DATABASE_URL (.env). Docker start is skipped."
}

Invoke-Step "Running migrations" { alembic upgrade head }

if (-not $SkipTests) {
    $env:SSLKEYLOGFILE = ""
    Invoke-Step "Running pytest" { python -m pytest -q }
}

Write-Host "[release-smoke] Completed successfully."
