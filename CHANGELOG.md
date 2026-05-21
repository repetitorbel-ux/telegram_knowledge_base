# Changelog

All notable changes to this project are documented in this file.

## 2026-05-21 (MCP Server)

### Added

- MCP server (`src/kb_bot/mcp_server/`) with 8 tools for LLM access to the knowledge base via Model Context Protocol (stdio transport).
  - `search_entries` — full-text search by query with optional topic filter.
  - `list_entries` — paginated listing of all entries.
  - `get_entry` — fetch a single entry by UUID.
  - `get_related` — fetch semantically/structurally related entries.
  - `list_topics` — topics tree with per-topic entry counts.
  - `get_topic_entries` — entries for a specific topic.
  - `get_stats` — DB statistics (counts, top topics, recent entries).
  - `semantic_search` — embedding-based search (conditional on `SEMANTIC_SEARCH_ENABLED`).
- `.mcp.json` — Claude Desktop / Claude Codex config for the MCP server.
- `src/kb_bot/mcp_server/README.md` — env vars, usage, Claude config.
- `src/kb_bot/mcp_server/evals.xml` — 10 evaluation questions for LLM tool testing.
- `tests/test_mcp_tools.py` — 11 unit tests for all tools (235 total, 0 failed).
- `pyproject.toml`: added `mcp>=1.0.0,<2.0.0`, upgraded `pydantic` to `>=2.11` compatibility.

### Restore swap strategy (PR #52)
- `BackupService.restore_backup` now uses safe swap strategy: restore into `<db>_restore_tmp`, then rename target → `<db>_old_<ts>`, rename tmp → target. Old DB retained for manual rollback.
- Added `psql_bin` / `createdb_bin` config settings (`PSQL_BIN`, `CREATEDB_BIN`).
- Tests updated: swap assertions added, cleanup-on-failure scenario covered.

---

## 2026-05-21 (Desktop reply menu — PR #51)

### Added

- Persistent reply-keyboard main menu for Telegram Desktop (`build_main_reply_keyboard`) — постоянная панель кнопок меню внизу интерфейса.
- Per-topic entry counters in topics tree — счётчик записей рядом с каждой темой.
- Help text handler with full command reference accessible from reply menu.
- New runtime scripts: `run_watchdog_hidden.pyw`, updated `start_bot_local.ps1`, `runtime_healthcheck_local.ps1`.
- Operator docs: `instructions/PROJECT_INSTRUCTION.md`, `instructions/POSTGRES_SERVICE_INCIDENT_RU.md`.

### Changed

- Topic detail keyboard: management buttons (переименовать/добавить подтему/удалить) в одной строке.
- Entry buttons in topic detail: 2 кнопки в ряд вместо по одной.
- Topics tree: добавлена кнопка «Обновить», «В главное меню» перенесена вверх.
- `test_router.py`: обновлён для соответствия новому `main_reply_button` хендлеру (Priority check).

## 2026-04-19

### Added

- Windows watchdog runtime script (`scripts/runtime_watchdog_restart.ps1`) for periodic process monitoring and bot auto-restart.
- Phase 2 requirement FR-024 for runtime supervision with healthcheck + auto-restart.

### Changed

- Task Scheduler registration script now provisions/updates both `tg-kb-bot` and `tg-kb-bot-healthcheck`.
- Watchdog execution switched to hidden window mode to avoid visual flashes on interval runs.
- Local runtime healthcheck behavior refined for direct process detection vs log-only fallback.

### Docs

- Updated Windows runtime reliability runbook with watchdog setup/verification steps.
- Synced Phase 2 SSoT state: P2-001 moved from planned features to implemented requirements.

## 2026-03-26

### Added

- CI workflow for migrations + tests.
- Deploy/restore operational runbooks.
- Production readiness checklist.
- Deployment target definition and production env template.

### Changed

- Restore flow hardening (token/checksum/protected DB guards).
- Manual entry tests converted from skipped to executable tests.

### Docs

- Git workflow standardized and documented.
- Release notes policy added.
