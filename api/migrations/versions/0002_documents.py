"""create documents table

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-26

"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("kommune", sa.String(), nullable=False),
        sa.Column("utvalg", sa.String(), nullable=False),
        sa.Column("moetedato", sa.Date(), nullable=False),
        sa.Column("dokumenttype", sa.String(), nullable=False),
        sa.Column("tittel", sa.String(), nullable=False),
        sa.Column("saksnummer", sa.String(), nullable=True),
        sa.Column("kilde_url", sa.String(), nullable=False),
        sa.Column("local_path", sa.String(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
    )
    op.create_unique_constraint("uq_documents_external_id", "documents", ["external_id"])


def downgrade() -> None:
    op.drop_table("documents")
