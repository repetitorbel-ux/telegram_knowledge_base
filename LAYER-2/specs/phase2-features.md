# LAYER-2: Phase 2 Features

> This file defines planned features for Phase 2.
> After a feature is implemented, move it to `requirements.md` as an FR.

---

## Candidate Features

### P2-002: FastAPI Admin Surface (Optional)
- Read-only health endpoint + export trigger via HTTP.
- Would allow monitoring without Telegram access.
- Open decision: see `LAYER-2/decisions/open-questions.md`.

### P2-003: Semantic Search (Deferred)
- Embeddings (OpenAI or local model) + pgvector index.
- Out of scope until basic ops is stable.

### P2-004: Enhanced Related Items UI
- Surface `/related <entry_uuid>` command results with inline navigation.
- Currently computed but not prominently exposed.

### P2-005: Multi-topic Support
- `knowledge_entry_topics` table already exists (future-proof).
- Allow entry to belong to more than one topic (secondary topics).

### P2-006: Webhook Mode
- Switch from long polling to webhook for lower latency and lower resource use.
- Requires a public HTTPS endpoint (reverse proxy / tunnel).

---

## Backlog from Open Decisions

- Restore strategy: restore-to-new-DB-then-swap approach (safer than in-place).
- See `LAYER-2/decisions/open-questions.md` for full context.
