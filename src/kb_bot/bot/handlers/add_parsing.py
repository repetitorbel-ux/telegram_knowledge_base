from urllib.parse import urlsplit


def parse_content_input(text: str) -> tuple[str | None, str | None]:
    candidate = text.strip()
    parts = urlsplit(candidate)
    if parts.scheme in {"http", "https"} and parts.netloc:
        return candidate, None
    return None, candidate

