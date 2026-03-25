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
class TopicDTO:
    id: UUID
    name: str
    full_path: str
    level: int

