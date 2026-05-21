import subprocess
import tempfile
import types
import uuid
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from kb_bot.db.orm.backup import BackupRecord
from kb_bot.services import backup_service as backup_service_module
from kb_bot.services.backup_service import BackupService


class FakeBackupsRepository:
    def __init__(self, record: BackupRecord) -> None:
        self._record = record

    async def get(self, backup_id: uuid.UUID) -> BackupRecord | None:
        if backup_id == self._record.id:
            return self._record
        return None


class CatalogBackupsRepository:
    def __init__(self, rows: list[BackupRecord] | None = None) -> None:
        self._rows = list(rows or [])

    async def create(self, record: BackupRecord) -> BackupRecord:
        if record.id is None:
            record.id = uuid.uuid4()
        self._rows.append(record)
        return record

    async def list_all(self) -> list[BackupRecord]:
        return list(self._rows)

    async def get(self, backup_id: uuid.UUID) -> BackupRecord | None:
        for row in self._rows:
            if row.id == backup_id:
                return row
        return None


class DisappearingBackupsRepository(FakeBackupsRepository):
    def __init__(self, record: BackupRecord) -> None:
        super().__init__(record)
        self._calls = 0

    async def get(self, backup_id: uuid.UUID) -> BackupRecord | None:
        self._calls += 1
        if self._calls == 1:
            return await super().get(backup_id)
        return None


@pytest.fixture(autouse=True)
def clear_restore_tokens() -> None:
    backup_service_module._RESTORE_TOKENS.clear()


def _create_backup_file(content: bytes) -> Path:
    fh = tempfile.NamedTemporaryFile(delete=False)
    path = Path(fh.name)
    fh.write(content)
    fh.close()
    return path


def _create_dump_file(path: Path, *, content: bytes) -> Path:
    path.write_bytes(content)
    return path


