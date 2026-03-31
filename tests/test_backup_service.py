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
            )

        session.commit.assert_awaited_once()
        session.rollback.assert_awaited_once()
        assert record.restore_tested_at is not None
        assert str(record.id) not in backup_service_module._RESTORE_TOKENS

        command = run_mock.call_args.args[0]
        timeout = run_mock.call_args.kwargs.get("timeout")
        capture_output = run_mock.call_args.kwargs.get("capture_output")
        text_mode = run_mock.call_args.kwargs.get("text")
        assert "--single-transaction" in command
        assert "--no-owner" in command
        assert "--no-privileges" in command
        assert timeout == 1800
        assert capture_output is True
        assert text_mode is True
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
