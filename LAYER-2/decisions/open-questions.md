# LAYER-2: Open Questions & Risks

> Source: `tz-tg_db.md` section P (Risks, Assumptions, Open Decisions).
> Update this file when a decision is made or a new risk is identified.

---

## Confirmed Assumptions (Phase 1)

- Long polling via `getUpdates` — no public webhook endpoint needed.
- `ltree` for topic subtree queries.
- `pg_trgm` for fuzzy search and related items.
- Updates not received within 24 hours are lost by Telegram — bot uptime matters.

---

## Open Decisions for Phase 2

| Question | Options | Decision |
|---|---|---|
| FastAPI admin surface? | Bot-only vs. read-only health+export HTTP endpoint | Delivered: optional local FastAPI (`/health`, `/export`) |
| Webhook mode now or later? | Keep polling vs. migrate to webhook with public HTTPS | Deferred by operator on 2026-04-22; keep polling for now |
| Restore strategy | In-place restore vs. restore-to-new-DB then swap DSN | TBD — new-DB is safer |
| Semantic search | Out of MVP scope — would require embeddings + vector index | Deferred |

---

## Known Risks

| Risk | Severity | Mitigation |
|---|---|---|
| `has_protected_content` — no origin metadata | Medium | Graceful degradation (save without source attribution) |
| Telegram 429 rate limit | Medium | Batch bot responses; use edit-in-place where possible |
| `ltree` slug restrictions | Low | Sanitize topic names to `[a-z0-9_]+` before storage |
| DNS loopback after reboot | Medium | See `LAYER-3/incidents/INCIDENT_2026-03-29_TELEGRAM_DNS_LOOPBACK.md` |

---

## Resolved Decisions (Phase 1)

- Restore uses confirmation code (time-bounded hash) — prevents accidental restores. ✅
- Duplicate policy: default = block and present merge options (not silent skip). ✅
- Topic rename updates ALL descendant paths atomically. ✅
