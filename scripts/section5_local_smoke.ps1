param(
    [Parameter(Mandatory = $false)]
    [string]$PytestArgs = "-q"
)

$ErrorActionPreference = "Stop"

$tests = @(
    "tests/test_start_and_add_flow.py",
    "tests/test_search_parsing.py",
    "tests/test_list_parsing.py",
    "tests/test_entry_parsing.py",
    "tests/test_status_parsing.py",
    "tests/test_status_machine.py",
    "tests/test_topic_parsing.py",
    "tests/test_collection_parsing.py",
    "tests/test_import_parsing.py",
    "tests/test_export_parsing.py",
    "tests/test_stats_service.py"
)

Write-Host "SECTION5_LOCAL_SMOKE: START"
Write-Host "Selected tests:"
foreach ($test in $tests) {
    Write-Host " - $test"
}

$cmd = @("python", "-m", "pytest") + $tests + @($PytestArgs)
Write-Host "Running: $($cmd -join ' ')"

if ($env:SSLKEYLOGFILE) {
    Write-Host "Clearing SSLKEYLOGFILE for test run (avoids permission issues in restricted environments)."
    Remove-Item Env:SSLKEYLOGFILE -ErrorAction SilentlyContinue
}

& python -m pytest @tests $PytestArgs
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Host "SECTION5_LOCAL_SMOKE: FAIL"
    exit $exitCode
}

Write-Host "SECTION5_LOCAL_SMOKE: PASS"
exit 0
