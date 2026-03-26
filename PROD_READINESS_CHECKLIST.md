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
- [x] Release command is documented and tested end-to-end.
- [x] Database migration step (`alembic upgrade head`) is part of release flow.
- [x] Rollback path is documented and tested at least once.

## 2) Configuration & Secrets

- [~] `TELEGRAM_BOT_TOKEN` secure storage location defined (`/etc/tg_kb/.env`) and pending host validation.
- [~] `TELEGRAM_ALLOWED_USER_ID` is set correctly for production user (pending host validation).
- [~] `DATABASE_URL` points to production DB (not local, not test) (pending host validation).
- [~] `BACKUP_DIR`, `PG_DUMP_BIN`, `PG_RESTORE_BIN` verified on target host (validation script prepared).
- [x] Secret rotation plan exists (who rotates, how often, how validated).
- Section 2 close command on target host: `pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath /etc/tg_kb/.env`
- Section 2 close criteria: command returns `SECTION2_ENV_CHECK: PASS`, then mark remaining Section 2 items as `[x]`.
- Blocker: production host shell access is required to run the close command in real environment.
- Owner: team
- Next action: execute close command on production host and append output summary to Evidence Log.

## 3) Database & Data Safety

- [ ] Backups can be created from production runtime (`/backup`).
- [ ] `/backups` lists newly created records.
- [x] Restore runbook reviewed: `docs/RESTORE_RUNBOOK.md`.
- [x] Restore drill executed in staging/safe DB with successful validation.
- [x] Checksum mismatch scenario is verified as blocked.
- [x] Restore to protected DB names is verified as blocked.

## 4) Runtime Reliability

- [ ] Bot startup command is stable on host restart.
- [ ] Process supervision configured (`systemd`/Docker restart policy/etc.).
- [ ] Logs are persisted and accessible (stdout aggregation or file sink).
- [ ] Error monitoring configured (at minimum: startup failures and exceptions).
- [x] Minimal health check procedure documented.

## 5) Functional UAT (Critical Flows)

- [x] Local pre-UAT smoke for Section 5 command parsing/services is green (`scripts/section5_local_smoke.ps1`).
- [ ] `/start` and auth guard validated with production user.
- [ ] `/add` manual flow validated (URL and note modes).
- [ ] `/search`, `/list`, `/entry`, `/status` validated on real data.
- [ ] Topic flow validated (`/topics`, `/topic_add`, `/topic_rename`).
- [ ] Import/export validated with representative CSV/JSON files.
- [ ] Collection flow validated (`/collection_add`, `/collections`, `/collection_run`).
- [ ] Stats command validated (`/stats`).
- Execution template: `docs/UAT_SECTION5_TEMPLATE.md`

## 6) CI/CD & Quality Gates

- [x] CI workflow exists for migrations + tests (`.github/workflows/ci.yml`).
- [~] Branch protection for `main` enabled (PR required, no direct pushes) - blocked by current GitHub plan for private repo.
- [~] Required checks configured on PR merge - blocked together with branch protection on current plan.
- [x] Release notes/changelog convention agreed.

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
- Evidence: `pwsh ./scripts/release_smoke.ps1` reaches Docker start, but migration step fails in current runner (`asyncio socketpair: Unexpected peer connection`)
- Owner: team

- Date: 2026-03-26
- Item: Release command tested end-to-end
- Evidence: `pwsh ./scripts/release_smoke.ps1` completed successfully (docker up, alembic upgrade head, pytest)
- Owner: team

- Date: 2026-03-26
- Item: Rollback path tested
- Evidence: rollback drill on container DB (`topics` count 6 -> 7 after insert -> 6 after restore; drill topic removed)
- Owner: team

- Date: 2026-03-26
- Item: Restore drill executed and runbook reviewed
- Evidence: `docs/RESTORE_RUNBOOK.md` used; `pg_dump` + `pg_restore --clean --if-exists --single-transaction` validated on safe DB
- Owner: team

- Date: 2026-03-26
- Item: Minimal health check procedure documented
- Evidence: `docs/DEPLOY_RUNBOOK.md` (post-deploy Telegram smoke commands)
- Owner: team

- Date: 2026-03-26
- Item: Branch protection setup attempt
- Evidence: `gh api repos/repetitorbel-ux/telegram_knowledge_base/branches/main/protection` -> HTTP 403 (requires GitHub Pro or public repository)
- Owner: team

- Date: 2026-03-26
- Item: Release notes/changelog convention agreed
- Evidence: `docs/RELEASE_NOTES_POLICY.md`, `CHANGELOG.md`
- Owner: team

- Date: 2026-03-26
- Item: Section 2 secret storage and rotation policy documented
- Evidence: `docs/SECRETS_RUNBOOK.md` (storage path, permissions, rotation cadence, validation flow)
- Owner: team

- Date: 2026-03-26
- Item: Section 2 host validation command prepared
- Evidence: `scripts/verify_prod_env.ps1`; run on target host: `pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath /etc/tg_kb/.env`
- Owner: team

- Date: 2026-03-26
- Item: Section 2 close is blocked in current session
- Evidence: no production shell access in this environment; close command documented and ready
- Owner: team

- Date: 2026-03-26
- Item: Section 5 UAT execution template prepared
- Evidence: `docs/UAT_SECTION5_TEMPLATE.md`
- Owner: team

- Date: 2026-03-26
- Item: Section 5 local pre-UAT smoke
- Evidence: `pwsh ./scripts/section5_local_smoke.ps1` -> `22 passed` (`SECTION5_LOCAL_SMOKE: PASS`)
- Owner: team

## Repo-Verified Snapshot (2026-03-26)

- `CI workflow exists`:
  - `.github/workflows/ci.yml` runs `alembic upgrade head` and `python -m pytest -q`.
- `Migration is in release flow`:
  - README quick start includes `alembic upgrade head`.
- `Restore safety checks implemented and tested`:
  - `src/kb_bot/services/backup_service.py` blocks protected DB targets and validates checksum.
  - `tests/test_backup_service.py` includes checksum-mismatch and protected-DB blocking tests.

## Next Session Priority

1. Run Section 2 host validation command on production host and mark remaining Section 2 items `[x]`.
2. Run Section 5 UAT on target environment using `docs/UAT_SECTION5_TEMPLATE.md` and record results.
3. Implement remaining Runtime Reliability controls (supervision/logging/alerts).
