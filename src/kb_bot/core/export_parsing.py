def parse_export_format(text: str | None) -> str:
    if not text:
        return "json"
    parts = text.split()
    if len(parts) < 2:
        return "json"
    fmt = parts[1].strip().lower()
    return fmt if fmt in {"json", "csv"} else "json"

