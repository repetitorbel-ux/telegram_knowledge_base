# Deployment Target

This document defines the primary deployment target for `telegram-kb-bot`.

## Selected Target

- Primary platform: local developer machine (Windows) with Docker Desktop + PostgreSQL container
- Runtime model: one local bot process + one PostgreSQL container
- Network mode: local host networking with Telegram API outbound access
- Optional profile: Linux VPS/VM (documented but not required for local usage)

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
- `DATABASE_URL` (must point to local runtime DB for local mode)
- `BACKUP_DIR`
- `PG_DUMP_BIN`
- `PG_RESTORE_BIN`

Template files:

- `.env.example` (local baseline)
- `env.production.example` (optional production-style placeholders)

## Local Run Flow (MVP)

1. Pull latest `main` on local machine.
2. Ensure Docker is running.
3. Copy `.env.example` to `.env` (or `env.production.example` if preferred) and set real values.
4. Start/update PostgreSQL service (`docker compose up -d postgres`).
5. Install/update app dependencies.
6. Run migration: `alembic upgrade head`.
7. Start/restart bot process (`python -m kb_bot.main`).
8. Run post-deploy smoke: `/start`, `/stats`, `/list limit=5`.

## Rollback Baseline (Local)

- App rollback:
  - checkout previous known-good commit/release
  - reinstall dependencies if needed
  - restart bot process
- Data rollback:
  - use restore flow from `docs/RESTORE_RUNBOOK.md`
  - use safe local target DB only

## Operational Notes

- Docker must be running for container-backed DB checks and restore drill.
- Keep `.env` and any secrets out of git.
- Use least-privilege DB credentials when possible, even locally.
- Use `docs/DEPLOY_RUNBOOK.md` for release command and rollback routine.
- Use `docs/SECRETS_RUNBOOK.md` for local secrets validation procedure.
- `docs/RUNTIME_RELIABILITY_RUNBOOK.md` is optional unless you move to Linux/VPS profile.
