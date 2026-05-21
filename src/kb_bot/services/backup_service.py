import asyncio
import hashlib
import os
import secrets
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

from kb_bot.db.orm.backup import BackupRecord
from kb_bot.db.repositories.backups import BackupsRepository

_RESTORE_TOKENS: dict[str, tuple[str, datetime]] = {}
_PROTECTED_DATABASES = {"postgres", "template0", "template1"}


@dataclass(slots=True)
class BackupResult:
    backup_id: str
    filename: str
    checksum: str


class BackupService:
    def __init__(self, backups_repo: BackupsRepository, session) -> None:
        self.backups_repo = backups_repo
        self.session = session

    async def create_backup(self, database_url: str, backup_dir: str, pg_dump_bin: str) -> BackupResult:
        target_dir = Path(backup_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"tg_kb_{ts}.dump"
        full_path = target_dir / filename

        sync_url, env = _to_pg_dump_url_and_env(database_url)
        await asyncio.to_thread(
            subprocess.run,
            [pg_dump_bin, "-Fc", "-f", str(full_path), sync_url],
            check=True,
            env=env,
        )

        checksum = _sha256_file(full_path)
        record = BackupRecord(filename=filename, file_path=str(full_path.resolve()), sha256_checksum=checksum)
        await self.backups_repo.create(record)
        await self.session.commit()
        return BackupResult(backup_id=str(record.id), filename=filename, checksum=checksum)

    async def list_backups(self, backup_dir: str | None = None) -> list[BackupRecord]:
        if backup_dir:
            await self.sync_backup_catalog(backup_dir)
        return await self.backups_repo.list_all()

    async def sync_backup_catalog(self, backup_dir: str) -> int:
        target_dir = Path(backup_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        rows = await self.backups_repo.list_all()
        known_by_filename = {row.filename: row for row in rows}

        created = 0
        for backup_path in sorted(target_dir.glob("*.dump")):
            if backup_path.name in known_by_filename:
                continue
            checksum = _sha256_file(backup_path)
            record = BackupRecord(
                filename=backup_path.name,
                file_path=str(backup_path.resolve()),
                sha256_checksum=checksum,
            )
            await self.backups_repo.create(record)
            created += 1

        if created:
            await self.session.commit()
        return created

    async def issue_restore_token(self, backup_id: str) -> str:
        _cleanup_expired_tokens()
        token = secrets.token_hex(8)
        _RESTORE_TOKENS[backup_id] = (token, datetime.now(UTC) + timedelta(minutes=10))
        return token

    async def restore_backup(
        self,
        backup_id: str,
        token: str,
        database_url: str,
        pg_restore_bin: str,
        psql_bin: str = "psql",
        createdb_bin: str = "createdb",
        restore_timeout_sec: int = 1800,
    ) -> None:
        _cleanup_expired_tokens()
        expected = _RESTORE_TOKENS.get(backup_id)
        if expected is None:
            raise ValueError("restore token was not issued")
        expected_token, expires_at = expected
        if datetime.now(UTC) > expires_at:
            _RESTORE_TOKENS.pop(backup_id, None)
            raise ValueError("invalid or expired restore token")
        if not secrets.compare_digest(token, expected_token):
            raise ValueError("invalid or expired restore token")

        import uuid

        record = await self.backups_repo.get(uuid.UUID(backup_id))
        if record is None:
            raise ValueError("backup not found")
        backup_path = Path(record.file_path)
        expected_checksum = record.sha256_checksum
        if not backup_path.is_file():
            raise ValueError("backup file is missing")
        actual_checksum = _sha256_file(backup_path)
        if not secrets.compare_digest(actual_checksum, expected_checksum):
            raise ValueError("backup checksum mismatch")

        # Release SQLAlchemy connection locks before any DDL.
        await self.session.rollback()

        sync_url, env = _to_pg_dump_url_and_env(database_url)
        _ensure_restore_target_is_safe(sync_url)

        parsed = urlparse(sync_url)
        db_name = parsed.path.lstrip("/")
        host = parsed.hostname or "localhost"
        port = str(parsed.port or 5432)
        user = parsed.username or ""
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        tmp_db = f"{db_name}_restore_tmp"
        old_db = f"{db_name}_old_{ts}"
        maintenance_url = f"postgresql://{user}@{host}:{port}/postgres"

        def _psql_exec(sql: str) -> None:
            subprocess.run(
                [psql_bin, "-v", "ON_ERROR_STOP=1", "-d", maintenance_url, "-c", sql],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

        # Step 1: drop tmp DB if leftover from previous failed attempt
        try:
            _psql_exec(f'DROP DATABASE IF EXISTS "{tmp_db}";')
        except subprocess.CalledProcessError:
            pass

        # Step 2: create tmp DB
        await asyncio.to_thread(
            subprocess.run,
            [createdb_bin, "-h", host, "-p", port, "-U", user, tmp_db],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )

        tmp_dsn = f"postgresql://{user}@{host}:{port}/{tmp_db}"
        try:
            # Step 3: restore into tmp DB
            await asyncio.to_thread(
                subprocess.run,
                [
                    pg_restore_bin,
                    "--no-owner",
                    "--no-privileges",
                    "-d",
                    tmp_dsn,
                    str(backup_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
                timeout=restore_timeout_sec,
            )

            # Step 4: terminate all connections to target DB (so we can rename it)
            _psql_exec(
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid();"
            )

            # Step 5: rename target → old, tmp → target
            _psql_exec(f'ALTER DATABASE "{db_name}" RENAME TO "{old_db}";')
            _psql_exec(f'ALTER DATABASE "{tmp_db}" RENAME TO "{db_name}";')

        except Exception:
            # Cleanup: drop tmp DB on any failure
            try:
                _psql_exec(f'DROP DATABASE IF EXISTS "{tmp_db}";')
            except Exception:
                pass
            raise

        _RESTORE_TOKENS.pop(backup_id, None)
        refreshed = await self.backups_repo.get(uuid.UUID(backup_id))
        if refreshed is not None:
            refreshed.restore_tested_at = datetime.now(UTC)
            try:
                await self.session.commit()
            except Exception:
                # Session may be invalid after DB rename — not critical
                pass


def _to_pg_dump_url_and_env(database_url: str) -> tuple[str, dict[str, str]]:
    if "+asyncpg" in database_url:
        database_url = database_url.replace("+asyncpg", "")

    parsed = urlparse(database_url)
    env = os.environ.copy()
    password = parsed.password
    if password:
        env["PGPASSWORD"] = password

    user = parsed.username or ""
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    db = parsed.path.lstrip("/")
    sync_url = f"postgresql://{user}@{host}:{port}/{db}"
    return sync_url, env


def _cleanup_expired_tokens() -> None:
    now = datetime.now(UTC)
    expired_ids = [backup_id for backup_id, (_, expires_at) in _RESTORE_TOKENS.items() if expires_at <= now]
    for backup_id in expired_ids:
        _RESTORE_TOKENS.pop(backup_id, None)


def _ensure_restore_target_is_safe(database_url: str) -> None:
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip("/").lower()
    if not db_name:
        raise ValueError("database name is missing in restore target")
    if db_name in _PROTECTED_DATABASES:
        raise ValueError(f"restore to protected database '{db_name}' is forbidden")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
