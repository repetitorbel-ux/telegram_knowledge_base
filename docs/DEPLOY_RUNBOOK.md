# Deploy Runbook

This runbook defines the practical release flow for `telegram-kb-bot`.

## Preconditions

- Target host has Docker Engine and Docker Compose installed.
- `main` branch is up to date on target host.
- `.env` exists and contains production values (from `env.production.example` template).
- Python 3.12+ and project dependencies are available.

## Release Command (Smoke Flow)

Use one command from repo root:

```powershell
pwsh ./scripts/release_smoke.ps1
```

This command performs:

1. starts PostgreSQL container (`docker compose up -d postgres`)
2. runs DB migrations (`alembic upgrade head`)
3. runs test smoke (`python -m pytest -q`)

If Docker is not running or inaccessible, the command fails fast with non-zero exit code.

## Bot Restart

After successful smoke:

1. restart bot process (`python -m kb_bot.main`) using your process supervisor
2. run Telegram smoke checks:
   - `/start`
   - `/stats`
   - `/list limit=5`

Production baseline for runtime supervision/logging/alerts is documented in:

- `docs/RUNTIME_RELIABILITY_RUNBOOK.md`

## Rollback

### Application rollback

1. checkout previous known-good release commit/tag
2. reinstall dependencies if required
3. rerun migration only if rollback plan allows it
4. restart bot process

### Data rollback

Follow `docs/RESTORE_RUNBOOK.md` and perform restore only with approved token flow.

## Evidence to Attach

- release timestamp
- operator name
- output of `pwsh ./scripts/release_smoke.ps1`
- confirmation of Telegram smoke commands

## Troubleshooting

- `failed to connect to the docker API at npipe:////./pipe/docker_engine`:
  - start Docker Desktop / Docker Engine on host
  - verify current user has access to Docker daemon
- `Access is denied` on Docker config/service:
  - run with proper host permissions (outside restricted sandbox session)
- `ConnectionError: Unexpected peer connection` during `alembic upgrade head`:
  - this indicates event loop restrictions of current runner/session
  - rerun release smoke directly in host terminal/session with full OS networking/event-loop support
