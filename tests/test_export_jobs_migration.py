from pathlib import Path


def test_export_jobs_migration_exists() -> None:
    path = Path("src/kb_bot/db/migrations/versions/0004_export_jobs.py")
    content = path.read_text(encoding="utf-8")
    assert "CREATE TABLE export_jobs" in content
    assert "export_format TEXT NOT NULL" in content

