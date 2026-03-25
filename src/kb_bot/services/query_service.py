import uuid
from dataclasses import dataclass

from kb_bot.db.repositories.entries import EntriesRepository


@dataclass(slots=True)
class EntryDetail:
    entry_id: uuid.UUID
    title: str
    status_name: str
    topic_name: str
    original_url: str | None
    normalized_url: str | None
    notes: str | None


class QueryService:
    def __init__(self, entries_repo: EntriesRepository) -> None:
        self.entries_repo = entries_repo

    async def get_entry_detail(self, entry_id: uuid.UUID) -> EntryDetail | None:
        row = await self.entries_repo.get_detail(entry_id)
        if row is None:
            return None
        entry, status_name, topic_name = row
        return EntryDetail(
            entry_id=entry.id,
            title=entry.title,
            status_name=status_name,
            topic_name=topic_name,
            original_url=entry.original_url,
            normalized_url=entry.normalized_url,
            notes=entry.notes,
        )

    async def list_entries(
        self,
        status_name: str | None = None,
        topic_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[EntryDetail]:
        rows = await self.entries_repo.list_entries(status_name=status_name, topic_id=topic_id, limit=limit)
        return [
            EntryDetail(
                entry_id=entry.id,
                title=entry.title,
                status_name=status,
                topic_name=topic_name,
                original_url=entry.original_url,
                normalized_url=entry.normalized_url,
                notes=entry.notes,
            )
            for entry, status, topic_name in rows
        ]

