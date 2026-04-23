# LAYER-2: Phase 2 Features

> This file defines planned features for Phase 2.
> After a feature is implemented, move it to `requirements.md` as an FR.

---

## Candidate Features / Status

### P2-002: FastAPI Admin Surface (Optional)
- Status: Delivered (2026-04-21).
- Optional local FastAPI app:
  - `GET /health` returns DB/Alembic health snapshot.
  - `POST /export` triggers export jobs over HTTP with token auth (`X-Admin-Token`).
- Improves monitoring and external automation without Telegram UI dependency.

### P2-003: Semantic Search (Delivered)
- Status: Delivered (2026-04-23).
- Embeddings (OpenAI or local model) + pgvector index.
- Scope for implementation is defined in `LAYER-2/specs/p2-semantic-search-design.md`.
- Runtime baseline remains long polling; webhook track (`P2-006`) is deferred.
- Implemented foundation:
  - migration `0007_semantic_embeddings` with `vector` extension + `knowledge_entry_embeddings`;
  - initial semantic env/config flags (`SEMANTIC_*`, provider endpoints/keys).
  - repository/service baseline for embeddings upsert and similarity candidates (`EmbeddingsRepository`, `EmbeddingService`).
  - semantic rerank hook in `SearchService` behind feature flag with graceful fallback to keyword order.
  - provider layer + runtime factory (`OpenAIEmbeddingProvider`, `LocalHTTPEmbeddingProvider`, `build_embedding_provider`).
  - entry create/edit auto-refreshes embeddings in best-effort mode.
  - maintenance backfill job: `python -m kb_bot.jobs.semantic_backfill`.
- Acceptance evidence (2026-04-23):
  - local Ollama endpoint check PASS (`/api/embeddings` returns embedding vector);
  - backfill PASS on real dataset (`processed=64`) with stable state `updated=0` after sync;
  - DB integrity check PASS: `total_entries=64`, `missing_embeddings=0`, `stale_embeddings=0`;
  - Telegram UI search sanity PASS (keyword + semantic requests);
  - fallback PASS when provider is unavailable (search stays operational via keyword ordering).

### P2-004: Enhanced Related Items UI
- Status: Delivered.
- `/related <entry_uuid>` and entry-context `Похожие` button are both supported.
- Inline navigation and compact related screen are implemented.

### P2-005: Multi-topic Support
- Status: Delivered (2026-04-21).
- `knowledge_entry_topics` table introduced for secondary topics.
- Entry can have one primary and multiple secondary topics.
- UI and command flows:
  - entry screen: `Темы записи` -> add/remove secondary topics;
  - commands: `/entry_topic_add`, `/entry_topic_remove`, `/entry_topic_set_primary`.

### P2-006: Webhook Mode
- Status: Deferred by operator decision (2026-04-22).
- Switch from long polling to webhook for lower latency and lower resource use.
- Requires a public HTTPS endpoint (reverse proxy / tunnel).
- Note: current runtime mode remains `polling`; webhook track is paused until explicitly resumed.

---

## Backlog from Open Decisions

- Restore strategy: restore-to-new-DB-then-swap approach (safer than in-place).
- See `LAYER-2/decisions/open-questions.md` for full context.
