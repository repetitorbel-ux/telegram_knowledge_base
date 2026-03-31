# Restore Runbook

This runbook describes a safe restore flow for `telegram-kb-bot`.

## Preconditions

- Bot process is running with valid DB access.
- Backup dump file exists on disk in `BACKUP_DIR`.
- You understand restore impact: `pg_restore --clean --if-exists` recreates objects in target DB.

## Safety Controls Implemented

- Restore token is required (`/restore_token <backup_uuid>`).
- Token is valid for 10 minutes and single-use.
- Backup file existence is validated before restore.
- Backup SHA256 is re-checked before restore.
- Restore to protected DB names is blocked: `postgres`, `template0`, `template1`.
- Restore uses safer flags: `--single-transaction --no-owner --no-privileges`.

## Standard Restore Procedure

1. List available backups:
   - `/backups`
2. Pick backup UUID.
3. Issue restore token:
   - `/restore_token <backup_uuid>`
4. Immediately execute restore:
   - `/restore <backup_uuid> <token>`
5. Validate bot commands:
   - `/start`
   - `/stats`
   - `/list limit=5`

## Failure Scenarios

- `restore token was not issued`:
  - Issue token again with `/restore_token`.
- `invalid or expired restore token`:
  - Token expired or typo; issue a new one.
- `backup file is missing`:
  - Restore dump file into expected path or choose another backup.
- `backup not found`:
  - Re-run `/backups` and use a fresh UUID from the latest list.
  - Note: after restore to an older snapshot, `backup_records` may roll back; the bot resyncs catalog from dump files on listing.
- `backup checksum mismatch`:
  - File was modified/corrupted. Do not restore; use another backup.
- `restore to protected database ... is forbidden`:
  - Verify `DATABASE_URL` points to the application DB (not system DB).

## Operational Notes

- Keep dumps and DB credentials accessible only to trusted operators.
- Prefer restoring during maintenance windows.
- After restore, create a fresh backup and verify `/stats` + basic read commands.
- Backup UUIDs can change after restore to older snapshots because DB state is restored from dump content.
- `/backups` performs catalog resync from dump files so missing records are re-indexed automatically.
