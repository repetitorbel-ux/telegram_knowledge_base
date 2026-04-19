# LAYER-3: Project Handoff

> Read this at the start of EVERY session.
> Update this at the end of EVERY session.
> Previous session files: `LAYER-3/sessions/`

---

## Current Status: Phase 1 Complete → Phase 2 In Progress

**Date:** 2026-04-19
**Active branch:** `main` (latest merged: P2-001 runtime supervision)

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
1. **P2-004** — Enhanced `/related` command UX.
2. **P2-002** — FastAPI admin (optional, low priority).
3. **P2-005** — Multi-topic support.

### Latest Completed in Phase 2 ✅
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
3. Telegram smoke: `/start`, `/stats`, `/list limit=5`.
4. Update this file with today's work at session end.
