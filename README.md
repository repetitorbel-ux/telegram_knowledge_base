# telegram-kb-bot (Phase 1)

Single-user Telegram KB bot MVP skeleton.

## Implemented in Phase 1

- Local git repo + feature branch workflow
- Project skeleton (`src/kb_bot`, `tests`)
- aiogram v3 bot with commands:
  - `/start`
  - `/topics`
  - `/add` (FSM: content -> title -> topic UUID -> save)
  - `/search <query>` (search in title/description/notes)
  - `/status <entry_uuid> <status name>` with transition validation
  - `/entry <entry_uuid>` (entry card/details)
  - `/list [status=...] [topic=<uuid>] [limit=...]` (filtered listing)
  - `/topic_add` and `/topic_rename` for dynamic topic tree edits, including nested subtopics
  - Forward message auto-save to default topic `Useful Channels`
  - Saved views (collections): `/collection_add`, `/collections`, `/collection_run`
  - CSV/JSON import via Telegram document (`/import`)
  - CSV/JSON export via `/export` with filters
  - Backup/restore flow (`/backup`, `/backups`, `/restore_token`, `/restore`)
  - Guided backup restore UI with 2-step confirmation and runtime progress feedback
  - Personal dashboard metrics via `/stats`
- Single-user allowlist middleware
- URL normalization + deterministic dedup hash
- SQLAlchemy async setup + Alembic migration
- Initial DB schema:
  - `statuses`
  - `topics`
  - `knowledge_entries`
  - `tags`
  - `knowledge_entry_tags`
- Seed data:
  - statuses: `New`, `To Read`, `Important`, `Archive`, `Verified`, `Outdated`
  - root topics: `Java`, `Git`, `Neural Networks / AI`, `Infrastructure`, `Useful Channels`, `Learning`
- Tests for normalization, dedup, service behavior, migration content, and basic bot-flow helpers

## Quick start

1. Copy env file:
   - `copy .env.example .env`
   - production: `copy env.production.example .env` and set real secrets
2. Fill in:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_ALLOWED_USER_ID`
   - `DATABASE_URL`
3. Ensure PostgreSQL is available (choose one):
   - Docker mode:
     - `docker compose up -d postgres`
     - default local mapped port: `55433`
   - No-Docker mode:
     - run local/remote PostgreSQL outside Docker
     - set `DATABASE_URL` to that instance (common local port: `5432`)
4. Install dependencies:
   - `python -m pip install -e .[dev]`
5. Run migration:
   - `alembic upgrade head`
6. Start bot:
   - `python -m kb_bot.main`

Release smoke options:

- Docker DB mode (default): `pwsh ./scripts/release_smoke.ps1`
- No-Docker DB mode: `pwsh ./scripts/release_smoke.ps1 -DatabaseMode external`

## Run tests

- `python -m pytest -q`

## Topic Hierarchy (User Flows)

- Topics support nesting (for example: `Neural Networks / AI -> Codex`).
- Menu UI:
  - open `Темы` and pick a topic
  - use `Добавить подтему` from topic detail card
  - use `Удалить тему` and confirm to archive/hide a topic branch
- Command mode (all supported):
  - `/topic_add <name>`
  - `/topic_add <parent_uuid|root> <name>`
  - `/topic_add parent=<parent_full_path_or_name> <name>`
  - `/topic_add "Neural Networks / AI" -> Codex`
  - `/topic_rename <topic_uuid> <new_name>`
  - `/topic_delete <topic_uuid|topic_full_path|topic_name>`

## Git Process

- Team git cycle for this repository:
  - `GIT_WORKFLOW.md`

## Readiness

- Local-first readiness checklist:
  - `PROD_READINESS_CHECKLIST.md`
- Section 5 UAT execution template:
  - `docs/UAT_SECTION5_TEMPLATE.md`
- Deployment target definition (local-first):
  - `DEPLOYMENT_TARGET.md`

## Operations

- Deploy procedure and release smoke:
  - `docs/DEPLOY_RUNBOOK.md`
- Runtime reliability (optional Linux profile: systemd/logging/alerts/reboot checks):
  - `docs/RUNTIME_RELIABILITY_RUNBOOK.md`
- Runtime reliability (Windows local profile: Task Scheduler/log files/healthcheck):
  - `docs/RUNTIME_RELIABILITY_RUNBOOK_WINDOWS.md`
- Restore safety checklist and procedure:
  - `docs/RESTORE_RUNBOOK.md`
- Secrets and configuration validation flow:
  - `docs/SECRETS_RUNBOOK.md`
- Section 5 local pre-UAT smoke command:
  - `pwsh ./scripts/section5_local_smoke.ps1`

## Release Notes

- `CHANGELOG.md`
- `docs/RELEASE_NOTES_POLICY.md`

## Workspace AI

- Repo entrypoint for Codex: [AGENTS.md](AGENTS.md)
- Canonical workspace guide: [_workspace_admin/docs/WORKSPACE_GUIDE.md](../_workspace_admin/docs/WORKSPACE_GUIDE.md)
- Windsurf opening guide: [_workspace_admin/docs/HOW_TO_OPEN_PROJECTS_WINDSURF.md](../_workspace_admin/docs/HOW_TO_OPEN_PROJECTS_WINDSURF.md)
- Workspace project registry: [_workspace_admin/inventory/projects.yaml](../_workspace_admin/inventory/projects.yaml)
- Local operator-oriented project note: [instructions/PROJECT_INSTRUCTION.md](instructions/PROJECT_INSTRUCTION.md)

## Current scope limits

- Single-user operation only (allowlist owner flow)
- Local-first operation (Windows + local PostgreSQL)
- No webhook mode (long polling only)
