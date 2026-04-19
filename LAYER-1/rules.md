# LAYER-1: Project Rules & Invariants

> This file defines the non-negotiable rules of the `tg_db` project.
> AI agents MUST read this file before making any code or schema changes.
> See `GIT_WORKFLOW.md` (project root) for branch and commit rules.

---

## 1. System Invariants

These rules MUST NEVER be violated. Any change that breaks them is rejected immediately.

### 1.1 Status Set (Locked — no additions, no renaming)
The system MUST contain exactly 6 statuses with these exact display names:
- `New`
- `To Read`
- `Important`
- `Archive` (terminal — no outgoing transitions)
- `Verified`
- `Outdated` (terminal — no outgoing transitions)

### 1.2 Single-User Allowlist
- EVERY bot handler MUST check `from_user.id == TELEGRAM_ALLOWED_USER_ID`.
- Unauthorized users receive NO data and NO acknowledgment.

### 1.3 Topic Tree
- Topics MUST remain dynamic (no enums, no hardcoded IDs in code).
- Topic hierarchy MUST be cycle-free (validated via `ltree` containment).
- Renaming a topic MUST update all descendant `full_path` / `full_path_ltree` values.

### 1.4 Schema Changes
- ANY change to DB schema requires an Alembic migration.
- Migration MUST be tested on a clean database before merging.
- Seed data (6 statuses + 6 root topics) MUST be present after every `alembic upgrade head`.

### 1.5 Secrets
- Bot token, user ID, DB credentials MUST be in `.env` only.
- `.env` is NEVER committed to git.

---

## 2. Code Quality Rules

- All bot handlers MUST be idempotent where feasible.
- URL normalization and dedup hash MUST remain deterministic and stable (no random salt).
- Tests MUST be updated or added for any change to: URL normalization, dedup logic, status transitions, or topic hierarchy.

---

## 3. AI Agent Rules

- Read `LAYER-2/specs/architecture.md` before editing any service or handler.
- Read `LAYER-2/specs/domain-model.md` before touching DB schema or migrations.
- Read `LAYER-3/HANDOFF.md` at the start of every session to know the current state.
- Do NOT read `tz-tg_db.md` as a source of truth — it is an archived document. Use `LAYER-2/specs/*` instead.
- Do NOT commit directly to `main`. Follow `GIT_WORKFLOW.md`.
