def parse_search_query(text: str | None) -> str:
    if not text:
        return ""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return ""
    return parts[1].strip()

