# LAYER-2: Requirements (FR/NFR)

> Source: `tz-tg_db.md` sections A, B, C.
> This file is the authoritative list of what the system MUST do (Phase 1 implemented).
> Phase 2 additions go to `LAYER-2/specs/phase2-features.md`.

---

## Executive Summary

Single-user Telegram personal knowledge base: one bot in a 1:1 chat, backed by PostgreSQL.
Saves and retrieves AI-focused resources (links, forwarded posts, notes) with dynamic hierarchical topics.

**Stack:** Python 3.12+, aiogram v3, PostgreSQL 16+, SQLAlchemy 2.x async, Alembic.

---

## Functional Requirements (Implemented)

### Core Capture
- FR-001 Single Telegram bot, single 1:1 personal chat. No groups/multi-user.
- FR-002 All data persisted in a database.
- FR-003 Single-user allowlist by Telegram user ID.
- FR-004 Manual entry creation via guided bot commands.
- FR-005 Auto-save from forwarded messages via `forward_origin` metadata.
- FR-006 Import entries from CSV and JSON files.
- FR-007 KnowledgeEntry MUST store all mandatory fields (see `domain-model.md`).

### Topic Management
- FR-008 Dynamic hierarchical Topic tree: create/rename/move/archive nodes without code changes.
- FR-009 Seed topics: Java, Git, Neural Networks / AI, Infrastructure, Useful Channels, Learning.

### Search & Retrieval
- FR-010 Keyword search using PostgreSQL full-text search (GIN index).
- FR-011 Tag-based search and tag filtering.
- FR-012 Topic subtree filtering (includes all descendants via `ltree`).
- FR-013 Saved Views (smart collections) — persist filter snapshots, re-runnable.
- FR-014 Related materials suggestions (shared topic/tags + trigram/FTS ranking).

### Workflow
- FR-015 Edit entry metadata (title, description, topic, status, tags, notes).
- FR-016 Exactly 6 statuses: New, To Read, Important, Archive, Verified, Outdated.
- FR-017 Status transition rules enforced (see `behaviors.md`).
- FR-018 Duplicate prevention: URL normalization + dedup hash.
- FR-025 Related materials UI flow is available from entry preview/card and via `/related <entry_uuid>`.
- FR-026 Entry supports multi-topic assignment:
  - one primary topic,
  - zero or more secondary topics via `knowledge_entry_topics`,
  - topic filters include both primary and secondary topic matches.

### Portability & Ops
- FR-019 Export entries to JSON and CSV.
- FR-020 Create backups with checksum and restore verification timestamp.
- FR-021 Restore from backup with safety rails (confirmation token).
- FR-022 Track ImportJob and ExportJob run counts and status.
- FR-023 Personal statistics dashboard (`/stats`).
- FR-024 Production runtime supervision on Windows/Linux (Task Scheduler or systemd) with periodic healthcheck and auto-restart on bot process failure.

---

## Non-Functional Requirements

- NFR-001 Command response time < 2 seconds (non-search, non-import/export).
- NFR-002 Full-text search uses GIN indexed `tsvector` — no full table scans.
- NFR-003 Fuzzy related-item lookups via `pg_trgm` with GIN/GiST indexes.
- NFR-004 Long polling only — no public webhook endpoint required.
- NFR-005 Telegram rate limiting: ≤ 1 message/sec in the private chat (avoid HTTP 429).
- NFR-006 Schema evolution via Alembic migrations only.
- NFR-007 Idempotent handlers — safe to resume after process restarts.
- NFR-008 Secrets via environment variables only — never in source control.
- NFR-009 Unauthorized users receive no data and no acknowledgment.
- NFR-010 Structured JSON logging: message ingests, dedup, imports/exports, backups, errors.
- NFR-011 Reproducible backups via `pg_dump -Fc` / `pg_restore`.
- NFR-012 All DB operations use ORM bindings — no raw string concatenation.
- NFR-013 Topic hierarchy: no cycles, stable ID references after rename/move.
- NFR-014 Unit tests for URL normalization/dedup + integration tests for DB and key flows.
- NFR-015 Graceful degradation when `forward_origin` is absent or `has_protected_content`.
