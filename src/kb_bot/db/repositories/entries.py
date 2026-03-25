from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kb_bot.db.orm.entry import KnowledgeEntry


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

