# LAYER-2: Phase 2 Features

> This file defines planned features for Phase 2.
> After a feature is implemented, move it to `requirements.md` as an FR.

---

## Candidate Features / Status

### P2-002: FastAPI Admin Surface (Optional)
- Read-only health endpoint + export trigger via HTTP.
- Would allow monitoring without Telegram access.
- Open decision: see `LAYER-2/decisions/open-questions.md`.

### P2-003: Semantic Search (Deferred)
- Embeddings (OpenAI or local model) + pgvector index.
- Out of scope until basic ops is stable.

### P2-004: Enhanced Related Items UI
- Status: Delivered.
- `/related <entry_uuid>` and entry-context `Похожие` button are both supported.
- Inline navigation and compact related screen are implemented.

### P2-005: Multi-topic Support
- Status: In progress (implementation branch).
- `knowledge_entry_topics` table introduced for secondary topics.
- Entry can have one primary and multiple secondary topics.
- UI and command flows:
  - entry screen: `Темы записи` -> add/remove secondary topics;
  - commands: `/entry_topic_add`, `/entry_topic_remove`.

### P2-006: Webhook Mode
- Switch from long polling to webhook for lower latency and lower resource use.
- Requires a public HTTPS endpoint (reverse proxy / tunnel).

---

## Backlog from Open Decisions

- Restore strategy: restore-to-new-DB-then-swap approach (safer than in-place).
- See `LAYER-2/decisions/open-questions.md` for full context.
