from pathlib import Path


def test_backup_records_migration_exists() -> None:
    path = Path("src/kb_bot/db/migrations/versions/0005_backup_records.py")
    content = path.read_text(encoding="utf-8")
    assert "CREATE TABLE backup_records" in content
    assert "sha256_checksum TEXT NOT NULL" in content

