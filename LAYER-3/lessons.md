# LAYER-3: Lessons Learned — Phase 1

> Extracted from `CHANGELOG.md` and session recaps.
> Use this to avoid repeating past mistakes and to preserve design decisions.

---

## Technical Decisions Made

### Restore Flow Hardening (2026-03-26)
- Added confirmation token + checksum verification to the restore flow.
- Protected DB guards prevent accidental in-place restores.
- Lesson: Restore is a destructive operation. Default = protect aggressively.

### Manual Entry Tests (2026-03-26)
- Tests were initially skipped due to FSM complexity. Converted to executable.
- Lesson: Skipped tests create false confidence. Convert them, don't defer.

### Git Workflow Standardized (2026-03-26)
- Documented branch discipline: one task = one branch. Main is always protected.
- CI must be green before merge, even in solo mode.

### UI Guided Status + Restore (2026-03-30 → 2026-03-31)
- Guided restore UI with 2-step confirmation and runtime progress feedback.
- Lesson: For destructive confirmed flows, show intermediate states. User must see progress.

### DNS Loopback Incident (2026-03-29)
- After reboot, DNS for Telegram API resolves to `127.*` in some boot cycles.
- Trigger autostart works, but DNS is not always ready at that point.
- Lesson: Add a DNS readiness probe or retry loop before bot connects to Telegram.
- Detail: `LAYER-3/incidents/INCIDENT_2026-03-29_TELEGRAM_DNS_LOOPBACK.md`.

### Reading UX + Delete Flow (2026-04-01)
- Improved entry reading UX and added clean entry delete flow with confirmation.
- Lesson: Delete operations need the same 2-step protection as restore.
