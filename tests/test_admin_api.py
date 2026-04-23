import base64
import asyncio
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from kb_bot.main import _patch_windows_socketpair_if_needed
from kb_bot.admin_api import app as admin_app_module
from kb_bot.admin_api.app import create_admin_app
from kb_bot.core.config import Settings
from kb_bot.services.export_service import ExportResult

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    _patch_windows_socketpair_if_needed()


class _FakeScalarResult:
    def __init__(self, value: str | None) -> None:
        self._value = value

    def scalar_one_or_none(self) -> str | None:
        return self._value


class _HealthSession:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    async def execute(self, statement: Any) -> _FakeScalarResult:
        sql = str(statement)
        if self.fail:
            raise RuntimeError("db down")
        if "alembic_version" in sql:
            return _FakeScalarResult("0006_entry_topics")
        return _FakeScalarResult(None)


class _SessionContext:
    def __init__(self, session: _HealthSession) -> None:
        self._session = session

    async def __aenter__(self) -> _HealthSession:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _SessionFactory:
    def __init__(self, session: _HealthSession) -> None:
        self._session = session

    def __call__(self) -> _SessionContext:
        return _SessionContext(self._session)


def _make_settings(temp_dir: Path) -> Settings:
    return Settings.model_construct(
        telegram_bot_token="test-token",
        telegram_allowed_user_id=1,
        database_url="postgresql+asyncpg://u:p@127.0.0.1:5432/db",
        backup_dir="backups",
        pg_dump_bin="pg_dump",
        pg_restore_bin="pg_restore",
        restore_timeout_sec=1800,
        admin_api_enabled=True,
        admin_api_host="127.0.0.1",
        admin_api_port=8080,
        admin_api_token="secret-token",
        admin_export_dir=str(temp_dir / "exports"),
    )


def _make_local_temp_dir() -> Path:
    path = Path(".pytest_tmp_admin") / str(uuid.uuid4())
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_health_reports_ok() -> None:
    temp_dir = _make_local_temp_dir()
    app = create_admin_app(
        session_factory=_SessionFactory(_HealthSession()),
        settings=_make_settings(temp_dir),
    )
    with TestClient(app) as client:
        response = client.get("/health")
    shutil.rmtree(temp_dir, ignore_errors=True)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["db_ok"] is True
    assert payload["alembic_revision"] == "0006_entry_topics"


def test_health_reports_degraded_when_db_fails() -> None:
    temp_dir = _make_local_temp_dir()
    app = create_admin_app(
        session_factory=_SessionFactory(_HealthSession(fail=True)),
        settings=_make_settings(temp_dir),
    )
    with TestClient(app) as client:
        response = client.get("/health")
    shutil.rmtree(temp_dir, ignore_errors=True)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["db_ok"] is False


def test_export_requires_token() -> None:
    temp_dir = _make_local_temp_dir()
    app = create_admin_app(
        session_factory=_SessionFactory(_HealthSession()),
        settings=_make_settings(temp_dir),
    )
    with TestClient(app) as client:
        response = client.post("/export", json={"export_format": "json"})
    shutil.rmtree(temp_dir, ignore_errors=True)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid admin token."


def test_export_returns_job_and_stored_file(monkeypatch) -> None:
    class _FakeExportService:
        def __init__(self, jobs_repo, entries_repo, session) -> None:
            pass

        async def export_entries(self, export_format, filters) -> ExportResult:
            assert export_format == "csv"
            assert filters.limit == 5
            return ExportResult(
                job_id=str(uuid.uuid4()),
                filename="export.csv",
                content=b"id,title\n1,Example\n",
                total_records=1,
            )

    monkeypatch.setattr(admin_app_module, "ExportService", _FakeExportService)

    temp_dir = _make_local_temp_dir()
    app = create_admin_app(
        session_factory=_SessionFactory(_HealthSession()),
        settings=_make_settings(temp_dir),
    )
    with TestClient(app) as client:
        response = client.post(
            "/export",
            headers={"x-admin-token": "secret-token"},
            json={"export_format": "csv", "limit": 5, "include_file_base64": True},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["export_format"] == "csv"
    assert payload["total_records"] == 1
    assert base64.b64decode(payload["content_base64"]) == b"id,title\n1,Example\n"
    assert Path(payload["stored_file"]).exists()
    shutil.rmtree(temp_dir, ignore_errors=True)
