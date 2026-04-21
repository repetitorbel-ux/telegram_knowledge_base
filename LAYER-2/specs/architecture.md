# LAYER-2: Architecture

> Source: `tz-tg_db.md` sections H (Architecture), M (Project Structure), J (Internal Service Contracts).
> Read this before editing any service, handler, or adding new components.

---

## System Overview

Single-process async Python bot operating in long-polling mode.
No public HTTP endpoint in MVP — Telegram delivers updates via `getUpdates`.

```
Telegram ──► aiogram Bot Process ──► Application Services ──► PostgreSQL
                                 └──────────────────────────► Local Storage (exports/backups)
```

---

## Backend Modules

| Module | Responsibility |
|---|---|
| `bot/` | Telegram handlers, routers, FSM states, inline keyboards |
| `domain/` | Immutable domain rules: status transitions, invariants |
| `services/` | Application use-cases (transactions, validation, orchestration) |
| `db/` | SQLAlchemy ORM models, repositories, Alembic migrations |
| `jobs/` | Async background tasks: import, export, backup |
| `core/` | Config, logging, allowlist, URL normalization, dedup |

---

## Database Extensions Required

- `ltree` — Topic subtree queries and efficient hierarchy indexing.
- `pg_trgm` — Fuzzy similarity for related-item lookups.
- `pgcrypto` — UUID generation (`gen_random_uuid()`).

---

## Internal Service Contracts

### EntryService
- `create_from_forward(update_message) → KnowledgeEntryDTO`
  - Extracts `forward_origin`, normalizes URL, computes dedup_hash.
  - Errors: `UnauthorizedUser`, `InvalidTopic`, `DuplicateDetected(existing_id)`
- `create_manual(payload) → KnowledgeEntryDTO`
- `update_entry(entry_id, patch) → KnowledgeEntryDTO`
- `set_status(entry_id, new_status_code) → KnowledgeEntryDTO` — validates allowed transitions.
- `move_to_topic(entry_id, topic_id) → KnowledgeEntryDTO` — changes primary topic.
- `add_secondary_topic(entry_id, topic_id) → list[TopicDTO]`
- `remove_secondary_topic(entry_id, topic_id) → list[TopicDTO]`
- `list_secondary_topics(entry_id) → list[TopicDTO]`

### TopicService
- `list_tree() → TopicTreeDTO`
- `create_topic(parent_id|null, name) → TopicDTO`
- `rename_topic(topic_id, new_name) → TopicDTO` — recomputes all descendant paths.
- `move_topic(topic_id, new_parent_id|null) → TopicDTO` — validates no cycles.
- `archive_topic(topic_id) → TopicDTO`

### SearchService
- `search(query, filters, page) → SearchResultPage` — FTS with GIN index.
- `related(entry_id, limit=10) → list[KnowledgeEntryDTO]` — pg_trgm similarity.

### ImportExportService
- `start_import(file_ref, format) → ImportJobDTO` — parses CSV/JSON, applies dedup.
- `start_export(filter_snapshot, format) → ExportJobDTO`

### BackupService
- `create_backup() → BackupRecordDTO` — runs `pg_dump -Fc`, stores checksum.
- `restore_backup(backup_id, confirmation_code) → RestoreResult`

---

## Repository Structure (Physical)

```
src/kb_bot/
├── bot/          # handlers/, ui/, fsm/
├── core/         # config, logging, auth, url_normalization, dedup
├── domain/       # models, status_machine, errors
├── services/     # entry_service, topic_service, search_service, ...
├── db/           # engine, session, repositories/, orm/, migrations/
└── jobs/         # runner, import_job, export_job, backup_job
```

---

## Configuration

- `.env` — secrets (token, user ID, DB URL, backup path). Never in git.
- `docker-compose.yml` — PostgreSQL for local dev.
- `.codex/config.toml` — Codex model defaults and sandbox settings.
- `.codex/rules/default.rules` — Starlark rules for AI command approval.

---

## Security Baseline

- Allowlist check: EVERY handler validates `from_user.id == TELEGRAM_ALLOWED_USER_ID`.
- No HTTP listener in MVP (long polling only).
- Soft-delete guarded by confirmation for destructive operations.
- Structured JSON logs for all critical operations.
