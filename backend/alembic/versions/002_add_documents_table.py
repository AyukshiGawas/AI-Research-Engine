"""Add documents table for project document metadata.

Revision ID: 002_add_documents_table
Revises: 001_initial_phase2_tables
Create Date: 2026-08-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_add_documents_table"
down_revision: Union[str, None] = "001_initial_phase2_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("extension", sa.String(20), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("UPLOADED", "PROCESSING", "PROCESSED", "FAILED", name="document_status"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_foreign_key(
        "fk_documents_project_id_projects",
        "documents",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_documents_uploaded_by_users",
        "documents",
        "users",
        ["uploaded_by"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index("ix_documents_id", "documents", ["id"], unique=False)
    op.create_index("ix_documents_project_id", "documents", ["project_id"], unique=False)
    op.create_index("ix_documents_uploaded_by", "documents", ["uploaded_by"], unique=False)
    op.create_index("ix_documents_stored_filename", "documents", ["stored_filename"], unique=True)
    op.create_index("ix_documents_status", "documents", ["status"], unique=False)
    op.create_index("ix_documents_project_status", "documents", ["project_id", "status"], unique=False)
    op.create_index("ix_documents_uploaded_created", "documents", ["uploaded_by", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_documents_uploaded_created", table_name="documents")
    op.drop_index("ix_documents_project_status", table_name="documents")
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_stored_filename", table_name="documents")
    op.drop_index("ix_documents_uploaded_by", table_name="documents")
    op.drop_index("ix_documents_project_id", table_name="documents")
    op.drop_index("ix_documents_id", table_name="documents")

    op.drop_constraint("fk_documents_uploaded_by_users", "documents", type_="foreignkey")
    op.drop_constraint("fk_documents_project_id_projects", "documents", type_="foreignkey")
    op.drop_table("documents")

    op.execute("DROP TYPE IF EXISTS document_status")
