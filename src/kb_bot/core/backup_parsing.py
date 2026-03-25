import uuid


def parse_single_uuid_arg(text: str | None) -> uuid.UUID | None:
    if not text:
        return None
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    try:
        return uuid.UUID(parts[1].strip())
    except ValueError:
        return None


def parse_restore_args(text: str | None) -> tuple[uuid.UUID | None, str | None]:
    if not text:
        return None, None
    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        return None, None
    try:
        backup_id = uuid.UUID(parts[1].strip())
    except ValueError:
        return None, None
    token = parts[2].strip()
    return backup_id, token or None

