from pathlib import Path


def test_entry_topics_migration_contains_required_table() -> None:
    migration_path = Path("src/kb_bot/db/migrations/versions/0006_entry_topics.py")
    content = migration_path.read_text(encoding="utf-8")

    assert "CREATE TABLE knowledge_entry_topics" in content
    assert "PRIMARY KEY (entry_id, topic_id)" in content
    assert "DROP TABLE IF EXISTS knowledge_entry_topics" in content

