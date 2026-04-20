# LAYER-3: Project Handoff

> Read this at the start of EVERY session.
> Update this at the end of EVERY session.
> Previous session files: `LAYER-3/sessions/`

---

## Current Status: Phase 1 Complete → Phase 2 In Progress

**Date:** 2026-04-20
**Active branch:** `feature/p2-004-related-ux` (latest local delivery: P2-004 related UX + UI polish)

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
1. **P2-005** — Multi-topic support.
2. **P2-002** — FastAPI admin (optional, low priority).

### Latest Completed in Phase 2 ✅
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

---

## Session Resume Checklist
1. Confirm current branch is NOT `main`.
2. Run local healthcheck: `pwsh ./scripts/runtime_healthcheck_local.ps1`.
3. Telegram smoke: `/start`, `/stats`, `/list limit=5`, preview -> `Похожие` -> pagination -> `Назад к записи`.
4. Merge `feature/p2-004-related-ux` to `main` after final review.
5. Start next feature: `P2-005` multi-topic support.
