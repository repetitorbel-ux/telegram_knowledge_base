# LAYER-2: Domain Model & Database Schema

> Source: `tz-tg_db.md` sections D (Domain Model), I (SQL DDL, Indexes, Seed Data).
> Read this before touching DB schema, migrations, or ORM models.

---

## Entities Overview

```
KnowledgeEntry ──► Topic (primary_topic_id)
               ──► Status (status_id)
               ──► Source (source_id)
               ──◄► Tag (via knowledge_entry_tags)
               ──◄► Topic (multi, via knowledge_entry_topics — future)
               ──► Attachment
               ──► AuditLog (immutable)

ImportJob / ExportJob / BackupRecord — operational append-only records
SavedView — persisted filter snapshots (smart collections)
RelatedEntryLink — explicit user-pinned relations
```

---

## Core Entities

### KnowledgeEntry
The canonical record for one saved resource.

| Field | Type | Required | Notes |
|---|---|---|---|
| id | UUID | PK | auto |
| original_url | TEXT | optional | Raw URL as received |
| normalized_url | TEXT | optional | After normalization rules |
| telegram_message_link | TEXT | optional | Best-effort `t.me/...` |
| title | TEXT | YES | default `''` |
| description | TEXT | optional | |
| source_id | UUID | optional | FK → Source |
| source_name | TEXT | YES | Denormalized snapshot |
| source_type | TEXT | YES | `telegram_channel`, `web`, `person`, etc. |
| message_date | TIMESTAMPTZ | optional | From `forward_origin.date` |
| saved_date | TIMESTAMPTZ | YES | auto now() |
| primary_topic_id | UUID | YES | FK → Topic |
| status_id | UUID | YES | FK → Status |
| notes | TEXT | optional | |
| dedup_hash | TEXT | YES | UNIQUE. SHA-256 hex |
| content_text | TEXT | optional | Extracted plain text |
| content_tsv | TSVECTOR | computed | FTS trigger-maintained |

### Topic
Dynamic tree. Never use hardcoded IDs.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | TEXT | Display name |
| slug | TEXT | `[a-z0-9_]+` only (ltree-compatible) |
| parent_topic_id | UUID | NULL = root |
| full_path | TEXT | Dot-separated: `neural_networks_ai.llms` |
| full_path_ltree | LTREE | For `<@` descendant queries |
| level | INT | 0 = root |
| is_active | BOOLEAN | |
| is_archived | BOOLEAN | Archived = not selectable by default |

**Hierarchy rules:**
- Rename → recompute slug + all descendant `full_path` and `full_path_ltree`.
- Move → update entire subtree paths.
- No cycles — validated via ltree containment.

### Status (Locked Set)
Exactly 6. Never add, rename, or delete.

| code | display_name | is_terminal |
|---|---|---|
| NEW | New | false |
| TO_READ | To Read | false |
| IMPORTANT | Important | false |
| VERIFIED | Verified | false |
| ARCHIVE | Archive | **true** |
| OUTDATED | Outdated | **true** |

### Tag
Lightweight label. Slug: lowercase `[a-z0-9_]+`, unique.

### Source
Normalized origin: `telegram_channel`, `telegram_chat`, `web_domain`, `person`, etc.

### Jobs & Records (Append-Only)
- **ImportJob**: tracks file imports — total/imported/skipped/duplicate counts.
- **ExportJob**: tracks exports — filter snapshot, exported count, file reference.
- **BackupRecord**: backup metadata — storage location, checksum, `restore_tested_at`.

---

## Key Indexes

| Index | Table | Type | Purpose |
|---|---|---|---|
| `content_tsv` | knowledge_entries | GIN | Full-text search |
| `title` | knowledge_entries | GIN (trgm) | Fuzzy title search |
| `normalized_url` | knowledge_entries | GIN (trgm) | URL fuzzy match |
| `full_path_ltree` | topics | GiST | Subtree queries |
| `dedup_hash` | knowledge_entries | UNIQUE | Deduplication |
| `saved_date`, `status_id`, `primary_topic_id` | knowledge_entries | B-tree | Common filters |

---

## Seed Data (Required After Every Migration)

Must be present after `alembic upgrade head`:
- **6 statuses** — exact codes and display names as listed above.
- **6 root topics** — Java, Git, Neural Networks / AI, Infrastructure, Useful Channels, Learning.
