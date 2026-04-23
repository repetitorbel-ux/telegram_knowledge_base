# P2-003: Semantic Search Design

> Status: Design in progress (2026-04-22).
> Goal: Add semantic retrieval without breaking existing keyword search and polling runtime.

---

## Objectives

- Keep existing `/search` keyword behavior as default-safe baseline.
- Add optional embedding-based ranking for better intent matching.
- Preserve single-user local-first profile and predictable operations.
- Support two providers:
  - remote embeddings API (OpenAI-compatible),
  - local embeddings model (offline-capable).

---

## Non-Goals (for first delivery)

- No mandatory migration from polling to webhook.
- No hard dependency on external API provider.
- No cross-user personalization (project remains single-user).
- No ANN sharding/distributed search complexity.

---

## Functional Behavior

### User-facing behavior

- Existing command remains: `/search <query>`.
- By default:
  - run current FTS/trigram path,
  - optionally enrich ranking with semantic score when feature flag enabled.
- If semantic provider fails:
  - fallback to current keyword search path,
  - return results without erroring user flow.

### Ranking strategy (v1)

- Candidate retrieval: current SQL FTS/trgm stack (bounded set).
- Optional semantic rerank:
  - embed query,
  - compare with stored entry embeddings,
  - blend scores:
    - `final_score = alpha * semantic + (1 - alpha) * keyword`
- Default `alpha`: `0.35` (configurable).

---

## Data Model Changes

Add new table (append-only compatible with current schema style):

- `knowledge_entry_embeddings`
  - `entry_id` UUID PK/FK -> `knowledge_entries.id` (ON DELETE CASCADE)
  - `provider` TEXT NOT NULL
  - `model` TEXT NOT NULL
  - `embedding_dim` INT NOT NULL
  - `embedding` VECTOR(N) NOT NULL (pgvector)
  - `content_hash` TEXT NOT NULL (detect stale vectors)
  - `updated_at` TIMESTAMPTZ NOT NULL default now()

Indexes (initial):

- IVFFLAT or HNSW index on `embedding` (final choice depends on pgvector version).
- B-tree index on `(provider, model)`.
- Optional index on `updated_at` for maintenance jobs.

DB extension:

- `CREATE EXTENSION IF NOT EXISTS vector;`

---

## Service Contracts (planned)

### New service: `EmbeddingService`

- `embed_query(text) -> list[float]`
- `embed_entry(entry_id) -> list[float]`
- provider abstraction:
  - `OpenAIEmbeddingProvider`
  - `LocalEmbeddingProvider`

### Search service extension

- `search(query, filters, page, semantic: bool | None = None)`
  - if semantic disabled/unavailable -> existing path only.
  - if enabled -> keyword candidate set + semantic rerank.

### Background refresh (optional but recommended)

- On entry create/update:
  - mark embedding stale if content hash changed.
- Periodic job:
  - backfill missing/stale embeddings in batches.

---

## Configuration (env)

- `SEMANTIC_SEARCH_ENABLED=false`
- `SEMANTIC_PROVIDER=openai|local`
- `SEMANTIC_MODEL=text-embedding-3-small` (provider-specific)
- `SEMANTIC_EMBEDDING_DIM=1536`
- `SEMANTIC_ALPHA=0.35`
- `SEMANTIC_TOP_K_CANDIDATES=100`
- `SEMANTIC_MIN_SCORE=0.0`
- `SEMANTIC_TIMEOUT_MS=3000`

Provider-specific:

- OpenAI-compatible:
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL` (optional override)
- Local:
  - `LOCAL_EMBEDDING_URL` or model runtime config

---

## Migration Plan

1. Add migration:
   - enable `vector` extension,
   - create `knowledge_entry_embeddings`,
   - add indexes.
2. Add repository for embedding CRUD and nearest-neighbor query.
3. Add provider abstraction + config wiring.
4. Add semantic rerank behind feature flag.
5. Add backfill command/job for existing entries.
6. Add observability logs and failure metrics.

---

## Testing Strategy

- Unit:
  - score blending math,
  - provider timeout/failure fallback,
  - stale-hash detection.
- Repository:
  - insert/update embedding row,
  - nearest-neighbor query shape.
- Service:
  - semantic enabled/disabled behavior parity,
  - fallback to keyword path on provider errors.
- Migration:
  - extension/table/index existence.

Acceptance criteria (v1):

- `/search` works unchanged when semantic flag is off.
- With semantic flag on, relevant intent matches improve on curated sample set.
- Provider outage does not break `/search`; fallback is automatic.

---

## Risks & Mitigations

- Provider latency/cost:
  - timeout + fallback + optional local provider.
- Embedding drift after content edits:
  - content hash + periodic backfill.
- Operational complexity:
  - keep semantic path optional and feature-flagged.
- DB growth:
  - one vector per entry in v1, monitor table size and index maintenance.

---

## Rollout Strategy

1. Deploy schema + code with `SEMANTIC_SEARCH_ENABLED=false`.
2. Backfill embeddings for a small subset.
3. Enable semantic in canary sessions (operator-only).
4. Evaluate relevance and latency.
5. Expand to full dataset when stable.
