from pathlib import Path


def test_saved_views_migration_exists() -> None:
    path = Path("src/kb_bot/db/migrations/versions/0002_saved_views.py")
    content = path.read_text(encoding="utf-8")
    assert "CREATE TABLE saved_views" in content
    assert "filter_snapshot JSONB" in content

