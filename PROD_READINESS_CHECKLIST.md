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
- [x] Optional: strict secret rotation policy for shared/production usage.
- Local close command: `pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath ./.env -Mode local`
- Close criteria: command returns `SECTION2_ENV_CHECK: PASS`.

## 3) Database & Data Safety (Local)

- [x] Backups can be created from runtime (`/backup`).
- [x] `/backups` lists newly created records.
- [x] Restore runbook reviewed: `docs/RESTORE_RUNBOOK.md`.
- [x] Restore drill executed in staging/safe DB with successful validation.
- [x] Checksum mismatch scenario is verified as blocked.
- [x] Restore to protected DB names is verified as blocked.

## 4) Runtime Reliability (Local)

- [x] Bot startup command is stable after local reboot.
- [x] Autostart strategy is configured (Task Scheduler/startup script/manual start checklist).
- [x] Logs are persisted and accessible locally.
- [x] Error notifications baseline is defined (at minimum: startup failures/exceptions).
- [x] Minimal health check procedure documented.
- [x] Optional (production/Linux profile): `systemd`/journald/OnFailure flow in `docs/RUNTIME_RELIABILITY_RUNBOOK.md`.
- [x] Windows local runtime profile documented: `docs/RUNTIME_RELIABILITY_RUNBOOK_WINDOWS.md`.

## 5) Functional UAT (Critical Flows, Local Telegram)

- [x] Local pre-UAT smoke for Section 5 command parsing/services is green (`scripts/section5_local_smoke.ps1`).
- [x] `/start` and auth guard validated with local owner user.
- [x] `/add` manual flow validated (URL and note modes).
- [x] `/search`, `/list`, `/entry`, `/status` validated on local real data.
- [x] Topic flow validated (`/topics`, `/topic_add`, `/topic_rename`).
- [x] Import/export validated with representative CSV/JSON files.
- [x] Collection flow validated (`/collection_add`, `/collections`, `/collection_run`).
- [x] Stats command validated (`/stats`).
- Execution template: `docs/UAT_SECTION5_TEMPLATE.md`

## 6) CI/CD & Quality Gates

- [x] CI workflow exists for migrations + tests (`.github/workflows/ci.yml`).
- [x] Branch protection for `main` enabled (PR required, no direct pushes).
- [x] Required checks configured on PR merge.
- [x] Release notes/changelog convention agreed.

## 7) Security & Access (Local)

- [x] Repository access reviewed (only required collaborators).
- [x] Local machine access baseline reviewed (OS account and file permissions).
- [x] DB user permissions scoped to required operations only (local DB user).
- [x] No sensitive values present in git history/new commits.

## 8) Local Usage Plan

- [x] First stable local usage date/time and owner assigned.
- [x] Local rollback decision criteria defined.
- [x] First 24h local observation owner assigned.
- [x] Recovery checklist prepared for failures.

## 9) Definition Of Done For Local Launch

Local launch is approved only when all conditions are true:

- [x] Sections 1-5 have no open critical items.
- [x] Backup + restore drill evidence is attached.
- [x] CI is green on latest `main`.
- [x] Local launch and rollback owners confirmed.

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

- Date: 2026-03-27
- Item: Section 5 UAT partial close (`/search`, `/list`, `/entry`, `/status`, import/export, `/stats`)
- Evidence: `docs/UAT_SECTION5_TEMPLATE_RU.md`; exports jobs `586f3753-c104-4e8b-9a92-6166eb3a4c77` (csv), `44e622d3-e0ad-46e9-a7b6-eebc96bfc418` (json); `/stats` -> `Total entries: 6`, `Verified: 1`
- Owner: team

- Date: 2026-03-27
- Item: Section 5 additional UAT close (`/start` auth guard, topic flow, collections)
- Evidence: `docs/UAT_SECTION5_TEMPLATE_RU.md`; `/start` allows owner + `Access denied` for non-allowlisted user; `Topic created` + successful rename; `/collection_run` for `uat_new` returned 5 `New` entries
- Owner: team

- Date: 2026-03-27
- Item: Section 5 final UAT close (`/add` URL/note modes)
- Evidence: `docs/UAT_SECTION5_TEMPLATE_RU.md`; created entries `899c4c42-f311-442a-ae5f-3120f044bf5b` (URL mode) and `db3a893f-842d-405a-99aa-1f01c863e37f` (note mode); both visible in `/list limit=5`
- Owner: team

- Date: 2026-03-27
- Item: Section 3 runtime backup checks (`/backup`, `/backups`)
- Evidence: `/backup` -> backup `4bf25c2a-ca50-4a62-b5fc-c3330756f5ac`, file `tg_kb_20260327_142909.dump`, checksum `679d0ec8d761fcb97cb7e1dea02d4f3dd51e3974c7fd8c1d3e17268d89d8e7a2`; `/backups` lists the same record (`tested=-`)
- Owner: team

- Date: 2026-03-27
- Item: Section 4 local runtime baseline (Windows profile + scripts)
- Evidence: `docs/RUNTIME_RELIABILITY_RUNBOOK_WINDOWS.md`; scripts `scripts/start_bot_local.ps1`, `scripts/register_autostart_task.ps1`, `scripts/runtime_healthcheck_local.ps1`; autostart task creation from restricted session is blocked by host permissions (`schtasks`: access/path errors), needs host-terminal execution
- Owner: team

