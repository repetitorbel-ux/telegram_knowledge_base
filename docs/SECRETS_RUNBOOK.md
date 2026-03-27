# Secrets & Configuration Runbook

This runbook defines how Section 2 ("Configuration & Secrets") is executed in local mode.

## Secret Storage Standard

- Local secrets are stored in repo-local `.env` (ignored by git).
- Optional Linux profile: secrets can be stored in `/etc/tg_kb/.env` with restrictive permissions.
- The `.env` file is never committed to git and never copied into docs/chats.

## Required Variables

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_ID`
- `DATABASE_URL`
- `BACKUP_DIR`
- `PG_DUMP_BIN`
- `PG_RESTORE_BIN`

## Validation Procedure (Section 2)

Run in local repo root:

```powershell
pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath ./.env -Mode local
```

Optional Linux profile:

```bash
pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath /etc/tg_kb/.env -Mode production
```

Expected result:

- `SECTION2_ENV_CHECK: PASS`
- exit code `0`

This command validates:

- no placeholder values are left
- `TELEGRAM_ALLOWED_USER_ID` has numeric format
- `DATABASE_URL` is not test-like and has no placeholders
- backup configuration and postgres binaries are available

## Secret Rotation Policy

- Owner: local operator (you)
- Rotation cadence:
  - `TELEGRAM_BOT_TOKEN`: every 90 days or immediately after suspected leak
  - DB password in `DATABASE_URL`: every 90 days or immediately after suspected leak
- Validation after each rotation:
  - update local `.env`
  - restart bot process
  - run Telegram smoke: `/start`, `/stats`, `/list limit=5`
  - run `pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath ./.env -Mode local`
  - record evidence in `PROD_READINESS_CHECKLIST.md` (date, operator, command result)

## Evidence Format

For each verification/rotation, append to checklist evidence log:

- Date (UTC)
- Item
- Evidence (command + PASS/FAIL + smoke checks)
- Owner
