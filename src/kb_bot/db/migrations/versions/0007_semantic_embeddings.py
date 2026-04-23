"""add semantic embeddings storage

Revision ID: 0007_semantic_embeddings
Revises: 0006_entry_topics
Create Date: 2026-04-22
"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "0007_semantic_embeddings"
down_revision = "0006_entry_topics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    vector_available = bool(
        bind.execute(text("SELECT EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector')")).scalar()
    )

    if vector_available:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        op.execute(
            """
            CREATE TABLE knowledge_entry_embeddings (
                entry_id UUID PRIMARY KEY REFERENCES knowledge_entries(id) ON DELETE CASCADE,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                embedding_dim INT NOT NULL,
                embedding VECTOR(1536) NOT NULL,
                content_hash TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
    else:
        # CI environments may not have pgvector installed; keep migration chain
        # runnable with a fallback type.
        op.execute(
            """
            CREATE TABLE knowledge_entry_embeddings (
                entry_id UUID PRIMARY KEY REFERENCES knowledge_entries(id) ON DELETE CASCADE,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                embedding_dim INT NOT NULL,
                embedding DOUBLE PRECISION[] NOT NULL,
                content_hash TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
    op.execute(
        """
        CREATE INDEX idx_entry_embeddings_provider_model
        ON knowledge_entry_embeddings (provider, model);
        """
    )
    op.execute(
        """
        CREATE INDEX idx_entry_embeddings_updated_at
        ON knowledge_entry_embeddings (updated_at);
        """
    )
    if vector_available:
        op.execute(
            """
            CREATE INDEX idx_entry_embeddings_vector_cosine
            ON knowledge_entry_embeddings
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
            """
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_entry_embeddings")
