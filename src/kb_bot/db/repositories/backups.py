import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kb_bot.db.orm.backup import BackupRecord


class BackupsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, record: BackupRecord) -> BackupRecord:
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def get(self, backup_id: uuid.UUID) -> BackupRecord | None:
        stmt = select(BackupRecord).where(BackupRecord.id == backup_id).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[BackupRecord]:
        stmt = select(BackupRecord).order_by(BackupRecord.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

