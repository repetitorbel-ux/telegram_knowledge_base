# Secrets & Configuration Runbook

This runbook defines how Section 2 ("Configuration & Secrets") is executed on the production host.

## Secret Storage Standard

- Production secrets are stored only in host file: `/etc/tg_kb/.env`.
- Ownership: `tgkb:tgkb` (or dedicated service user/group).
- Permissions: `600` (read/write for owner only).
- The `.env` file is never committed to git and never copied into docs/chats.

## Required Variables

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_ID`
- `DATABASE_URL`
- `BACKUP_DIR`
- `PG_DUMP_BIN`
- `PG_RESTORE_BIN`

## Validation Procedure (Section 2)

Run on production host:

```bash
pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath /etc/tg_kb/.env
```

Expected result:

- `SECTION2_ENV_CHECK: PASS`
- exit code `0`

This command validates:

- no placeholder values are left
- `TELEGRAM_ALLOWED_USER_ID` has numeric format
- `DATABASE_URL` is not local/test-like
- backup configuration and postgres binaries are available

## Secret Rotation Policy

- Owner: on-call operator (primary) + repository owner (backup approver)
- Rotation cadence:
  - `TELEGRAM_BOT_TOKEN`: every 90 days or immediately after suspected leak
  - DB password in `DATABASE_URL`: every 90 days or immediately after suspected leak
- Validation after each rotation:
  - update `/etc/tg_kb/.env`
  - restart bot process
  - run Telegram smoke: `/start`, `/stats`, `/list limit=5`
  - run `pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath /etc/tg_kb/.env`
  - record evidence in `PROD_READINESS_CHECKLIST.md` (date, operator, command result)

## Evidence Format

For each verification/rotation, append to checklist evidence log:

- Date (UTC)
- Item
- Evidence (command + PASS/FAIL + smoke checks)
- Owner
