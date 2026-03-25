import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from kb_bot.db.orm.entry import KnowledgeEntry
from kb_bot.db.orm.status import Status


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
