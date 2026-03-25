import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kb_bot.db.orm.topic import Topic


class TopicsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, topic_id: uuid.UUID) -> Topic | None:
        stmt = select(Topic).where(Topic.id == topic_id, Topic.is_active.is_(True)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tree(self) -> list[Topic]:
        stmt = (
            select(Topic)
            .where(Topic.is_active.is_(True))
            .order_by(Topic.full_path.asc(), Topic.sort_order.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, topic: Topic) -> Topic:
        self.session.add(topic)
        await self.session.flush()
        await self.session.refresh(topic)
        return topic

    async def get_by_full_path(self, full_path: str) -> Topic | None:
        stmt = select(Topic).where(Topic.full_path == full_path).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Topic | None:
        stmt = select(Topic).where(Topic.name == name, Topic.is_active.is_(True)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_descendants(self, prefix: str) -> list[Topic]:
        stmt = select(Topic).where(Topic.full_path.like(f"{prefix}.%"))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
