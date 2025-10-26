"""create prioritise roadmap

Revision ID: 8fdf98a4b84f
Revises: a65f5faa4d9c
Create Date: 2025-10-24 18:17:27.139385

"""

from textwrap import dedent
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from src.config import settings

# revision identifiers, used by Alembic.
revision: str = "8fdf98a4b84f"
down_revision: Union[str, None] = "a65f5faa4d9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create prioritized_roadmaps table for Roadmap Intelligence Context."""

    # Create prioritized_roadmaps table
    op.create_table(
        "prioritized_roadmaps",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("private.get_user_id_from_jwt()"),
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "prioritized_theme_ids",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dev.workspace.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id", name="uq_prioritized_roadmaps_workspace_id"
        ),
        schema="dev",
    )

    # Add RLS policies and grants
    op.execute(
        dedent(
            f"""
            ALTER TABLE dev.prioritized_roadmaps ENABLE ROW LEVEL SECURITY;

            CREATE POLICY prioritized_roadmaps_policy ON dev.prioritized_roadmaps
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt());

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.prioritized_roadmaps TO {settings.postgrest_authenticated_role};
            """
        )
    )

    # Create index on workspace_id for faster lookups
    op.create_index(
        "ix_prioritized_roadmaps_workspace_id",
        "prioritized_roadmaps",
        ["workspace_id"],
        schema="dev",
    )


def downgrade() -> None:
    """Drop prioritized_roadmaps table."""

    # Drop index
    op.drop_index(
        "ix_prioritized_roadmaps_workspace_id",
        table_name="prioritized_roadmaps",
        schema="dev",
    )

    # Drop table
    op.drop_table("prioritized_roadmaps", schema="dev")
