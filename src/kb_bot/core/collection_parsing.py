import uuid


def parse_collection_add_name(text: str | None) -> str | None:
    if not text:
        return None
    parts = text.split()
    if len(parts) < 2:
        return None
    return parts[1].strip()


def parse_collection_run_id(text: str | None) -> uuid.UUID | None:
    if not text:
        return None
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    try:
        return uuid.UUID(parts[1].strip())
    except ValueError:
        return None

