import re
from collections.abc import Iterable

URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def extract_first_url(text: str | None, *, entities: Iterable[object] | None = None) -> str | None:
    if entities:
        for entity in entities:
            entity_type = getattr(entity, "type", None)
            if hasattr(entity_type, "value"):
                entity_type = entity_type.value
            if str(entity_type).lower() != "text_link":
                continue

            entity_url = getattr(entity, "url", None)
            if entity_url:
                return str(entity_url).strip()

    if not text:
        return None
    match = URL_RE.search(text)
    if not match:
        return None
    return match.group(0).rstrip(".,)")


def build_forward_title(text: str | None) -> str:
    if not text:
        return "Forwarded message"
    compact = " ".join(text.split()).strip()
    if not compact:
        return "Forwarded message"
    return compact[:80]


def build_forward_notes(text: str | None, origin_repr: str | None) -> str | None:
    parts = []
    if origin_repr:
        parts.append(f"origin: {origin_repr}")
    if text:
        parts.append(text.strip())
    if not parts:
        return None
    return "\n\n".join(parts)
