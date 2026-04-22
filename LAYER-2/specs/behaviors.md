# LAYER-2: Behaviors — User Flows, Bot Commands, Business Rules

> Source: `tz-tg_db.md` sections E (User Flows), F (Bot Commands), G (Search/Dedup/Topic Rules), K (Import/Export/Backup).
> Read before adding or changing bot commands, FSM flows, or business logic.

---

## Bot Commands (Implemented)

| Command | Purpose |
|---|---|
| `/start` | Help + system status (DB connectivity, migration version) |
| `/add` | Guided manual entry creation (FSM) |
| `/inbox` | List entries with status `New` |
| `/search <query>` | FTS keyword search across title/description/notes |
| `/list [status=...] [topic=<uuid>] [limit=...]` | Filtered entry listing |
| `/topics` | Browse topic tree |
| `/topic_add`, `/topic_rename`, `/topic_move`, `/topic_delete` | Topic management |
| `/status <uuid> <name>` | Change entry status |
| `/entry <uuid>` | Entry details card |
| `/entry_delete <uuid>` | Delete entry (with confirmation) |
| `/related <entry_uuid>` | Related entries for one source entry |
| `/entry_topic_add <entry_uuid> <topic_uuid>` | Add secondary topic to entry |
| `/entry_topic_remove <entry_uuid> <topic_uuid>` | Remove secondary topic from entry |
| `/collections`, `/collection_add`, `/collection_run` | Saved views management |
| `/import` | Import via Telegram document (CSV/JSON) |
| `/export` | Export with filters (CSV/JSON) |
| `/backup`, `/backups`, `/restore_token`, `/restore` | Backup and restore flow |
| `/stats` | Personal statistics dashboard |

---

## Key User Flows

### Forward-Save Flow
1. User forwards message/post.
2. Bot validates allowlist.
3. Extracts `forward_origin`, text, URLs.
4. Normalizes URL → computes `dedup_hash`.
5. **Duplicate?** → Offer: Open / Update metadata / Cancel.
6. **New** → Prompt topic selection → optional tags → save entry.

### Status State Machine
Allowed transitions (non-terminal → terminal = one-way):
```
New      → To Read, Important, Archive, Outdated
To Read  → Important, Verified, Archive, Outdated
Important → Verified, Archive, Outdated
Verified → Archive, Outdated
Archive  → (terminal — no outgoing)
Outdated → (terminal — no outgoing)
```
Bot shows ONLY allowed transitions as inline buttons.

---

## Business Rules

### URL Normalization Algorithm
Applied whenever `original_url` is present:
1. Trim whitespace.
2. Parse with `urllib.parse`, reject invalid schemes.
3. Lowercase scheme and host.
4. Remove fragment (`#...`).
5. Normalize percent-encoding.
6. Remove dot-segments in path.
7. Remove tracking parameters: `utm_source`, `utm_medium`, `utm_campaign`, `utm_id`, etc.
8. Sort remaining query parameters (key then value) for determinism.
9. Store result as `normalized_url`.

### Deduplication Logic
1. If URL present: `dedup_hash = sha256("url:" + normalized_url)`.
2. If no URL + forward from channel: `dedup_hash = sha256("tg_origin:" + origin_chat_id + ":" + origin_message_id)`.
3. Default policy on duplicate: **do not insert** → offer merge/update options to user.

### Related Materials Scoring
- +5 if same `primary_topic_id`
- +3 per shared Tag (cap at +9)
- +0..+3 trigram similarity on `title` (pg_trgm)
- +0..+3 FTS rank overlap on `description/notes`
- Returns top 10, excluding self and exact duplicates.

### Related UX Flow (P2-004)
1. User opens entry preview or entry card.
2. Taps `Похожие`.
3. Bot shows compact header `Похожие материалы для: <source_title>`.
4. User navigates related entry buttons and pagination.

Example:
- Source entry title: `PostgreSQL backup strategy`
- Result header: `Похожие материалы для: PostgreSQL backup strategy`
- Actions: `Далее`, `Обновить`, `Назад к записи`.

### Multi-Topic Flow (P2-005)
1. User opens entry preview/card -> `Темы записи`.
2. User can:
   - `Добавить тему` (secondary topic),
   - `Убрать: <topic>` (remove secondary topic),
   - `Сменить основную тему` (switch primary topic via move flow).

Rules:
- One primary topic is mandatory.
- Secondary topic cannot duplicate primary topic.
- Primary topic cannot be removed through secondary-topic removal flow.
- Topic-based list filter matches both primary and secondary topic subtrees.

Examples:
- Add via UI: `Темы записи -> Добавить тему -> Infrastructure`.
- Add via command:
  - `/entry_topic_add 11111111-1111-1111-1111-111111111111 22222222-2222-2222-2222-222222222222`
- Remove via command:
  - `/entry_topic_remove 11111111-1111-1111-1111-111111111111 22222222-2222-2222-2222-222222222222`

### Topic Hierarchy Rules
- Rename: updates `name`, recomputes `slug` and all descendant `full_path` / `full_path_ltree`.
- Archive parent: does NOT force archival of children automatically.
- Cycle prevention: disallow setting parent to self or any descendant.
- Subtree filter: `topic_path <@ selected_topic_path` (ltree `<@` operator).

---

## Import / Export / Backup Rules

### Import
- Accepts: CSV (one row per entry) and JSON (structured).
- Required fields: `title`, `primary_topic_id` (or resolvable topic path), `status`.
- Dedup applied during import — duplicates → increment `duplicate_records` counter.
- Default policy: update missing fields on existing entry, do NOT overwrite title/notes unless empty.

### Export
- JSON: full fidelity including IDs.
- CSV: human-friendly (topic path as string, status display_name).
- `filter_snapshot` stored in ExportJob for audit.
- Phase 2 admin API adds HTTP export trigger:
  - `POST /export` with `X-Admin-Token`,
  - writes exported file to `ADMIN_EXPORT_DIR`,
  - returns `job_id`, `total_records`, and stored file path.

### FastAPI Admin Surface (P2-002)
1. Operator runs `python -m kb_bot.admin_api.main`.
2. `GET /health` returns DB connectivity and current Alembic revision.
3. `POST /export` triggers same export pipeline as Telegram command flow.
4. Invalid/missing token on `/export` returns `401`.

### Backup
- `pg_dump -Fc` to timestamped file → compute sha256 → store BackupRecord.
- Restore requires time-bounded confirmation code to prevent accidental restores.
- Post-restore verification: confirm 6 statuses + 6 root topics present.
- Record `restore_tested_at` after successful verification.
