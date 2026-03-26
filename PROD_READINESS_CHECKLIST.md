# Local Readiness Checklist

This checklist is tailored for `telegram-kb-bot` (`tg_db`) and is intended for local single-user operation.  
Production-only controls are marked as optional.

## How To Use

- Mark each item as done only after evidence is available (logs, screenshots, command output, or document link).
- Do not skip blocked items; add owner + next action.
- Use this file as the single source of truth for local readiness.

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

## 2) Local Configuration & Secrets

- [x] `TELEGRAM_BOT_TOKEN` is set in local `.env` and not committed to git.
- [x] `TELEGRAM_ALLOWED_USER_ID` is set to the local owner account.
- [x] `DATABASE_URL` points to local PostgreSQL instance.
- [x] `BACKUP_DIR`, `PG_DUMP_BIN`, `PG_RESTORE_BIN` are valid for local machine.
- [~] Optional: strict secret rotation policy for shared/production usage.
- Local close command: `pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath ./.env -Mode local`
- Close criteria: command returns `SECTION2_ENV_CHECK: PASS`.

## 3) Database & Data Safety (Local)

- [ ] Backups can be created from runtime (`/backup`).
- [ ] `/backups` lists newly created records.
- [x] Restore runbook reviewed: `docs/RESTORE_RUNBOOK.md`.
- [x] Restore drill executed in staging/safe DB with successful validation.
- [x] Checksum mismatch scenario is verified as blocked.
- [x] Restore to protected DB names is verified as blocked.

## 4) Runtime Reliability (Local)

- [ ] Bot startup command is stable after local reboot.
- [ ] Autostart strategy is configured (Task Scheduler/startup script/manual start checklist).
- [ ] Logs are persisted and accessible locally.
- [ ] Error notifications baseline is defined (at minimum: startup failures/exceptions).
- [x] Minimal health check procedure documented.
- [~] Optional (production/Linux profile): `systemd`/journald/OnFailure flow in `docs/RUNTIME_RELIABILITY_RUNBOOK.md`.

## 5) Functional UAT (Critical Flows, Local Telegram)

- [x] Local pre-UAT smoke for Section 5 command parsing/services is green (`scripts/section5_local_smoke.ps1`).
- [ ] `/start` and auth guard validated with local owner user.
- [ ] `/add` manual flow validated (URL and note modes).
- [ ] `/search`, `/list`, `/entry`, `/status` validated on local real data.
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

## 7) Security & Access (Local)

- [ ] Repository access reviewed (only required collaborators).
- [ ] Local machine access baseline reviewed (OS account and file permissions).
- [ ] DB user permissions scoped to required operations only (local DB user).
- [ ] No sensitive values present in git history/new commits.

## 8) Local Usage Plan

- [ ] First stable local usage date/time and owner assigned.
- [ ] Local rollback decision criteria defined.
- [ ] First 24h local observation owner assigned.
- [ ] Recovery checklist prepared for failures.

## 9) Definition Of Done For Local Launch

Local launch is approved only when all conditions are true:

- [ ] Sections 1-5 have no open critical items.
- [ ] Backup + restore drill evidence is attached.
- [ ] CI is green on latest `main`.
- [ ] Local launch and rollback owners confirmed.

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

- Date: 2026-03-26
- Item: Runtime reliability baseline prepared
- Evidence: `docs/RUNTIME_RELIABILITY_RUNBOOK.md`, `deploy/systemd/*`, `scripts/runtime_healthcheck.sh`
- Owner: team

- Date: 2026-03-26
- Item: Checklist switched to local-first mode
- Evidence: sections and acceptance criteria updated for local single-user operation
- Owner: team

- Date: 2026-03-26
- Item: Section 2 local validation run
- Evidence: `pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath ./.env -Mode local` -> FAIL (`TELEGRAM_BOT_TOKEN still has placeholder value`)
- Owner: team

- Date: 2026-03-26
- Item: Section 2 local validation rerun
- Evidence: `pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath ./.env -Mode local` -> `SECTION2_ENV_CHECK: PASS`
- Owner: team

- Date: 2026-03-26
- Item: Full local regression tests
- Evidence: `python -m pytest -q` -> `43 passed`
- Owner: team

- Date: 2026-03-26
- Item: Local runtime start check from current runner
- Evidence: `python -m kb_bot.main` still fails in this restricted session (`ConnectionError: Unexpected peer connection`), run directly in normal local terminal to validate Telegram polling runtime
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

1. Run Section 5 UAT on local Telegram environment using `docs/UAT_SECTION5_TEMPLATE.md`.
2. Choose and apply local runtime strategy for Section 4 (autostart/logging/error visibility).
3. Complete Section 3 backup runtime checks (`/backup`, `/backups`) and attach evidence.
