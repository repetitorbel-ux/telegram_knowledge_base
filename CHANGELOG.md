# Changelog

All notable changes to this project are documented in this file.

## 2026-05-21

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
