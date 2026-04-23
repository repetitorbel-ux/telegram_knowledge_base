"""set semantic embedding vector dim to 768 for local ollama mode

Revision ID: 0008_embedding_dim_768
Revises: 0007_semantic_embeddings
Create Date: 2026-04-23
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_embedding_dim_768"
down_revision = "0007_semantic_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_entry_embeddings_vector_cosine;")
    op.execute("TRUNCATE TABLE knowledge_entry_embeddings;")
    op.execute(
        """
        ALTER TABLE knowledge_entry_embeddings
        ALTER COLUMN embedding TYPE vector(768)
        USING embedding::vector(768);
        """
    )
    op.execute(
        """
        CREATE INDEX idx_entry_embeddings_vector_cosine
        ON knowledge_entry_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_entry_embeddings_vector_cosine;")
    op.execute("TRUNCATE TABLE knowledge_entry_embeddings;")
    op.execute(
        """
        ALTER TABLE knowledge_entry_embeddings
        ALTER COLUMN embedding TYPE vector(1536)
        USING embedding::vector(1536);
        """
    )
    op.execute(
        """
        CREATE INDEX idx_entry_embeddings_vector_cosine
        ON knowledge_entry_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        """
    )
