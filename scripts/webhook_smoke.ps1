param(
    [string]$BotToken = $env:TELEGRAM_BOT_TOKEN,
    [Parameter(Mandatory = $true)]
    [string]$WebhookBaseUrl,
    [string]$WebhookPath = "/telegram/webhook",
    [string]$SecretToken = $env:TELEGRAM_WEBHOOK_SECRET_TOKEN,
    [switch]$DropPendingUpdates,
    [switch]$RollbackToPolling
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($BotToken)) {
    throw "TELEGRAM_BOT_TOKEN is required (pass -BotToken or set env)."
}

if ([string]::IsNullOrWhiteSpace($WebhookBaseUrl)) {
    throw "Webhook base URL is required (for example: https://bot.example.com)."
}

$normalizedBase = $WebhookBaseUrl.TrimEnd("/")
if ([string]::IsNullOrWhiteSpace($WebhookPath)) {
    $WebhookPath = "/telegram/webhook"
}
$normalizedPath = if ($WebhookPath.StartsWith("/")) { $WebhookPath } else { "/$WebhookPath" }
$finalWebhookUrl = "$normalizedBase$normalizedPath"
$apiBase = "https://api.telegram.org/bot$BotToken"

Write-Host "[webhook-smoke] Registering webhook: $finalWebhookUrl"
$setPayload = @{
    url = $finalWebhookUrl
    drop_pending_updates = [bool]$DropPendingUpdates
}
if (-not [string]::IsNullOrWhiteSpace($SecretToken)) {
    $setPayload.secret_token = $SecretToken
}

$setResult = Invoke-RestMethod `
    -Method Post `
    -Uri "$apiBase/setWebhook" `
    -ContentType "application/json" `
    -Body ($setPayload | ConvertTo-Json -Compress)

if (-not $setResult.ok) {
    throw "[webhook-smoke] setWebhook failed: $($setResult.description)"
}

Write-Host "[webhook-smoke] Reading webhook info..."
$infoResult = Invoke-RestMethod -Method Post -Uri "$apiBase/getWebhookInfo"
if (-not $infoResult.ok) {
    throw "[webhook-smoke] getWebhookInfo failed: $($infoResult.description)"
}

$info = $infoResult.result
Write-Host ("[webhook-smoke] info.url={0}" -f $info.url)
Write-Host ("[webhook-smoke] info.pending_update_count={0}" -f $info.pending_update_count)
Write-Host ("[webhook-smoke] info.last_error_date={0}" -f $info.last_error_date)
Write-Host ("[webhook-smoke] info.last_error_message={0}" -f $info.last_error_message)

if ($info.url -ne $finalWebhookUrl) {
    throw "[webhook-smoke] URL mismatch. Expected: $finalWebhookUrl, got: $($info.url)"
}

Write-Host "[webhook-smoke] PASS: webhook URL is active in Telegram."

if ($RollbackToPolling) {
    Write-Host "[webhook-smoke] Rolling back to polling (deleteWebhook)..."
    $deleteResult = Invoke-RestMethod `
        -Method Post `
        -Uri "$apiBase/deleteWebhook" `
        -ContentType "application/json" `
        -Body (@{ drop_pending_updates = $false } | ConvertTo-Json -Compress)

    if (-not $deleteResult.ok) {
        throw "[webhook-smoke] deleteWebhook failed: $($deleteResult.description)"
    }

    $postDeleteInfo = Invoke-RestMethod -Method Post -Uri "$apiBase/getWebhookInfo"
    if (-not $postDeleteInfo.ok) {
        throw "[webhook-smoke] getWebhookInfo after delete failed: $($postDeleteInfo.description)"
    }
    if (-not [string]::IsNullOrWhiteSpace($postDeleteInfo.result.url)) {
        throw "[webhook-smoke] Rollback check failed: webhook URL is still set."
    }
    Write-Host "[webhook-smoke] PASS: webhook removed, polling can be used."
}

