# Runtime Reliability Runbook (Windows Local)

This runbook covers checklist Section 4 for local Windows usage without Docker.

## Scope

- startup stability checks
- autostart via Task Scheduler
- watchdog auto-restart when process is down
- persistent local log files
- minimum error visibility baseline

## Scripts

- `scripts/start_bot_local.ps1`
- `scripts/register_autostart_task.ps1`
- `scripts/runtime_healthcheck_local.ps1`
- `scripts/runtime_watchdog_restart.ps1`

## One-Time Setup

From repo root:

```powershell
pwsh ./scripts/register_autostart_task.ps1
```

This creates/updates task `tg-kb-bot` (trigger: `ONLOGON`) that runs:

- `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/start_bot_local.ps1`

And creates/updates task `tg-kb-bot-healthcheck` (trigger: every 5 minutes) that runs:

- `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/runtime_watchdog_restart.ps1 -TaskName tg-kb-bot`

## Manual Start (Current Session)

```powershell
pwsh ./scripts/start_bot_local.ps1
```

Behavior:

- starts bot via `python -m kb_bot.main`
- writes output to `logs/bot_<timestamp>.log`
- clears proxy env vars to avoid Telegram API routing issues

## Verify Autostart Task

```powershell
schtasks /Query /TN tg-kb-bot
schtasks /Query /TN tg-kb-bot-healthcheck
```

Optional immediate run:

```powershell
schtasks /Run /TN tg-kb-bot
```

Optional immediate watchdog run:

```powershell
pwsh ./scripts/runtime_watchdog_restart.ps1 -TaskName tg-kb-bot
```

## Runtime Health Check

```powershell
pwsh ./scripts/runtime_healthcheck_local.ps1
```

Expected: `RUNTIME_CHECK: PASS`.

## Logs (Persistent)

Local log folder:

- `logs/`

Quick view:

```powershell
Get-ChildItem logs | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,Length,LastWriteTime
Get-Content (Get-ChildItem logs -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName -Tail 50
```

## Minimum Error Notification Baseline (Local)

Baseline for local operation:

- startup failures are visible in terminal / Task Scheduler history
- runtime exceptions are written to `logs/bot_*.log`
- automatic watchdog check via `tg-kb-bot-healthcheck` task
- periodic manual check via `runtime_healthcheck_local.ps1`

## Evidence To Attach (Checklist Section 4)

- output of `schtasks /Query /TN tg-kb-bot`
- output of `schtasks /Query /TN tg-kb-bot-healthcheck`
- output of `pwsh ./scripts/runtime_healthcheck_local.ps1`
- sample lines from `logs/watchdog.log`
- sample lines from latest file in `logs/`
- Telegram smoke after restart:
  - `/start`
  - `/stats`
  - `/list limit=5`
