# Deployment Target

This document defines the production deployment target for `telegram-kb-bot`.

## Selected Target

- Platform: VPS/VM (Linux) with Docker Engine + Docker Compose
- Runtime model: one bot process + one PostgreSQL container
- Network mode: internal host networking with Telegram API outbound access

## Service Topology

- `kb-bot` (app container/process)
  - starts with `python -m kb_bot.main`
  - reads config from environment variables
- `postgres` (stateful container)
  - PostgreSQL 16
  - persistent volume for DB data
  - local compose mapping uses host port `55433` -> container `5432`

## Required Environment Variables

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_ID`
- `DATABASE_URL` (must point to production DB)
- `BACKUP_DIR`
- `PG_DUMP_BIN`
- `PG_RESTORE_BIN`

Production-safe template file:

- `env.production.example` (placeholders only, no secrets)

## Deployment Flow (MVP)

1. Pull latest `main` on target host.
2. Ensure Docker is running.
3. Copy `env.production.example` to `.env` and set real secret values on host.
4. Start/update PostgreSQL service (`docker compose up -d postgres`).
5. Install/update app dependencies.
6. Run migration: `alembic upgrade head`.
7. Start/restart bot process.
8. Run post-deploy smoke: `/start`, `/stats`, `/list limit=5`.

## Rollback Baseline

- App rollback:
  - checkout previous known-good commit/release
  - reinstall dependencies if needed
  - restart bot process
- Data rollback:
  - use restore flow from `docs/RESTORE_RUNBOOK.md`
  - only after validation and approval

## Operational Notes

- Docker must be running for container-backed DB checks and restore drill.
- Keep `.env` and any secrets out of git.
- Use least-privilege DB credentials for production.
- Use `docs/DEPLOY_RUNBOOK.md` for release command and rollback routine.
