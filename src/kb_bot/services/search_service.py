from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.domain.dto import EntryDTO


class SearchService:
    def __init__(self, entries_repo: EntriesRepository) -> None:
        self.entries_repo = entries_repo

    async def search(self, query: str, limit: int = 10) -> list[EntryDTO]:
        q = query.strip()
        if not q:
            return []

        rows = await self.entries_repo.search(q, limit=limit)
        return [
            EntryDTO(
                id=entry.id,
                title=entry.title,
                original_url=entry.original_url,
                normalized_url=entry.normalized_url,
                primary_topic_id=entry.primary_topic_id,
                status_name=status_name,
                notes=entry.notes,
                saved_date=entry.saved_date,
            )
            for entry, status_name in rows
        ]

