import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from kb_bot.db.orm.entry import KnowledgeEntry
from kb_bot.db.orm.status import Status
from kb_bot.db.orm.topic import Topic


class EntriesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists_by_dedup_hash(self, dedup_hash: str) -> bool:
        stmt = select(KnowledgeEntry.id).where(KnowledgeEntry.dedup_hash == dedup_hash).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def search(self, query: str, limit: int = 10) -> list[tuple[KnowledgeEntry, str]]:
        pattern = f"%{query.strip()}%"
        stmt = (
            select(KnowledgeEntry, Status.display_name)
            .join(Status, Status.id == KnowledgeEntry.status_id)
            .where(
                or_(
                    KnowledgeEntry.title.ilike(pattern),
                    KnowledgeEntry.description.ilike(pattern),
                    KnowledgeEntry.notes.ilike(pattern),
                )
            )
            .order_by(KnowledgeEntry.saved_date.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_with_status(self, entry_id: uuid.UUID) -> tuple[KnowledgeEntry, str] | None:
        stmt = (
            select(KnowledgeEntry, Status.display_name)
            .join(Status, Status.id == KnowledgeEntry.status_id)
            .where(KnowledgeEntry.id == entry_id)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if row is None:
            return None
        return row[0], row[1]

    async def get_detail(self, entry_id: uuid.UUID) -> tuple[KnowledgeEntry, str, str] | None:
        stmt = (
            select(KnowledgeEntry, Status.display_name, Topic.name)
            .join(Status, Status.id == KnowledgeEntry.status_id)
            .join(Topic, Topic.id == KnowledgeEntry.primary_topic_id)
            .where(KnowledgeEntry.id == entry_id)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if row is None:
            return None
        return row[0], row[1], row[2]

    async def list_entries(
        self,
        status_name: str | None = None,
        topic_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[tuple[KnowledgeEntry, str, str]]:
        stmt = (
            select(KnowledgeEntry, Status.display_name, Topic.name)
            .join(Status, Status.id == KnowledgeEntry.status_id)
            .join(Topic, Topic.id == KnowledgeEntry.primary_topic_id)
            .order_by(KnowledgeEntry.saved_date.desc())
            .limit(limit)
        )
        if status_name:
            stmt = stmt.where(Status.display_name == status_name)
        if topic_id:
            selected_topic_stmt = select(Topic.full_path).where(Topic.id == topic_id).limit(1)
            selected_topic_result = await self.session.execute(selected_topic_stmt)
            selected_topic_path = selected_topic_result.scalar_one_or_none()
            if selected_topic_path is None:
                return []
            stmt = stmt.where(
                or_(
                    Topic.full_path == selected_topic_path,
                    Topic.full_path.like(f"{selected_topic_path}.%"),
                )
            )

        result = await self.session.execute(stmt)
        return [(row[0], row[1], row[2]) for row in result.all()]
