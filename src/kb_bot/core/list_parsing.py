import uuid
from dataclasses import dataclass


@dataclass(slots=True)
class ListFilters:
    status_name: str | None
    topic_id: uuid.UUID | None
    limit: int


def parse_list_command(text: str | None) -> ListFilters:
    status_name: str | None = None
    topic_id: uuid.UUID | None = None
    limit = 20

    if not text:
        return ListFilters(status_name=status_name, topic_id=topic_id, limit=limit)

    parts = text.split()
    for part in parts[1:]:
        if part.startswith("status="):
            raw_status = part.removeprefix("status=").strip()
            if raw_status:
                status_name = raw_status.replace("_", " ")
        elif part.startswith("topic="):
            raw_topic = part.removeprefix("topic=").strip()
            try:
                topic_id = uuid.UUID(raw_topic)
            except ValueError:
                topic_id = None
        elif part.startswith("limit="):
            raw_limit = part.removeprefix("limit=").strip()
            try:
                parsed = int(raw_limit)
                limit = max(1, min(50, parsed))
            except ValueError:
                limit = 20

    return ListFilters(status_name=status_name, topic_id=topic_id, limit=limit)

