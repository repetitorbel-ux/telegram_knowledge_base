from pathlib import Path


def test_initial_migration_contains_required_entities() -> None:
    migration_path = Path("src/kb_bot/db/migrations/versions/0001_init.py")
    content = migration_path.read_text(encoding="utf-8")

    assert "CREATE TABLE statuses" in content
    assert "CREATE TABLE topics" in content
    assert "CREATE TABLE knowledge_entries" in content
    assert "CREATE TABLE tags" in content
    assert "CREATE TABLE knowledge_entry_tags" in content

    for name in ["New", "To Read", "Important", "Archive", "Verified", "Outdated"]:
        assert name in content

    for topic in [
        "Java",
        "Git",
        "Neural Networks / AI",
        "Infrastructure",
        "Useful Channels",
        "Learning",
    ]:
        assert topic in content

