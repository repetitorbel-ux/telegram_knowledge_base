# Deploy Runbook

This runbook defines the practical release flow for `telegram-kb-bot`.

## Preconditions

- `main` branch is up to date locally.
- `.env` exists and contains local values (`.env.example` or `env.production.example` as template).
- Python 3.12+ and project dependencies are available.
- PostgreSQL from `DATABASE_URL` is reachable.
  - Docker mode: Docker Desktop/Engine + Compose installed.
  - No-Docker mode: local/remote PostgreSQL is running and accessible.

## Release Command (Smoke Flow)

Use one command from repo root:

```powershell
pwsh ./scripts/release_smoke.ps1
```

No-Docker DB mode:

```powershell
pwsh ./scripts/release_smoke.ps1 -DatabaseMode external
```

This command performs:

1. starts PostgreSQL container (`docker compose up -d postgres`) in Docker mode only
2. runs DB migrations (`alembic upgrade head`)
3. runs test smoke (`python -m pytest -q`)

In `-DatabaseMode external`, Docker step is skipped and command uses DB from `DATABASE_URL`.

## Bot Restart

After successful smoke:

1. restart bot process (`python -m kb_bot.main`) with your local run method
2. run Telegram smoke checks:
   - `/start`
   - `/stats`
   - `/list limit=5`

## Webhook Smoke (P2-006 mode)

Use this section only when `TELEGRAM_MODE=webhook`.

Preconditions:

- bot process is running in webhook mode
- `TELEGRAM_BOT_TOKEN` is available in environment or passed explicitly
- `TELEGRAM_WEBHOOK_BASE_URL` points to a public HTTPS host

Command:

```powershell
pwsh ./scripts/webhook_smoke.ps1 -WebhookBaseUrl "https://<public-host>" -WebhookPath "/telegram/webhook"
```

Expected PASS criteria:

1. script prints `PASS: webhook URL is active in Telegram.`
2. reported `info.url` equals `<WebhookBaseUrl><WebhookPath>`
3. `last_error_message` is empty (or absent)

Optional rollback-to-polling verification:

```powershell
pwsh ./scripts/webhook_smoke.ps1 -WebhookBaseUrl "https://<public-host>" -WebhookPath "/telegram/webhook" -RollbackToPolling
```

This performs `deleteWebhook` and confirms that `getWebhookInfo.result.url` is empty.

Optional Linux production profile for runtime supervision/logging/alerts is documented in:

- `docs/RUNTIME_RELIABILITY_RUNBOOK.md`

## Rollback

### Application rollback

1. checkout previous known-good release commit/tag
2. reinstall dependencies if required
3. rerun migration only if rollback plan allows it
4. restart bot process
5. if rollback target uses polling, run Telegram API cleanup:
   - `pwsh ./scripts/webhook_smoke.ps1 -WebhookBaseUrl "https://<public-host>" -RollbackToPolling`

### Data rollback

Follow `docs/RESTORE_RUNBOOK.md` and perform restore only with approved token flow.

## Evidence to Attach

- release timestamp
- operator name
- output of `pwsh ./scripts/release_smoke.ps1`
- confirmation of Telegram smoke commands
- webhook smoke output (for webhook mode releases)

## Troubleshooting

- `failed to connect to the docker API at npipe:////./pipe/docker_engine`:
  - start Docker Desktop / Docker Engine on host
  - verify current user has access to Docker daemon
- `Import failed: ... Connect call failed ('127.0.0.1', <port>)`:
  - DB host/port from `DATABASE_URL` is unreachable
  - check DB service status and port mapping
  - for no-Docker mode, verify local PostgreSQL service and credentials
- `Access is denied` on Docker config/service:
  - run with proper host permissions (outside restricted sandbox session)
- `ConnectionError: Unexpected peer connection` during `alembic upgrade head`:
  - this indicates event loop restrictions of current runner/session
  - rerun release smoke directly in host terminal/session with full OS networking/event-loop support
