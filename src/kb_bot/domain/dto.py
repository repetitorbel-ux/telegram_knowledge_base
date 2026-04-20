from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class EntryDTO:
    id: UUID
    title: str
    original_url: str | None
    normalized_url: str | None
    primary_topic_id: UUID
    status_name: str
    notes: str | None
    saved_date: datetime


@dataclass(slots=True)
class RelatedEntryDTO:
    id: UUID
    title: str
    status_name: str
    topic_name: str
    score: int
    same_topic: bool
    shared_tags_count: int
    title_similarity_points: int
    text_overlap_points: int
    saved_date: datetime


@dataclass(slots=True)
class TopicDTO:
    id: UUID
    name: str
    full_path: str
    level: int
