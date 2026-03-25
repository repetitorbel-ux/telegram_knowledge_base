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

