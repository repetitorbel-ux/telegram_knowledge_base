# AGENTS.md

## AI Workspace — Vibe Coding Edition

This project uses the three-layer Vibe Coding documentation structure.
Read layers in the order shown below at the start of every session.

---

## 📚 Vibe Layer Map (Priority Order)

| Priority | File | Purpose |
|---|---|---|
| 1 | `LAYER-3/HANDOFF.md` | Current session state — read FIRST |
| 2 | `LAYER-1/rules.md` | Non-negotiable project invariants |
| 3 | `LAYER-2/specs/architecture.md` | Components and service contracts |
| 4 | `LAYER-2/specs/domain-model.md` | Entities, DB schema, indexes |
| 5 | `LAYER-2/specs/behaviors.md` | User flows, bot commands, business rules |

**For Phase 2 planning:** also read `LAYER-2/specs/phase2-features.md`.
**For open issues and risks:** `LAYER-2/decisions/open-questions.md`.

---

## ⚠️ Archive Notice

`tz-tg_db.md` (58KB) is the **original monolithic TZ document** — kept for historical reference.
**Do NOT use it as a source of truth.** All authoritative specs are in `LAYER-2/specs/`.

---

## Git Safety

- Follow `GIT_WORKFLOW.md` (project root) for all branch and commit rules.
- Do NOT commit directly to `main`.
- Do NOT create commits until the user has reviewed or explicitly asked.
- Confirm current branch is NOT `main` before any file edit.

---

## Supplementary Resources (Still Valid)

- `instructions/PROJECT_INSTRUCTION.md` — operator-oriented runtime commands and healthcheck scripts.
- `instructions/analiz_before_install_vibe_coding.md` — migration analysis and brainstorm.
- `docs/DEPLOY_RUNBOOK.md`, `docs/RESTORE_RUNBOOK.md`, `docs/SECRETS_RUNBOOK.md` — operational runbooks.
- `PROD_READINESS_CHECKLIST.md` — Phase 1 production readiness (historical, for reference).
- `TASKS.md` — Phase 1 task journal (all done — see `LAYER-3/HANDOFF.md` for Phase 2 state).
