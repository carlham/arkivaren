"""create employer, job_ad and sync_state

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-10

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employer",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("orgnr", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
    )
    op.create_table(
        "job_ad",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(36), nullable=False, unique=True),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("employer.id")),
        sa.Column("municipal", sa.String(100)),
        sa.Column("county", sa.String(100)),
        sa.Column("extent", sa.String(50)),
        sa.Column("sector", sa.String(50)),
        sa.Column("application_url", sa.Text()),
        sa.Column("application_deadline_text", sa.Text()),
        sa.Column("application_deadline", sa.Date()),
        sa.Column("occupation_categories", postgresql.JSONB()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("source_modified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_job_ad_status", "job_ad", ["status"])
    op.create_table(
        "sync_state",
        sa.Column("name", sa.String(50), primary_key=True),
        sa.Column("last_page_url", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("sync_state")
    op.drop_index("ix_job_ad_status", table_name="job_ad")
    op.drop_table("job_ad")
    op.drop_table("employer")
