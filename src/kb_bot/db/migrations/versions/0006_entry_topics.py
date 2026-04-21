"""add knowledge_entry_topics for multi-topic support

Revision ID: 0006_entry_topics
Revises: 0005_backup_records
Create Date: 2026-04-21
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_entry_topics"
down_revision = "0005_backup_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE knowledge_entry_topics (
            entry_id UUID NOT NULL REFERENCES knowledge_entries(id) ON DELETE CASCADE,
            topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (entry_id, topic_id)
        );
        """
    )
    op.execute("CREATE INDEX idx_entry_topics_topic_id ON knowledge_entry_topics (topic_id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_entry_topics")

