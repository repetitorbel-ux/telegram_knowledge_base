from pathlib import Path


def test_semantic_embeddings_migration_contains_required_schema() -> None:
    migration_path = Path("src/kb_bot/db/migrations/versions/0007_semantic_embeddings.py")
    content = migration_path.read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS vector;" in content
    assert "CREATE TABLE knowledge_entry_embeddings" in content
    assert "embedding VECTOR(1536) NOT NULL" in content
    assert "CREATE INDEX idx_entry_embeddings_provider_model" in content
    assert "USING ivfflat (embedding vector_cosine_ops)" in content
    assert "DROP TABLE IF EXISTS knowledge_entry_embeddings" in content