- Date: 2026-03-27
- Item: Section 4 runtime live verification (local)
- Evidence: `pwsh ./scripts/start_bot_local.ps1` -> bot started with log file `logs/bot_20260327_174900.log`; `pwsh ./scripts/runtime_healthcheck_local.ps1` -> `RUNTIME_CHECK: PASS` (`Process count: 1`)
- Owner: team

- Date: 2026-03-28
- Item: Section 4 close (reboot autostart + Telegram smoke)
- Evidence: after local PC reboot PowerShell autostart ran `scripts/start_bot_local.ps1` (`Starting bot from D:\Development_codex\tg_db`, log `logs\bot_20260328_080437.log`); local check `pwsh ./scripts/runtime_healthcheck_local.ps1` -> `RUNTIME_CHECK: PASS`, `Process count: 1`; Telegram smoke confirms runtime and data path: `/stats` -> `Total entries: 8`, `New: 7`, `Verified: 1`; `/list limit=5` returns latest entries including `db3a893f-842d-405a-99aa-1f01c863e37f`, `899c4c42-f311-442a-ae5f-3120f044bf5b`, `e4138a7e-5925-462c-bbfa-1b1b8c32f00c`
- Owner: team

- Date: 2026-03-28
- Item: Section 7 partial close (repository access + secrets/history)
- Evidence: GitHub collaborators check via `gh api repos/repetitorbel-ux/telegram_knowledge_base/collaborators --paginate --jq '.[].login'` returns single collaborator `repetitorbel-ux`; secret scan in working tree (`rg` for token/DSN patterns, excluding local artifacts) found only placeholders in `.env.example` and `env.production.example`; additional history scan (`git rev-list --all` + `git grep` for `ghp_`/`gho_`) found no matches
- Owner: team

- Date: 2026-03-28
- Item: Section 7 local machine access baseline reviewed
- Evidence: `whoami` -> `asrockb85m\\codexsandboxoffline`; ACL snapshot collected for repo root and `.env` via `Get-Acl`; observed non-owner groups (`BUILTIN\\Пользователи`, `Все`) in ACL entries, to be considered in local hardening follow-up
- Owner: team

- Date: 2026-03-28
- Item: Section 7 DB user permissions scoped (local)
- Evidence: connected via `psql` using `.env` `DATABASE_URL` normalized from `postgresql+asyncpg://` to `postgresql://`; current role `kb_bot_user` on DB `tg_kb`; role flags `super=false`, `createdb=false`, `createrole=false`; table grants in `public` limited to application DML set (SELECT/INSERT/UPDATE/DELETE and related REFERENCES/TRIGGER/TRUNCATE) for bot runtime tables; schema `public` has `USAGE=true`, `CREATE=true` retained for local migration flow (`alembic upgrade head`)
- Owner: team

- Date: 2026-03-28
- Item: Section 8 local usage plan defined
- Evidence: first stable usage window assigned for 2026-03-29 10:00 (Europe/Minsk), owner `repetitorbel-ux`; first 24h observation owner `repetitorbel-ux`; rollback trigger criteria defined as any of: bot process count `0`, failed healthcheck, or critical command regression in `/start` `/stats` `/list`; recovery checklist basis: restart via `scripts/start_bot_local.ps1`, run `scripts/runtime_healthcheck_local.ps1`, use `/backup`/`/backups`/`/restore` flow from `docs/RESTORE_RUNBOOK.md`
- Owner: team

- Date: 2026-03-28
- Item: Section 9 local launch DoD confirmation
- Evidence: Sections 1-5 contain no open critical items; backup/restore drill evidence already recorded on 2026-03-26 and runtime backup checks on 2026-03-27; latest `main` CI is green for HEAD `fe82dbc` (GitHub Actions run `23678984492`, workflow `CI`, `conclusion=success`)
- Owner: team

- Date: 2026-03-28
- Item: Optional Section 2 secret rotation policy closure
- Evidence: `docs/SECRETS_RUNBOOK.md` includes explicit owner, 90-day rotation cadence for Telegram token and DB password, plus mandatory post-rotation validation steps (`verify_prod_env.ps1` + Telegram smoke) and evidence logging format
- Owner: team

- Date: 2026-03-28
- Item: Optional Section 4 Linux runtime profile closure
- Evidence: `docs/RUNTIME_RELIABILITY_RUNBOOK.md` + `deploy/systemd/*` + `scripts/runtime_healthcheck.sh` define full `systemd`/journald/OnFailure profile (install commands, persistent logs, timer healthcheck, reboot verification, evidence requirements)
- Owner: team

- Date: 2026-03-28
- Item: Section 6 branch protection blocker revalidated
- Evidence: `gh api repos/repetitorbel-ux/telegram_knowledge_base/branches/main/protection` -> HTTP 403 (`Upgrade to GitHub Pro or make this repository public to enable this feature`); items remain `[~]` pending plan/repo visibility change
- Owner: team

- Date: 2026-03-28
- Item: Section 6 branch protection and required checks validated as active
- Evidence: validation PR `#15` (`test: validate branch protection behavior`) rejected immediate merge (`base branch policy prohibits the merge`); direct push test `git push origin test/branch-protection-validation-20260328:main` rejected with `GH006 Protected branch update failed` and `At least 1 approving review is required`; PR closed after verification
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
