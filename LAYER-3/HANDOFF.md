# LAYER-3: Project Handoff

> Read this at the start of EVERY session.
> Update this at the end of EVERY session.
> Previous session files: `LAYER-3/sessions/`

---

## Current Status: Phase 1 Complete → Phase 2 In Progress

**Date:** 2026-05-21
**Active branch:** `feature/mcp-server` (PR #53 open, CI pending)

### Phase 1 — Done ✅
All 42 tasks completed. Bot fully operational:
- All commands implemented: `/add`, `/search`, `/list`, `/status`, `/entry`, `/topics`, `/topic_add`, `/topic_rename`, `/collection_add`, `/import`, `/export`, `/backup`, `/restore`, `/stats`.
- Full test coverage for: URL normalization, dedup, service behavior, migration, bot flows, search parsing, status transitions, topic parsing, forward handling, collections, import/export, backup.
- README updated. CI green.

### Infrastructure Ready
- `PROD_READINESS_CHECKLIST.md` — local deployment checklist.
- `DEPLOYMENT_TARGET.md` — deployment target definition.
- Runbooks in `docs/`: DEPLOY, RESTORE, SECRETS, RUNTIME (Linux + Windows).

---

## Phase 2 Queue (Pending)

See `LAYER-2/specs/phase2-features.md` for full backlog.

Priority order (suggested):
1. **P2-003** — Semantic search (**Delivered on 2026-04-23**).
2. **P2-006** — Webhook mode (**Deferred by operator decision on 2026-04-22; keep polling mode for now**).

### Latest Progress in Phase 2 (Current Session) ✅

- **MCP Server** — LLM access to knowledge base via Model Context Protocol (PR #53, 2026-05-21):
  - `src/kb_bot/mcp_server/` package with `FastMCP` server, 8 tools, stdio transport.
  - Tools: `search_entries`, `list_entries`, `get_entry`, `get_related`, `list_topics`, `get_topic_entries`, `get_stats`, `semantic_search`.
  - `.mcp.json` config for Claude Desktop / Claude Codex.
  - `tests/test_mcp_tools.py` — 11 tests, 235 total passed, 0 failed.
  - `src/kb_bot/mcp_server/README.md` + `evals.xml` (10 eval questions).
  - `pydantic` upgraded to `>=2.11` compat (mcp 1.27.1 requirement).
  - Status: committed on `feature/mcp-server`, PR #53 pending.

- **Restore swap strategy** — Safe `/restore` using createdb + pg_restore + rename (PR #52, merged 2026-05-21):
  - Old DB preserved as `<db>_old_<ts>` for manual rollback.
  - `psql_bin` / `createdb_bin` config settings added.

- **P2-UX-desktop** — Desktop reply menu + UX polish (PR #51, merged 2026-05-21):
  - Added persistent reply-keyboard main menu (`build_main_reply_keyboard`).
  - Per-topic entry counters in topics tree.
  - Help handler с полным списком команд.
  - CI: 222 passed, 0 failed.

- **P2-003** — semantic search foundation delivered on 2026-04-23:
  - Added migration `0007_semantic_embeddings` (`vector` extension + `knowledge_entry_embeddings` table + indexes).
  - Added migration `0008_embedding_dim_768` for local Ollama mode (`vector(768)`).
  - Added semantic runtime config flags (`SEMANTIC_*`, provider endpoint/key settings) to env and settings model.
  - Added repository/service baseline for embeddings upsert/hash/similarity (`EmbeddingsRepository`, `EmbeddingService`).
  - Added semantic rerank path in `SearchService` behind `SEMANTIC_SEARCH_ENABLED`, with fallback to keyword ordering on any semantic failure.
  - Added embedding provider/runtime layer (`OpenAIEmbeddingProvider`, `LocalHTTPEmbeddingProvider`, runtime factory helpers).
  - Wired best-effort embedding refresh into entry create/edit flows.
  - Added semantic embeddings backfill CLI job: `python -m kb_bot.jobs.semantic_backfill`.
  - Stability fixes for local mode:
    - proxy-safe local HTTP calls (`trust_env=False`);
    - retry/fallback handling for transient provider errors;
    - context-length adaptive shortening for Ollama `HTTP 500` cases.
  - Added/updated tests:
    - `tests/test_semantic_embeddings_migration.py`
    - `tests/test_embedding_providers.py`
    - `tests/test_embedding_service.py`
  - Acceptance evidence (2026-04-23):
    - endpoint check PASS: local `/api/embeddings` responds with embedding vector;
    - backfill sync PASS on real dataset (`processed=64`, stable `updated=0` after sync);
    - DB consistency PASS: `total_entries=64`, `missing_embeddings=0`, `stale_embeddings=0`;
    - Telegram search sanity PASS for keyword and semantic-style queries;
    - fallback PASS when provider unavailable (search remains available via keyword path).

### Latest Completed in Phase 2 ✅
- **P2-002** — FastAPI admin surface completed on 2026-04-21:
  - Added optional FastAPI module `kb_bot.admin_api`.
  - Implemented `GET /health` with DB probe and Alembic revision reporting.
  - Implemented authenticated `POST /export` trigger with `X-Admin-Token`.
  - Added admin runtime config (`ADMIN_API_*`) and export storage path (`ADMIN_EXPORT_DIR`).
  - Added API test coverage (`tests/test_admin_api.py`) and docs/env updates.
- **P2-005** — Multi-topic support completed on 2026-04-21:
  - Added secondary-topic storage via `knowledge_entry_topics` + migration.
  - Entry topic UI implemented from preview/card: `Темы записи`.
  - Topic management actions implemented: add secondary topic, remove secondary topic, promote secondary topic to primary.
  - Commands implemented and wired end-to-end: `/entry_topic_add`, `/entry_topic_remove`, `/entry_topic_set_primary`.
  - UI polish based on manual checks: topic-management and navigation button rows optimized for Telegram mobile layout.
  - Test coverage added/updated for repository, parsing, UI flows, migration, and handlers.
- **P2-004** — Enhanced `/related` UX completed on 2026-04-20:
  - `/related` end-to-end flow implemented (service scoring + callbacks + repositories + DTO).
  - `Похожие` removed from main menu; scenario is now entry-contextual (preview/card).
  - Related screen simplified: compact header + buttons (no verbose score/reasons in text).
  - UI polish: unified back labels; list screen de-duplicated; key button blocks re-laid for better mobile use.
  - Test coverage added/updated (`tests/test_related_handler.py`, `tests/test_search_service.py`, `tests/test_ui_menu.py`).
- **P2-001** — Production deployment baseline completed on 2026-04-19:
  - Windows Task Scheduler autostart + periodic watchdog (`tg-kb-bot-healthcheck`).
  - Auto-restart when bot process is missing.
  - Hidden watchdog execution mode to avoid UI flashes.
  - Runbook/docs updated.

---

## Known Open Incident
- **DNS loopback after reboot**: Telegram DNS resolves to `127.*` in some boot cycles.
- Detail: `LAYER-3/incidents/INCIDENT_2026-03-29_TELEGRAM_DNS_LOOPBACK.md`.
- Recovery steps are documented in the incident file.
- **2026-05-08 local Winsock/proxy breakage**: after ISP proxy setup, bot callback/list buttons appeared unresponsive because PostgreSQL at `127.0.0.1:5432` was unreachable. Evidence:
  - bot logs showed `ConnectionRefusedError: [Errno 10061] Connect call failed ('127.0.0.1', 5432)`;
  - `pg_isready -h 127.0.0.1 -p 5432` returned no response;
  - Python socket creation failed with `WinError 10106`;
  - PostgreSQL service `postgresql-x64-17` was `Stopped`/`Disabled`, and non-admin service start was denied.
  Runtime scripts were hardened so healthcheck/launcher fail on DB precheck instead of reporting a false PASS.
  - Current follow-up evidence (2026-05-08): service `postgresql-x64-17` is now `Running`/`Automatic`, but `pg_isready` still reports no response and Python socket creation still fails with `WinError 10106`; likely remaining fix is an administrator-level Winsock reset followed by Windows restart.

---

## Session Resume Checklist
1. Confirm current branch is NOT `main`.
2. Run local healthcheck: `pwsh ./scripts/runtime_healthcheck_local.ps1`.
3. FastAPI smoke: run `python -m kb_bot.admin_api.main`, check `GET /health`, then `POST /export` with `X-Admin-Token`.
4. Telegram smoke for topics: `/start`, `/list limit=5`, open preview -> `Темы записи` -> add/remove secondary topic -> `Сделать основной`.
5. Keep runtime in polling mode; do not start `P2-006` implementation until operator re-opens webhook track.
6. `P2-003` acceptance completed on 2026-04-23; keep evidence synced in handoff/spec files.
