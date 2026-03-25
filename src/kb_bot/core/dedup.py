import hashlib


def compute_dedup_hash(normalized_url: str | None, title: str, notes: str | None) -> str:
    if normalized_url:
        base = f"url:{normalized_url}"
    else:
        normalized_title = " ".join(title.split()).strip().lower()
        normalized_notes = " ".join((notes or "").split()).strip().lower()
        base = f"note:{normalized_title}|{normalized_notes}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

