import tempfile
import types
import uuid
from collections.abc import Coroutine
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from kb_bot.db.orm.backup import BackupRecord
from kb_bot.services import backup_service as backup_service_module
from kb_bot.services.backup_service import BackupService


def run_coroutine(coroutine: Coroutine[object, object, object]) -> object:
    while True:
        try:
            coroutine.send(None)
        except StopIteration as done:
            return done.value


class FakeBackupsRepository:
    def __init__(self, record: BackupRecord) -> None:
        self._record = record

    async def get(self, backup_id: uuid.UUID) -> BackupRecord | None:
        if backup_id == self._record.id:
            return self._record
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


def test_restore_forbidden_for_protected_database() -> None:
    file_path = _create_backup_file(b"backup-content")
    try:
        checksum = backup_service_module._sha256_file(file_path)
        record = BackupRecord(
            id=uuid.uuid4(),
            filename=file_path.name,
            file_path=str(file_path),
            sha256_checksum=checksum,
        )
        service = BackupService(FakeBackupsRepository(record), types.SimpleNamespace(commit=AsyncMock()))
        token = run_coroutine(service.issue_restore_token(str(record.id)))

        with patch("kb_bot.services.backup_service.subprocess.run") as run_mock:
            with pytest.raises(ValueError, match="protected database"):
                run_coroutine(
                    service.restore_backup(
                        backup_id=str(record.id),
                        token=str(token),
                        database_url="postgresql+asyncpg://postgres:secret@localhost:5432/postgres",
                        pg_restore_bin="pg_restore",
                    )
                )

        run_mock.assert_not_called()
    finally:
        file_path.unlink(missing_ok=True)


def test_restore_rejects_checksum_mismatch() -> None:
    file_path = _create_backup_file(b"backup-content")
    try:
        record = BackupRecord(
            id=uuid.uuid4(),
            filename=file_path.name,
            file_path=str(file_path),
            sha256_checksum="0" * 64,
        )
        service = BackupService(FakeBackupsRepository(record), types.SimpleNamespace(commit=AsyncMock()))
        token = run_coroutine(service.issue_restore_token(str(record.id)))

        with patch("kb_bot.services.backup_service.subprocess.run") as run_mock:
            with pytest.raises(ValueError, match="checksum mismatch"):
                run_coroutine(
                    service.restore_backup(
                        backup_id=str(record.id),
                        token=str(token),
                        database_url="postgresql+asyncpg://postgres:secret@localhost:5432/tg_kb",
                        pg_restore_bin="pg_restore",
                    )
                )

        run_mock.assert_not_called()
    finally:
        file_path.unlink(missing_ok=True)


def test_restore_success_marks_tested_and_consumes_token() -> None:
    file_path = _create_backup_file(b"backup-content")
    try:
        checksum = backup_service_module._sha256_file(file_path)
        record = BackupRecord(
            id=uuid.uuid4(),
            filename=file_path.name,
            file_path=str(file_path),
            sha256_checksum=checksum,
        )
        session = types.SimpleNamespace(commit=AsyncMock())
        service = BackupService(FakeBackupsRepository(record), session)
        token = run_coroutine(service.issue_restore_token(str(record.id)))

        with patch("kb_bot.services.backup_service.subprocess.run") as run_mock:
            run_coroutine(
                service.restore_backup(
                    backup_id=str(record.id),
                    token=str(token),
                    database_url="postgresql+asyncpg://postgres:secret@localhost:5432/tg_kb",
                    pg_restore_bin="pg_restore",
                )
            )

        session.commit.assert_awaited_once()
        assert record.restore_tested_at is not None
        assert str(record.id) not in backup_service_module._RESTORE_TOKENS

        command = run_mock.call_args.args[0]
        assert "--single-transaction" in command
        assert "--no-owner" in command
        assert "--no-privileges" in command
    finally:
        file_path.unlink(missing_ok=True)