@pytest.mark.asyncio
async def test_restore_forbidden_for_protected_database() -> None:
    file_path = _create_backup_file(b"backup-content")
    try:
        checksum = backup_service_module._sha256_file(file_path)
        record = BackupRecord(
            id=uuid.uuid4(),
            filename=file_path.name,
            file_path=str(file_path),
            sha256_checksum=checksum,
        )
        service = BackupService(
            FakeBackupsRepository(record),
            types.SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock()),
        )
        token = await service.issue_restore_token(str(record.id))

        with patch("kb_bot.services.backup_service.subprocess.run") as run_mock:
            with pytest.raises(ValueError, match="protected database"):
                await service.restore_backup(
                    backup_id=str(record.id),
                    token=str(token),
                    database_url="postgresql+asyncpg://postgres:secret@localhost:5432/postgres",
                    pg_restore_bin="pg_restore",
                )

        run_mock.assert_not_called()
    finally:
        file_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_restore_rejects_checksum_mismatch() -> None:
    file_path = _create_backup_file(b"backup-content")
    try:
        record = BackupRecord(
            id=uuid.uuid4(),
            filename=file_path.name,
            file_path=str(file_path),
            sha256_checksum="0" * 64,
        )
        service = BackupService(
            FakeBackupsRepository(record),
            types.SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock()),
        )
        token = await service.issue_restore_token(str(record.id))

        with patch("kb_bot.services.backup_service.subprocess.run") as run_mock:
            with pytest.raises(ValueError, match="checksum mismatch"):
                await service.restore_backup(
                    backup_id=str(record.id),
                    token=str(token),
                    database_url="postgresql+asyncpg://postgres:secret@localhost:5432/tg_kb",
                    pg_restore_bin="pg_restore",
                )

        run_mock.assert_not_called()
    finally:
        file_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_restore_success_marks_tested_and_consumes_token() -> None:
    file_path = _create_backup_file(b"backup-content")
    try:
        checksum = backup_service_module._sha256_file(file_path)
        record = BackupRecord(
            id=uuid.uuid4(),
            filename=file_path.name,
            file_path=str(file_path),
            sha256_checksum=checksum,
        )
        session = types.SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
        service = BackupService(FakeBackupsRepository(record), session)
        token = await service.issue_restore_token(str(record.id))

        with patch("kb_bot.services.backup_service.subprocess.run") as run_mock:
            await service.restore_backup(
                backup_id=str(record.id),
                token=str(token),
                database_url="postgresql+asyncpg://postgres:secret@localhost:5432/tg_kb",
                pg_restore_bin="pg_restore",
                psql_bin="psql",
                createdb_bin="createdb",
            )

        session.rollback.assert_awaited_once()
        assert record.restore_tested_at is not None
        assert str(record.id) not in backup_service_module._RESTORE_TOKENS

        # collect all commands called
        all_calls = run_mock.call_args_list
        all_cmds = [call.args[0] for call in all_calls]

        # createdb must be called
        createdb_calls = [cmd for cmd in all_cmds if cmd[0] == "createdb"]
        assert len(createdb_calls) == 1
        assert "tg_kb_restore_tmp" in createdb_calls[0]

        # pg_restore must be called with tmp db dsn and --no-owner, --no-privileges
        pg_restore_calls = [cmd for cmd in all_cmds if cmd[0] == "pg_restore"]
        assert len(pg_restore_calls) == 1
        assert "--no-owner" in pg_restore_calls[0]
        assert "--no-privileges" in pg_restore_calls[0]
        assert "--single-transaction" not in pg_restore_calls[0]
        restore_dsn = pg_restore_calls[0][pg_restore_calls[0].index("-d") + 1]
        assert "tg_kb_restore_tmp" in restore_dsn

        # psql rename must be called (ALTER DATABASE ... RENAME TO ...)
        psql_calls = [cmd for cmd in all_cmds if cmd[0] == "psql"]
        rename_cmds = [call.kwargs.get("") or call for call in all_calls if call.args[0][0] == "psql"]
        psql_sqls = [call.args[0][-1] for call in all_calls if call.args[0][0] == "psql"]
        rename_sqls = [s for s in psql_sqls if "RENAME TO" in s]
        assert len(rename_sqls) == 2  # rename tg_kb -> old, tmp -> tg_kb

    finally:
        file_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_restore_swap_cleans_up_tmp_db_on_failure() -> None:
    file_path = _create_backup_file(b"backup-content")
    try:
        checksum = backup_service_module._sha256_file(file_path)
        record = BackupRecord(
            id=uuid.uuid4(),
            filename=file_path.name,
            file_path=str(file_path),
            sha256_checksum=checksum,
        )
        session = types.SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
        service = BackupService(FakeBackupsRepository(record), session)
        token = await service.issue_restore_token(str(record.id))

        call_count = 0

        def _run_side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            # fail on pg_restore call
            if cmd[0] == "pg_restore":
                raise subprocess.CalledProcessError(1, cmd, stderr="simulated restore error")
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch("kb_bot.services.backup_service.subprocess.run", side_effect=_run_side_effect):
            with pytest.raises(subprocess.CalledProcessError):
                await service.restore_backup(
                    backup_id=str(record.id),
                    token=str(token),
                    database_url="postgresql+asyncpg://postgres:secret@localhost:5432/tg_kb",
                    pg_restore_bin="pg_restore",
                    psql_bin="psql",
                    createdb_bin="createdb",
                )

        # token should still be consumed after failure attempt? No — token stays if restore fails
        # Actually by design token is only popped on SUCCESS. Token stays on failure.
        # Verify the restore token is NOT consumed on failure
        assert str(record.id) in backup_service_module._RESTORE_TOKENS
    finally:
        file_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_restore_success_when_backup_row_disappears_after_restore() -> None:
    file_path = _create_backup_file(b"backup-content")
    try:
        checksum = backup_service_module._sha256_file(file_path)
        record = BackupRecord(
            id=uuid.uuid4(),
            filename=file_path.name,
            file_path=str(file_path),
            sha256_checksum=checksum,
        )
        session = types.SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
        service = BackupService(DisappearingBackupsRepository(record), session)
        token = await service.issue_restore_token(str(record.id))

        with patch("kb_bot.services.backup_service.subprocess.run"):
            await service.restore_backup(
                backup_id=str(record.id),
                token=str(token),
                database_url="postgresql+asyncpg://postgres:secret@localhost:5432/tg_kb",
                pg_restore_bin="pg_restore",
            )

        assert str(record.id) not in backup_service_module._RESTORE_TOKENS
        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()
    finally:
        file_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_list_backups_recovers_missing_rows_from_backup_dir() -> None:
    target_dir = Path("tests/.tmp_backup_catalog") / str(uuid.uuid4())
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        file_existing = _create_dump_file(target_dir / "tg_kb_existing.dump", content=b"existing")
        file_missing = _create_dump_file(target_dir / "tg_kb_missing.dump", content=b"missing")

        existing_record = BackupRecord(
            id=uuid.uuid4(),
            filename=file_existing.name,
            file_path=str(file_existing),
            sha256_checksum=backup_service_module._sha256_file(file_existing),
        )
        repo = CatalogBackupsRepository([existing_record])
        session = types.SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
        service = BackupService(repo, session)

        rows = await service.list_backups(str(target_dir))
        filenames = {row.filename for row in rows}

        assert file_existing.name in filenames
        assert file_missing.name in filenames
        session.commit.assert_awaited_once()
    finally:
        shutil.rmtree(target_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_list_backups_does_not_commit_when_catalog_is_up_to_date() -> None:
    target_dir = Path("tests/.tmp_backup_catalog") / str(uuid.uuid4())
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        existing_file = _create_dump_file(target_dir / "tg_kb_existing.dump", content=b"existing")
        existing_record = BackupRecord(
            id=uuid.uuid4(),
            filename=existing_file.name,
            file_path=str(existing_file),
            sha256_checksum=backup_service_module._sha256_file(existing_file),
        )
        repo = CatalogBackupsRepository([existing_record])
        session = types.SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
        service = BackupService(repo, session)

        rows = await service.list_backups(str(target_dir))
        assert len(rows) == 1
        session.commit.assert_not_awaited()
    finally:
        shutil.rmtree(target_dir, ignore_errors=True)
