from pathlib import Path


def test_import_jobs_migration_exists() -> None:
    path = Path("src/kb_bot/db/migrations/versions/0003_import_jobs.py")
    content = path.read_text(encoding="utf-8")
    assert "CREATE TABLE import_jobs" in content
    assert "source_format TEXT NOT NULL" in content

