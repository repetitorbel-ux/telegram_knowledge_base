"""add backup records table

Revision ID: 0005_backup_records
Revises: 0004_export_jobs
Create Date: 2026-03-25
"""

from alembic import op

revision = "0005_backup_records"
down_revision = "0004_export_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE backup_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            sha256_checksum TEXT NOT NULL,
            restore_tested_at TIMESTAMPTZ NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS backup_records")

