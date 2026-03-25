import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kb_bot.db.orm.saved_view import SavedView


class SavedViewsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, view: SavedView) -> SavedView:
        self.session.add(view)
        await self.session.flush()
        await self.session.refresh(view)
        return view

    async def list_all(self) -> list[SavedView]:
        stmt = select(SavedView).order_by(SavedView.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, view_id: uuid.UUID) -> SavedView | None:
        stmt = select(SavedView).where(SavedView.id == view_id).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> SavedView | None:
        stmt = select(SavedView).where(SavedView.name == name).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

