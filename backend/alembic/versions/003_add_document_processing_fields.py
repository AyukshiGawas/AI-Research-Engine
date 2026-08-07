"""Add document processing fields.

Revision ID: 003_add_document_processing_fields
Revises: 002_add_documents_table
Create Date: 2026-08-07 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_add_document_processing_fields"
down_revision: Union[str, None] = "002_add_documents_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("extracted_text", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("processing_error", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("word_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "word_count")
    op.drop_column("documents", "page_count")
    op.drop_column("documents", "processing_error")
    op.drop_column("documents", "extracted_text")
    op.drop_column("documents", "processed_at")
