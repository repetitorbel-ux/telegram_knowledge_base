from kb_bot.core.dedup import compute_dedup_hash


def test_dedup_hash_same_for_same_normalized_url() -> None:
    h1 = compute_dedup_hash("https://example.com/a", "Title", None)
    h2 = compute_dedup_hash("https://example.com/a", "Other title", "notes")
    assert h1 == h2


def test_dedup_hash_note_mode_changes_with_content() -> None:
    h1 = compute_dedup_hash(None, "Some note", "A")
    h2 = compute_dedup_hash(None, "Some note", "B")
    assert h1 != h2

