import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kb_bot.db.orm.status import Status


class StatusesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_display_name(self, name: str) -> Status | None:
        stmt = select(Status).where(Status.display_name == name).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, status_id: uuid.UUID) -> Status | None:
        stmt = select(Status).where(Status.id == status_id).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
