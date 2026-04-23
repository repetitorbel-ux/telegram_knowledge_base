import uuid

from sqlalchemy import exists, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from kb_bot.db.orm.entry import KnowledgeEntry
from kb_bot.db.orm.entry_topic import KnowledgeEntryTopic
from kb_bot.db.orm.status import Status
from kb_bot.db.orm.tag import KnowledgeEntryTag
from kb_bot.db.orm.topic import Topic


class EntriesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists_by_dedup_hash(self, dedup_hash: str) -> bool:
        stmt = select(KnowledgeEntry.id).where(KnowledgeEntry.dedup_hash == dedup_hash).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_dedup_hash_for_other(self, dedup_hash: str, entry_id: uuid.UUID) -> bool:
        stmt = (
            select(KnowledgeEntry.id)
            .where(KnowledgeEntry.dedup_hash == dedup_hash, KnowledgeEntry.id != entry_id)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def get(self, entry_id: uuid.UUID) -> KnowledgeEntry | None:
        stmt = select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_embedding(self, limit: int, offset: int = 0) -> list[KnowledgeEntry]:
        stmt = (
            select(KnowledgeEntry)
            .order_by(KnowledgeEntry.updated_at.desc(), KnowledgeEntry.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, entry: KnowledgeEntry) -> None:
        await self.session.delete(entry)
        await self.session.flush()

    async def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[tuple[KnowledgeEntry, str]]:
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
            .offset(offset)
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

    async def get_with_status_many(self, entry_ids: list[uuid.UUID]) -> list[tuple[KnowledgeEntry, str]]:
        if not entry_ids:
            return []
        stmt = (
            select(KnowledgeEntry, Status.display_name)
            .join(Status, Status.id == KnowledgeEntry.status_id)
            .where(KnowledgeEntry.id.in_(entry_ids))
        )
        result = await self.session.execute(stmt)
        rows = [(row[0], row[1]) for row in result.all()]
        by_id = {entry.id: (entry, status_name) for entry, status_name in rows}
        ordered: list[tuple[KnowledgeEntry, str]] = []
        for entry_id in entry_ids:
            pair = by_id.get(entry_id)
            if pair is not None:
                ordered.append(pair)
        return ordered

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

    async def list_secondary_topics(self, entry_id: uuid.UUID) -> list[Topic]:
        stmt = (
            select(Topic)
            .join(KnowledgeEntryTopic, KnowledgeEntryTopic.topic_id == Topic.id)
            .where(KnowledgeEntryTopic.entry_id == entry_id)
            .order_by(Topic.full_path.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_secondary_topic(self, entry_id: uuid.UUID, topic_id: uuid.UUID) -> None:
        stmt = (
            insert(KnowledgeEntryTopic)
            .values(entry_id=entry_id, topic_id=topic_id)
            .on_conflict_do_nothing(index_elements=["entry_id", "topic_id"])
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def remove_secondary_topic(self, entry_id: uuid.UUID, topic_id: uuid.UUID) -> bool:
        stmt = select(KnowledgeEntryTopic).where(
            KnowledgeEntryTopic.entry_id == entry_id,
            KnowledgeEntryTopic.topic_id == topic_id,
        )
        result = await self.session.execute(stmt)
        link = result.scalar_one_or_none()
        if link is None:
            return False
        await self.session.delete(link)
        await self.session.flush()
        return True

    async def get_entry_tag_ids(self, entry_id: uuid.UUID) -> set[uuid.UUID]:
        stmt = select(KnowledgeEntryTag.tag_id).where(KnowledgeEntryTag.entry_id == entry_id)
        result = await self.session.execute(stmt)
        return {row[0] for row in result.all()}

    async def get_tags_for_entries(self, entry_ids: list[uuid.UUID]) -> dict[uuid.UUID, set[uuid.UUID]]:
        if not entry_ids:
            return {}
        stmt = select(KnowledgeEntryTag.entry_id, KnowledgeEntryTag.tag_id).where(
            KnowledgeEntryTag.entry_id.in_(entry_ids)
        )
        result = await self.session.execute(stmt)
        tags_by_entry: dict[uuid.UUID, set[uuid.UUID]] = {}
        for entry_id, tag_id in result.all():
            tags = tags_by_entry.setdefault(entry_id, set())
            tags.add(tag_id)
        return tags_by_entry

    async def get_related_candidates(
        self,
        entry_id: uuid.UUID,
        limit: int,
    ) -> list[tuple[KnowledgeEntry, str, str]]:
        stmt = (
            select(KnowledgeEntry, Status.display_name, Topic.name)
            .join(Status, Status.id == KnowledgeEntry.status_id)
            .join(Topic, Topic.id == KnowledgeEntry.primary_topic_id)
            .where(KnowledgeEntry.id != entry_id)
            .order_by(KnowledgeEntry.saved_date.desc(), KnowledgeEntry.id.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def list_entries(
        self,
        status_name: str | None = None,
        topic_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[tuple[KnowledgeEntry, str, str]]:
        stmt = (
            select(KnowledgeEntry, Status.display_name, Topic.name)
            .join(Status, Status.id == KnowledgeEntry.status_id)
            .join(Topic, Topic.id == KnowledgeEntry.primary_topic_id)
            .order_by(KnowledgeEntry.saved_date.desc())
            .offset(offset)
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

            secondary_topic = aliased(Topic)
            secondary_exists = exists(
                select(1)
                .select_from(KnowledgeEntryTopic)
                .join(secondary_topic, secondary_topic.id == KnowledgeEntryTopic.topic_id)
                .where(
                    KnowledgeEntryTopic.entry_id == KnowledgeEntry.id,
                    or_(
                        secondary_topic.full_path == selected_topic_path,
                        secondary_topic.full_path.like(f"{selected_topic_path}.%"),
                    ),
                )
            )
            stmt = stmt.where(
                or_(
                    Topic.full_path == selected_topic_path,
                    Topic.full_path.like(f"{selected_topic_path}.%"),
                    secondary_exists,
                )
            )

        result = await self.session.execute(stmt)
        return [(row[0], row[1], row[2]) for row in result.all()]
