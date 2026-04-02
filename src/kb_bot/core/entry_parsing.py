import uuid


def parse_entry_command(text: str | None) -> uuid.UUID | None:
    if not text:
        return None
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    try:
        return uuid.UUID(parts[1].strip())
    except ValueError:
        return None


def parse_entry_move_command(text: str | None) -> tuple[uuid.UUID, uuid.UUID] | None:
    if not text:
        return None
    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        return None
    try:
        entry_id = uuid.UUID(parts[1].strip())
        topic_id = uuid.UUID(parts[2].strip())
    except ValueError:
        return None
    return entry_id, topic_id
