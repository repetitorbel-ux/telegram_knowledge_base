# Changelog

All notable changes to this project are documented in this file.

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
