from __future__ import annotations

import base64
from datetime import UTC, datetime
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kb_bot import __version__
from kb_bot.core.config import Settings, get_settings
from kb_bot.core.list_parsing import ListFilters
from kb_bot.db.engine import create_engine
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.jobs import JobsRepository
from kb_bot.db.session import create_session_factory
from kb_bot.services.export_service import ExportService


class HealthResponse(BaseModel):
    status: str
    app_version: str
    db_ok: bool
    alembic_revision: str | None
    checked_at: str


class ExportRequest(BaseModel):
    export_format: str = Field(default="json", pattern="^(json|csv)$")
    status_name: str | None = None
    topic_id: str | None = None
    limit: int = Field(default=20, ge=1, le=50)
    include_file_base64: bool = False


class ExportResponse(BaseModel):
    job_id: str
    export_format: str
    total_records: int
    stored_file: str
    content_base64: str | None = None


def _ensure_admin_token(settings: Settings, token: str | None) -> None:
    expected = settings.admin_api_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_API_TOKEN is not configured.",
        )
    if token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token.")


def create_admin_app(
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    engine = None
    if session_factory is None:
        engine = create_engine(app_settings.database_url)
        session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def _lifespan(_: FastAPI):
        yield
        if engine is not None:
            await engine.dispose()

    app = FastAPI(title="telegram-kb-bot admin", version=__version__, lifespan=_lifespan)

    def _get_settings() -> Settings:
        return app_settings

    async def _get_session() -> AsyncSession:
        async with session_factory() as session:
            yield session

    @app.get("/health", response_model=HealthResponse)
    async def health(
        session: AsyncSession = Depends(_get_session),
    ) -> HealthResponse:
        db_ok = False
        revision: str | None = None

        try:
            await session.execute(text("SELECT 1"))
            db_ok = True
            revision_row = await session.execute(text("SELECT version_num FROM alembic_version"))
            revision = revision_row.scalar_one_or_none()
        except Exception:
            db_ok = False

        overall_status = "ok" if db_ok else "degraded"
        checked_at = datetime.now(UTC).isoformat()
        return HealthResponse(
            status=overall_status,
            app_version=__version__,
            db_ok=db_ok,
            alembic_revision=revision,
            checked_at=checked_at,
        )

    @app.post("/export", response_model=ExportResponse)
    async def trigger_export(
        payload: ExportRequest,
        session: AsyncSession = Depends(_get_session),
        local_settings: Settings = Depends(_get_settings),
        x_admin_token: str | None = Header(default=None),
    ) -> ExportResponse:
        _ensure_admin_token(local_settings, x_admin_token)

        topic_uuid = None
        if payload.topic_id:
            try:
                import uuid

                topic_uuid = uuid.UUID(payload.topic_id)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="topic_id must be UUID.",
                ) from exc

        filters = ListFilters(
            status_name=payload.status_name,
            topic_id=topic_uuid,
            limit=payload.limit,
        )
        service = ExportService(
            jobs_repo=JobsRepository(session),
            entries_repo=EntriesRepository(session),
            session=session,
        )
        result = await service.export_entries(export_format=payload.export_format, filters=filters)

        export_dir = Path(local_settings.admin_export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        stored_name = f"{timestamp}_{result.job_id}_{result.filename}"
        stored_path = export_dir / stored_name
        stored_path.write_bytes(result.content)

        encoded_content = None
        if payload.include_file_base64:
            encoded_content = base64.b64encode(result.content).decode("ascii")

        return ExportResponse(
            job_id=result.job_id,
            export_format=payload.export_format,
            total_records=result.total_records,
            stored_file=str(stored_path),
            content_base64=encoded_content,
        )

    return app
