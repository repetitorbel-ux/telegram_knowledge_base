import uuid


def parse_status_command(text: str | None) -> tuple[uuid.UUID | None, str | None]:
    if not text:
        return None, None

    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        return None, None

    try:
        entry_id = uuid.UUID(parts[1].strip())
    except ValueError:
        return None, None

    status_name = parts[2].strip()
    if not status_name:
        return None, None

    return entry_id, status_name

