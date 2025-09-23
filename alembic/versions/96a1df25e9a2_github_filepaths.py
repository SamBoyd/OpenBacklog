"""github filepaths

Revision ID: 96a1df25e9a2
Revises: 33ed869554e2
Create Date: 2025-09-19 11:42:25.459929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '96a1df25e9a2'
down_revision: Union[str, None] = '33ed869554e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create repository_file_index table for GitHub file autocomplete
    op.create_table(
        "repository_file_index",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("github_installation_id", sa.UUID(), nullable=False),
        sa.Column("repository_full_name", sa.String(), nullable=False),
        sa.Column("file_search_string", sa.Text(), nullable=False),
        sa.Column("last_indexed_commit_sha", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(
            ["github_installation_id"],
            ["private.github_installation.id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_installation_id", "repository_full_name"),
        schema="private",
    )

    # Create indexes for performance
    op.create_index(
        "ix_repository_file_index_github_installation_id",
        "repository_file_index",
        ["github_installation_id"],
        schema="private",
    )
    op.create_index(
        "ix_repository_file_index_repository_full_name",
        "repository_file_index",
        ["repository_full_name"],
        schema="private",
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index(
        "ix_repository_file_index_repository_full_name",
        table_name="repository_file_index",
        schema="private",
    )
    op.drop_index(
        "ix_repository_file_index_github_installation_id",
        table_name="repository_file_index",
        schema="private",
    )

    # Drop the table
    op.drop_table("repository_file_index", schema="private")
