"""init schema for tg kb bot phase1

Revision ID: 0001_init
Revises:
Create Date: 2026-03-25
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS ltree")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute(
        """
        CREATE TABLE statuses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            sort_order INT NOT NULL,
            is_terminal BOOLEAN NOT NULL DEFAULT FALSE
        );
        """
    )

    op.execute(
        """
        CREATE TABLE topics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            parent_topic_id UUID NULL REFERENCES topics(id),
            full_path TEXT NOT NULL UNIQUE,
            full_path_ltree LTREE NOT NULL,
            level INT NOT NULL DEFAULT 0,
            sort_order INT NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_archived BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute("CREATE INDEX idx_topics_full_path_ltree_gist ON topics USING GIST (full_path_ltree)")

    op.execute(
        """
        CREATE TABLE tags (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            color_or_style_marker TEXT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    op.execute(
        """
        CREATE TABLE knowledge_entries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            original_url TEXT NULL,
            normalized_url TEXT NULL,
            title TEXT NOT NULL,
            description TEXT NULL,
            notes TEXT NULL,
            primary_topic_id UUID NOT NULL REFERENCES topics(id),
            status_id UUID NOT NULL REFERENCES statuses(id),
            dedup_hash TEXT NOT NULL UNIQUE,
            saved_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute("CREATE INDEX idx_entries_primary_topic ON knowledge_entries (primary_topic_id)")
    op.execute("CREATE INDEX idx_entries_status ON knowledge_entries (status_id)")
    op.execute("CREATE INDEX idx_entries_saved_date ON knowledge_entries (saved_date)")
    op.execute(
        "CREATE INDEX idx_entries_title_fts ON knowledge_entries USING GIN (to_tsvector('simple', coalesce(title, '')))"
    )
    op.execute(
        "CREATE INDEX idx_entries_title_trgm ON knowledge_entries USING GIN (title gin_trgm_ops)"
    )

    op.execute(
        """
        CREATE TABLE knowledge_entry_tags (
            entry_id UUID NOT NULL REFERENCES knowledge_entries(id) ON DELETE CASCADE,
            tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (entry_id, tag_id)
        );
        """
    )

    op.execute(
        """
        INSERT INTO statuses (code, display_name, description, sort_order, is_terminal) VALUES
        ('NEW',       'New',       'Captured but not triaged yet.',               10, FALSE),
        ('TO_READ',   'To Read',   'Queued to read/review later.',                20, FALSE),
        ('IMPORTANT', 'Important', 'High signal; prioritize and keep current.',   30, FALSE),
        ('VERIFIED',  'Verified',  'Validated as accurate and current.',          40, FALSE),
        ('ARCHIVE',   'Archive',   'No longer active but kept for reference.',    90, TRUE),
        ('OUTDATED',  'Outdated',  'Known to be obsolete or superseded.',         100, TRUE);
        """
    )

    op.execute(
        """
        INSERT INTO topics (name, slug, parent_topic_id, full_path, full_path_ltree, level, sort_order)
        VALUES
        ('Java',                 'java',               NULL, 'java',               'java',               0, 10),
        ('Git',                  'git',                NULL, 'git',                'git',                0, 20),
        ('Neural Networks / AI', 'neural_networks_ai', NULL, 'neural_networks_ai', 'neural_networks_ai', 0, 30),
        ('Infrastructure',       'infrastructure',     NULL, 'infrastructure',     'infrastructure',     0, 40),
        ('Useful Channels',      'useful_channels',    NULL, 'useful_channels',    'useful_channels',    0, 50),
        ('Learning',             'learning',           NULL, 'learning',           'learning',           0, 60);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_entry_tags")
    op.execute("DROP TABLE IF EXISTS knowledge_entries")
    op.execute("DROP TABLE IF EXISTS tags")
    op.execute("DROP TABLE IF EXISTS topics")
    op.execute("DROP TABLE IF EXISTS statuses")

