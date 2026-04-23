# telegram-kb-bot (Phase 2)

Single-user Telegram KB bot MVP skeleton.

## Implemented

- Local git repo + feature branch workflow
- Project skeleton (`src/kb_bot`, `tests`)
- aiogram v3 bot with commands:
  - `/start`
  - `/topics`
  - `/add` (FSM: content -> title -> topic UUID -> save)
  - `/search <query>` (search in title/description/notes)
  - `/status <entry_uuid> <status name>` with transition validation
  - `/entry <entry_uuid>` (entry card/details)
  - `/entry_delete <entry_uuid>` (delete entry)
  - `/related <entry_uuid>` (related materials for a concrete entry)
  - `/list [status=...] [topic=<uuid>] [limit=...]` (filtered listing)
  - `/entry_topic_add <entry_uuid> <topic_uuid>` (add secondary topic to entry)
  - `/entry_topic_remove <entry_uuid> <topic_uuid>` (remove secondary topic from entry)
  - `/topic_add`, `/topic_move`, and `/topic_rename` for dynamic topic tree edits, including nested subtopics
  - Forward message auto-save to topic `To read` (slug-stable routing) with status `To Read`
  - Saved views (collections): `/collection_add`, `/collections`, `/collection_run`
  - CSV/JSON import via Telegram document (`/import`)
  - CSV/JSON export via `/export` with filters
  - Backup/restore flow (`/backup`, `/backups`, `/restore_token`, `/restore`)
  - Guided backup restore UI with 2-step confirmation and runtime progress feedback
  - Personal dashboard metrics via `/stats`
  - Optional FastAPI admin surface:
    - `GET /health` (DB + migration health),
    - `POST /export` (HTTP export trigger with token auth)
- Single-user allowlist middleware
- URL normalization + deterministic dedup hash
- SQLAlchemy async setup + Alembic migration
- Initial DB schema:
  - `statuses`
  - `topics`
  - `knowledge_entries`
  - `tags`
  - `knowledge_entry_tags`
  - `knowledge_entry_topics` (secondary topics for entries)
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
   - `ADMIN_API_TOKEN` (if FastAPI admin surface is enabled)
   - semantic search (optional):
     - `SEMANTIC_SEARCH_ENABLED=true|false`
     - `SEMANTIC_PROVIDER=openai|local`
     - OpenAI provider: set `OPENAI_API_KEY`
     - local provider: set `LOCAL_EMBEDDING_URL`
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
   - default (long polling): `TELEGRAM_MODE=polling`
   - optional webhook mode:
     - `TELEGRAM_MODE=webhook`
     - `TELEGRAM_WEBHOOK_BASE_URL=https://<public-host>`
     - `TELEGRAM_WEBHOOK_PATH=/telegram/webhook`
     - optional: `TELEGRAM_WEBHOOK_SECRET_TOKEN=<secret>`
   - `python -m kb_bot.main`
7. Optional: start FastAPI admin surface:
   - set `ADMIN_API_ENABLED=true`
   - `python -m kb_bot.admin_api.main`

Release smoke options:

- Docker DB mode (default): `pwsh ./scripts/release_smoke.ps1`
- No-Docker DB mode: `pwsh ./scripts/release_smoke.ps1 -DatabaseMode external`

Semantic embeddings maintenance:

- Backfill/update embeddings for existing entries:
  - `python -m kb_bot.jobs.semantic_backfill --batch-size 100`

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
  - `/topic_move <topic_uuid|topic_full_path|topic_name> <target_parent_uuid|target_parent_full_path|root>`
  - `/topic_rename <topic_uuid> <new_name>`
  - `/topic_delete <topic_uuid|topic_full_path|topic_name>`

## Related Materials (P2-004)

- Launch points:
  - UI: open entry preview/card -> `Похожие`
  - command: `/related <entry_uuid>`
- Screen behavior:
  - compact header: `Похожие материалы для: <title>`
  - list of related entries as buttons
  - navigation: pagination, refresh, back to source entry

Example:
1. Open `Список -> To Read`.
2. Pick entry preview.
3. Tap `Похожие`.
4. Open one of related entries or return via `Назад к записи`.

## Multi-Topic Entries (P2-005)

- Every entry still has one primary topic.
- Entry can additionally have multiple secondary topics.
- Topic filtering (`/list ... topic=<uuid>`) returns entries where topic matches:
  - primary topic subtree OR
  - any secondary topic subtree.

UI example:
1. Open entry preview -> `Темы записи`.
2. Tap `Добавить тему` and pick a topic.
3. Entry appears under both primary and secondary topic filters.
4. Remove via `Убрать: <topic>`.

Command example:
- Add secondary topic:
  - `/entry_topic_add 11111111-1111-1111-1111-111111111111 22222222-2222-2222-2222-222222222222`
- Remove secondary topic:
  - `/entry_topic_remove 11111111-1111-1111-1111-111111111111 22222222-2222-2222-2222-222222222222`

## FastAPI Admin Surface (P2-002)

- Start:
  - `python -m kb_bot.admin_api.main`
- Base URL:
  - `http://<ADMIN_API_HOST>:<ADMIN_API_PORT>`
- Auth:
  - header `X-Admin-Token: <ADMIN_API_TOKEN>` for `POST /export`

### `GET /health`

Response example:

```json
{
  "status": "ok",
  "app_version": "0.1.0",
  "db_ok": true,
  "alembic_revision": "0006_entry_topics",
  "checked_at": "2026-04-21T10:15:10.422377+00:00"
}
```

### `POST /export`

Request example:

```json
{
  "export_format": "json",
  "status_name": "To Read",
  "limit": 20,
  "include_file_base64": false
}
```

Response example:

```json
{
  "job_id": "11111111-1111-1111-1111-111111111111",
  "export_format": "json",
  "total_records": 42,
  "stored_file": "exports/20260421_101510_11111111-1111-1111-1111-111111111111_export.json",
  "content_base64": null
}
```

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
- Webhook mode requires a public HTTPS endpoint
