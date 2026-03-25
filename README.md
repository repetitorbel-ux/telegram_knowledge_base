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
  - `/topic_add` and `/topic_rename` for dynamic topic tree edits
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
2. Fill in:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_ALLOWED_USER_ID`
   - `DATABASE_URL`
3. Start PostgreSQL:
   - `docker-compose up -d`
4. Install dependencies:
   - `python -m pip install -e .[dev]`
5. Run migration:
   - `alembic upgrade head`
6. Start bot:
   - `python -m kb_bot.main`

## Run tests

- `python -m pytest -q`

## Current scope limits

- No forwarded-message ingest flow yet
- No import/export and backup/restore
- No webhook mode (long polling only)
