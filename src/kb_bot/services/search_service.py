import re
import uuid
from difflib import SequenceMatcher

from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.domain.dto import EntryDTO, RelatedEntryDTO
from kb_bot.domain.errors import EntryNotFoundError


class SearchService:
    def __init__(self, entries_repo: EntriesRepository) -> None:
        self.entries_repo = entries_repo

    async def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[EntryDTO]:
        q = query.strip()
        if not q:
            return []

        rows = await self.entries_repo.search(q, limit=limit, offset=offset)
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

    async def related(
        self,
        entry_id: uuid.UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> list[RelatedEntryDTO]:
        source_entry = await self.entries_repo.get(entry_id)
        if source_entry is None:
            raise EntryNotFoundError

        if limit <= 0:
            return []
        if offset < 0:
            offset = 0

        source_tags = await self.entries_repo.get_entry_tag_ids(entry_id)
        candidate_limit = min(max(limit + offset + 50, 100), 500)
        candidates = await self.entries_repo.get_related_candidates(entry_id, limit=candidate_limit)
        candidate_ids = [entry.id for entry, _, _ in candidates]
        tags_by_entry = await self.entries_repo.get_tags_for_entries(candidate_ids)

        scored: list[RelatedEntryDTO] = []
        for entry, status_name, topic_name in candidates:
            same_topic = entry.primary_topic_id == source_entry.primary_topic_id
            same_topic_points = 5 if same_topic else 0

            shared_tags_count = len(source_tags & tags_by_entry.get(entry.id, set()))
            shared_tags_points = min(shared_tags_count * 3, 9)

            title_similarity_points = _title_similarity_points(source_entry.title, entry.title)
            text_overlap_points = _text_overlap_points(
                f"{source_entry.description or ''} {source_entry.notes or ''}",
                f"{entry.description or ''} {entry.notes or ''}",
            )

            score = same_topic_points + shared_tags_points + title_similarity_points + text_overlap_points
            if score <= 0:
                continue

            scored.append(
                RelatedEntryDTO(
                    id=entry.id,
                    title=entry.title,
                    status_name=status_name,
                    topic_name=topic_name,
                    score=score,
                    same_topic=same_topic,
                    shared_tags_count=shared_tags_count,
                    title_similarity_points=title_similarity_points,
                    text_overlap_points=text_overlap_points,
                    saved_date=entry.saved_date,
                )
            )

        scored.sort(
            key=lambda item: (
                -item.score,
                -item.saved_date.timestamp(),
                item.title.lower(),
            )
        )
        return scored[offset : offset + limit]


def _title_similarity_points(source_title: str, candidate_title: str) -> int:
    source = (source_title or "").strip().lower()
    candidate = (candidate_title or "").strip().lower()
    if not source or not candidate:
        return 0
    ratio = SequenceMatcher(a=source, b=candidate).ratio()
    return min(int(round(ratio * 3)), 3)


_TOKEN_RE = re.compile(r"[a-zA-Z0-9_]{3,}")


def _text_overlap_points(source_text: str, candidate_text: str) -> int:
    source_tokens = set(_TOKEN_RE.findall((source_text or "").lower()))
    candidate_tokens = set(_TOKEN_RE.findall((candidate_text or "").lower()))
    if not source_tokens or not candidate_tokens:
        return 0

    overlap_count = len(source_tokens & candidate_tokens)
    if overlap_count <= 0:
        return 0
    ratio = overlap_count / max(1, len(source_tokens))
    return min(int(round(ratio * 3)), 3)
