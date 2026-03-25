import re

URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def extract_first_url(text: str | None) -> str | None:
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

