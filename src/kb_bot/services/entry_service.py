import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from kb_bot.core.dedup import compute_dedup_hash
from kb_bot.core.url_normalization import normalize_url
from kb_bot.db.orm.entry import KnowledgeEntry
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.statuses import StatusesRepository
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.dto import EntryDTO
from kb_bot.domain.errors import (
    DuplicateEntryError,
    EntryNotFoundError,
    InvalidStatusTransitionError,
    StatusNotFoundError,
    TopicNotFoundError,
)
from kb_bot.domain.status_machine import can_transition


@dataclass(slots=True)
class CreateManualEntryPayload:
    title: str
    primary_topic_id: uuid.UUID
    original_url: str | None = None
    notes: str | None = None
    description: str | None = None
    status_code: str | None = None


class EntryService:
    def __init__(
        self,
        session: AsyncSession,
        entries_repo: EntriesRepository,
        topics_repo: TopicsRepository,
        statuses_repo: StatusesRepository,
    ) -> None:
        self.session = session
        self.entries_repo = entries_repo
        self.topics_repo = topics_repo
        self.statuses_repo = statuses_repo

    async def create_manual(self, payload: CreateManualEntryPayload) -> EntryDTO:
        title = payload.title.strip()
        if not title:
            raise ValueError("title is required")

        topic = await self.topics_repo.get(payload.primary_topic_id)
        if topic is None:
            raise TopicNotFoundError("topic not found")

        normalized_url = normalize_url(payload.original_url)
        dedup_hash = compute_dedup_hash(normalized_url, title, payload.notes)
        if await self.entries_repo.exists_by_dedup_hash(dedup_hash):
            raise DuplicateEntryError(dedup_hash)

        status = None
        if payload.status_code:
            status = await self.statuses_repo.get_by_code(payload.status_code)
        if status is None:
            status = await self.statuses_repo.get_by_code("NEW")
        if status is None:
            status = await self.statuses_repo.get_by_display_name("New")
        if status is None:
            raise RuntimeError("Default status 'New' is not seeded")

        entry = KnowledgeEntry(
            title=title,
            original_url=payload.original_url,
            normalized_url=normalized_url,
            description=payload.description,
            notes=payload.notes,
            primary_topic_id=payload.primary_topic_id,
            status_id=status.id,
            dedup_hash=dedup_hash,
        )
        await self.entries_repo.create(entry)
        await self.session.commit()
        await self.session.refresh(entry)

        return EntryDTO(
            id=entry.id,
            title=entry.title,
            original_url=entry.original_url,
            normalized_url=entry.normalized_url,
            primary_topic_id=entry.primary_topic_id,
            status_name=status.display_name,
            notes=entry.notes,
            saved_date=entry.saved_date,
        )

    async def set_status(self, entry_id: uuid.UUID, target_status_name: str) -> EntryDTO:
        row = await self.entries_repo.get_with_status(entry_id)
        if row is None:
            raise EntryNotFoundError("entry not found")
        entry, current_status_name = row

        target_status = await self.statuses_repo.get_by_display_name(target_status_name)
        if target_status is None:
            raise StatusNotFoundError("status not found")

        if not can_transition(current_status_name, target_status.display_name):
            raise InvalidStatusTransitionError(
                f"Transition {current_status_name} -> {target_status.display_name} is not allowed"
            )

        entry.status_id = target_status.id
        await self.session.commit()
        await self.session.refresh(entry)

        return EntryDTO(
            id=entry.id,
            title=entry.title,
            original_url=entry.original_url,
            normalized_url=entry.normalized_url,
            primary_topic_id=entry.primary_topic_id,
            status_name=target_status.display_name,
            notes=entry.notes,
            saved_date=entry.saved_date,
        )

    async def delete(self, entry_id: uuid.UUID) -> None:
        entry = await self.entries_repo.get(entry_id)
        if entry is None:
            raise EntryNotFoundError("entry not found")
        await self.entries_repo.delete(entry)
        await self.session.commit()

    async def move_to_topic(self, entry_id: uuid.UUID, target_topic_id: uuid.UUID) -> EntryDTO:
        row = await self.entries_repo.get_with_status(entry_id)
        if row is None:
            raise EntryNotFoundError("entry not found")
        entry, current_status_name = row

        topic = await self.topics_repo.get(target_topic_id)
        if topic is None:
            raise TopicNotFoundError("topic not found")

        entry.primary_topic_id = topic.id
        await self.session.commit()
        await self.session.refresh(entry)

        return EntryDTO(
            id=entry.id,
            title=entry.title,
            original_url=entry.original_url,
            normalized_url=entry.normalized_url,
            primary_topic_id=entry.primary_topic_id,
            status_name=current_status_name,
            notes=entry.notes,
            saved_date=entry.saved_date,
        )
