"""create strategic initiative

Revision ID: a65f5faa4d9c
Revises: ff5673aa6d11
Create Date: 2025-10-21 07:29:31.733088

"""

from textwrap import dedent
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from src.config import settings

# revision identifiers, used by Alembic.
revision: str = "a65f5faa4d9c"
down_revision: Union[str, None] = "ff5673aa6d11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create strategic_initiatives table for linking initiatives to strategic context."""

    # Create strategic_initiatives table
    op.create_table(
        "strategic_initiatives",
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
            "initiative_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "pillar_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "theme_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("user_need", sa.Text(), nullable=True),
        sa.Column("connection_to_vision", sa.Text(), nullable=True),
        sa.Column("success_criteria", sa.Text(), nullable=True),
        sa.Column("out_of_scope", sa.Text(), nullable=True),
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
        # Check constraints for text field lengths
        sa.CheckConstraint(
            "user_need IS NULL OR char_length(user_need) <= 1000",
            name="ck_strategic_initiatives_user_need_length",
        ),
        sa.CheckConstraint(
            "connection_to_vision IS NULL OR char_length(connection_to_vision) <= 1000",
            name="ck_strategic_initiatives_connection_to_vision_length",
        ),
        sa.CheckConstraint(
            "success_criteria IS NULL OR char_length(success_criteria) <= 1000",
            name="ck_strategic_initiatives_success_criteria_length",
        ),
        sa.CheckConstraint(
            "out_of_scope IS NULL OR char_length(out_of_scope) <= 1000",
            name="ck_strategic_initiatives_out_of_scope_length",
        ),
        # Foreign keys
        sa.ForeignKeyConstraint(
            ["initiative_id"],
            ["dev.initiative.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dev.workspace.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pillar_id"],
            ["dev.strategic_pillars.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["theme_id"],
            ["dev.roadmap_themes.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "initiative_id", name="uq_strategic_initiatives_initiative_id"
        ),
        schema="dev",
    )

    # Enable RLS and create policy
    op.execute(
        dedent(
            f"""
            ALTER TABLE dev.strategic_initiatives ENABLE ROW LEVEL SECURITY;

            CREATE POLICY strategic_initiatives_policy ON dev.strategic_initiatives
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt());

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.strategic_initiatives TO {settings.postgrest_authenticated_role};
            """
        )
    )

    # Create indexes
    op.create_index(
        "ix_strategic_initiatives_workspace_id",
        "strategic_initiatives",
        ["workspace_id"],
        schema="dev",
    )

    op.create_index(
        "ix_strategic_initiatives_initiative_id",
        "strategic_initiatives",
        ["initiative_id"],
        unique=True,
        schema="dev",
    )

    op.create_index(
        "ix_strategic_initiatives_pillar_id",
        "strategic_initiatives",
        ["pillar_id"],
        schema="dev",
    )

    op.create_index(
        "ix_strategic_initiatives_theme_id",
        "strategic_initiatives",
        ["theme_id"],
        schema="dev",
    )


def downgrade() -> None:
    """Drop strategic_initiatives table."""

    # Drop indexes
    op.drop_index(
        "ix_strategic_initiatives_theme_id",
        table_name="strategic_initiatives",
        schema="dev",
    )

    op.drop_index(
        "ix_strategic_initiatives_pillar_id",
        table_name="strategic_initiatives",
        schema="dev",
    )

    op.drop_index(
        "ix_strategic_initiatives_initiative_id",
        table_name="strategic_initiatives",
        schema="dev",
    )

    op.drop_index(
        "ix_strategic_initiatives_workspace_id",
        table_name="strategic_initiatives",
        schema="dev",
    )

    # Drop table (RLS policy will be automatically dropped)
    op.drop_table("strategic_initiatives", schema="dev")
