# Production Readiness Checklist

This checklist is tailored for `telegram-kb-bot` (`tg_db`) and is intended to be executed before first real production launch.

## How To Use

- Mark each item as done only after evidence is available (logs, screenshots, command output, or document link).
- Do not skip blocked items; add owner + next action.
- Use this file as the single source of truth for go-live readiness.

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done

---

## 1) Release & Deployment

- [x] Deployment target is defined (host/container platform, region, runtime).
- [x] `.env` production template is finalized (without secrets in repo).
- [~] Release command is documented and partially tested (blocked by Docker daemon access in current environment).
- [x] Database migration step (`alembic upgrade head`) is part of release flow.
- [~] Rollback path is documented; execution test pending on target/staging host.

## 2) Configuration & Secrets

- [ ] `TELEGRAM_BOT_TOKEN` is stored in secure secret storage.
- [ ] `TELEGRAM_ALLOWED_USER_ID` is set correctly for production user.
- [ ] `DATABASE_URL` points to production DB (not local, not test).
- [ ] `BACKUP_DIR`, `PG_DUMP_BIN`, `PG_RESTORE_BIN` verified on target host.
- [ ] Secret rotation plan exists (who rotates, how often, how validated).

## 3) Database & Data Safety

- [ ] Backups can be created from production runtime (`/backup`).
- [ ] `/backups` lists newly created records.
- [ ] Restore runbook reviewed: `docs/RESTORE_RUNBOOK.md`.
- [ ] Restore drill executed in staging/safe DB with successful validation.
- [x] Checksum mismatch scenario is verified as blocked.
- [x] Restore to protected DB names is verified as blocked.

## 4) Runtime Reliability

- [ ] Bot startup command is stable on host restart.
- [ ] Process supervision configured (`systemd`/Docker restart policy/etc.).
- [ ] Logs are persisted and accessible (stdout aggregation or file sink).
- [ ] Error monitoring configured (at minimum: startup failures and exceptions).
- [x] Minimal health check procedure documented.

## 5) Functional UAT (Critical Flows)

- [ ] `/start` and auth guard validated with production user.
- [ ] `/add` manual flow validated (URL and note modes).
- [ ] `/search`, `/list`, `/entry`, `/status` validated on real data.
- [ ] Topic flow validated (`/topics`, `/topic_add`, `/topic_rename`).
- [ ] Import/export validated with representative CSV/JSON files.
- [ ] Collection flow validated (`/collection_add`, `/collections`, `/collection_run`).
- [ ] Stats command validated (`/stats`).

## 6) CI/CD & Quality Gates

- [x] CI workflow exists for migrations + tests (`.github/workflows/ci.yml`).
- [ ] Branch protection for `main` enabled (PR required, no direct pushes).
- [ ] Required checks configured on PR merge.
- [ ] Release notes/changelog convention agreed.

## 7) Security & Access

- [ ] Repository access reviewed (only required collaborators).
- [ ] Production host access reviewed (least privilege).
- [ ] DB user permissions scoped to required operations only.
- [ ] No sensitive values present in git history/new commits.

## 8) Go-Live Plan

- [ ] Go-live date/time and owner assigned.
- [ ] Rollback decision criteria defined.
- [ ] First 24h monitoring owner assigned.
- [ ] Communication template prepared for incident/update.

## 9) Definition Of Done For Production

Production launch is approved only when all conditions are true:

- [ ] Sections 1-5 have no open critical items.
- [ ] Backup + restore drill evidence is attached.
- [ ] CI is green on latest `main`.
- [ ] Go-live and rollback owners confirmed.

---

## Evidence Log

Use this section to record proof links and timestamps.

- Date:
- Item:
- Evidence:
- Owner:

- Date: 2026-03-26
- Item: Deployment target is defined
- Evidence: `DEPLOYMENT_TARGET.md`
- Owner: team

- Date: 2026-03-26
- Item: `.env` production template is finalized
- Evidence: `env.production.example`
- Owner: team

- Date: 2026-03-26
- Item: Release command documented
- Evidence: `docs/DEPLOY_RUNBOOK.md`, `scripts/release_smoke.ps1`
- Owner: team

- Date: 2026-03-26
- Item: Release smoke execution attempt
- Evidence: `pwsh ./scripts/release_smoke.ps1` failed fast with Docker daemon unavailable (`npipe docker_engine`)
- Owner: team

- Date: 2026-03-26
- Item: Minimal health check procedure documented
- Evidence: `docs/DEPLOY_RUNBOOK.md` (post-deploy Telegram smoke commands)
- Owner: team

## Repo-Verified Snapshot (2026-03-26)

- `CI workflow exists`:
  - `.github/workflows/ci.yml` runs `alembic upgrade head` and `python -m pytest -q`.
- `Migration is in release flow`:
  - README quick start includes `alembic upgrade head`.
- `Restore safety checks implemented and tested`:
  - `src/kb_bot/services/backup_service.py` blocks protected DB targets and validates checksum.
  - `tests/test_backup_service.py` includes checksum-mismatch and protected-DB blocking tests.
