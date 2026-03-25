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
        subprocess.run([pg_dump_bin, "-Fc", "-f", str(full_path), sync_url], check=True, env=env)

        checksum = _sha256_file(full_path)
        record = BackupRecord(filename=filename, file_path=str(full_path), sha256_checksum=checksum)
        await self.backups_repo.create(record)
        await self.session.commit()
        return BackupResult(backup_id=str(record.id), filename=filename, checksum=checksum)

    async def list_backups(self) -> list[BackupRecord]:
        return await self.backups_repo.list_all()

    async def issue_restore_token(self, backup_id: str) -> str:
        token = secrets.token_hex(8)
        _RESTORE_TOKENS[backup_id] = (token, datetime.now(UTC) + timedelta(minutes=10))
        return token

    async def restore_backup(
        self,
        backup_id: str,
        token: str,
        database_url: str,
        pg_restore_bin: str,
    ) -> None:
        expected = _RESTORE_TOKENS.get(backup_id)
        if expected is None:
            raise ValueError("restore token was not issued")
        expected_token, expires_at = expected
        if datetime.now(UTC) > expires_at or token != expected_token:
            raise ValueError("invalid or expired restore token")

        import uuid

        record = await self.backups_repo.get(uuid.UUID(backup_id))
        if record is None:
            raise ValueError("backup not found")

        sync_url, env = _to_pg_dump_url_and_env(database_url)
        subprocess.run(
            [pg_restore_bin, "--clean", "--if-exists", "-d", sync_url, record.file_path],
            check=True,
            env=env,
        )
        record.restore_tested_at = datetime.now(UTC)
        await self.session.commit()


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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()

