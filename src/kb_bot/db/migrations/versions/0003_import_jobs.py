"""add import jobs table

Revision ID: 0003_import_jobs
Revises: 0002_saved_views
Create Date: 2026-03-25
"""

from alembic import op

revision = "0003_import_jobs"
down_revision = "0002_saved_views"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE import_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_filename TEXT NULL,
            source_format TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            total_records INT NOT NULL DEFAULT 0,
            imported_records INT NOT NULL DEFAULT 0,
            duplicate_records INT NOT NULL DEFAULT 0,
            error_records INT NOT NULL DEFAULT 0,
            error_details TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS import_jobs")

