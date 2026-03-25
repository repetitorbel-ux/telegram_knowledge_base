"""add export jobs table

Revision ID: 0004_export_jobs
Revises: 0003_import_jobs
Create Date: 2026-03-25
"""

from alembic import op

revision = "0004_export_jobs"
down_revision = "0003_import_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE export_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            export_format TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            filter_snapshot TEXT NULL,
            total_records INT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS export_jobs")

