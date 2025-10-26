"""create strategic models

Revision ID: ff5673aa6d11
Revises: 4f25dc97c12b
Create Date: 2025-10-19 10:13:05.853382

"""

from textwrap import dedent
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from src.config import settings

# revision identifiers, used by Alembic.
revision: str = "ff5673aa6d11"
down_revision: Union[str, None] = "4f25dc97c12b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create strategic planning tables."""

    # Create workspace_vision table
    op.create_table(
        "workspace_vision",
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
        sa.Column("vision_text", sa.Text(), nullable=False),
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
        sa.CheckConstraint(
            "char_length(vision_text) <= 1000",
            name="ck_workspace_vision_text_length",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dev.workspace.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", name="uq_workspace_vision_workspace_id"),
        schema="dev",
    )

    op.execute(
        dedent(
            f"""
            ALTER TABLE dev.workspace_vision ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY workspace_vision_policy ON dev.workspace_vision
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt()); 

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.workspace_vision TO {settings.postgrest_authenticated_role};
            """
        )
    )

    op.create_index(
        "ix_workspace_vision_workspace_id",
        "workspace_vision",
        ["workspace_id"],
        schema="dev",
    )

    # Create strategic_pillars table
    op.create_table(
        "strategic_pillars",
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
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("anti_strategy", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
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
        sa.CheckConstraint(
            "char_length(description) <= 1000",
            name="ck_strategic_pillars_description_length",
        ),
        sa.CheckConstraint(
            "char_length(anti_strategy) <= 1000",
            name="ck_strategic_pillars_anti_strategy_length",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dev.workspace.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "name",
            name="uq_strategic_pillars_workspace_id_name",
        ),
        schema="dev",
    )

    op.execute(
        dedent(
            f"""
            ALTER TABLE dev.strategic_pillars ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY strategic_pillars_policy ON dev.strategic_pillars
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt()); 

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.strategic_pillars TO {settings.postgrest_authenticated_role};
            """
        )
    )

    op.create_index(
        "ix_strategic_pillars_workspace_id",
        "strategic_pillars",
        ["workspace_id"],
        schema="dev",
    )

    op.create_index(
        "ix_strategic_pillars_workspace_id_display_order",
        "strategic_pillars",
        ["workspace_id", "display_order"],
        schema="dev",
    )

    # Create product_outcomes table
    op.create_table(
        "product_outcomes",
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
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metrics", sa.Text(), nullable=True),
        sa.Column("time_horizon_months", sa.Integer(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
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
        sa.CheckConstraint(
            "description IS NULL OR char_length(description) <= 1500",
            name="ck_product_outcomes_description_length",
        ),
        sa.CheckConstraint(
            "metrics IS NULL OR char_length(metrics) <= 1000",
            name="ck_product_outcomes_metrics_length",
        ),
        sa.CheckConstraint(
            "time_horizon_months IS NULL OR (time_horizon_months >= 6 AND time_horizon_months <= 36)",
            name="ck_product_outcomes_time_horizon",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dev.workspace.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "name",
            name="uq_product_outcomes_workspace_id_name",
        ),
        schema="dev",
    )

    op.execute(
        dedent(
            f"""
            ALTER TABLE dev.product_outcomes ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY product_outcomes_policy ON dev.product_outcomes
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt()); 

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.product_outcomes TO {settings.postgrest_authenticated_role};
            """
        )
    )

    op.create_index(
        "ix_product_outcomes_workspace_id",
        "product_outcomes",
        ["workspace_id"],
        schema="dev",
    )

    op.create_index(
        "ix_product_outcomes_workspace_id_display_order",
        "product_outcomes",
        ["workspace_id", "display_order"],
        schema="dev",
    )

    # Create roadmap_themes table
    op.create_table(
        "roadmap_themes",
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
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=True),
        sa.Column("indicative_metrics", sa.Text(), nullable=True),
        sa.Column("time_horizon_months", sa.Integer(), nullable=True),
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
        sa.CheckConstraint(
            "char_length(problem_statement) > 0 AND char_length(problem_statement) <= 1500",
            name="ck_roadmap_themes_problem_statement_length",
        ),
        sa.CheckConstraint(
            "hypothesis IS NULL OR char_length(hypothesis) <= 1500",
            name="ck_roadmap_themes_hypothesis_length",
        ),
        sa.CheckConstraint(
            "indicative_metrics IS NULL OR char_length(indicative_metrics) <= 1000",
            name="ck_roadmap_themes_indicative_metrics_length",
        ),
        sa.CheckConstraint(
            "time_horizon_months IS NULL OR (time_horizon_months >= 0 AND time_horizon_months <= 12)",
            name="ck_roadmap_themes_time_horizon",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dev.workspace.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "name",
            name="uq_roadmap_themes_workspace_id_name",
        ),
        schema="dev",
    )

    op.execute(
        dedent(
            f"""
            ALTER TABLE dev.roadmap_themes ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY roadmap_themes_policy ON dev.roadmap_themes
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt()); 

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.roadmap_themes TO {settings.postgrest_authenticated_role};
            """
        )
    )

    op.create_index(
        "ix_roadmap_themes_workspace_id",
        "roadmap_themes",
        ["workspace_id"],
        schema="dev",
    )

    # Create outcome_pillar_links table (many-to-many)
    op.create_table(
        "outcome_pillar_links",
        sa.Column(
            "outcome_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("private.get_user_id_from_jwt()"),
        ),
        sa.Column(
            "pillar_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["outcome_id"],
            ["dev.product_outcomes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pillar_id"],
            ["dev.strategic_pillars.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("outcome_id", "pillar_id"),
        schema="dev",
    )

    op.execute(
        dedent(
            f"""
            ALTER TABLE dev.outcome_pillar_links ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY outcome_pillar_links_policy ON dev.outcome_pillar_links
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt()); 

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.outcome_pillar_links TO {settings.postgrest_authenticated_role};
            """
        )
    )

    op.create_index(
        "ix_outcome_pillar_links_outcome_id",
        "outcome_pillar_links",
        ["outcome_id"],
        schema="dev",
    )

    op.create_index(
        "ix_outcome_pillar_links_pillar_id",
        "outcome_pillar_links",
        ["pillar_id"],
        schema="dev",
    )

    # Create theme_outcome_links table (many-to-many)
    op.create_table(
        "theme_outcome_links",
        sa.Column(
            "theme_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("private.get_user_id_from_jwt()"),
        ),
        sa.Column(
            "outcome_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["theme_id"],
            ["dev.roadmap_themes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["outcome_id"],
            ["dev.product_outcomes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("theme_id", "outcome_id"),
        schema="dev",
    )

    op.execute(
        dedent(
            f"""
            ALTER TABLE dev.theme_outcome_links ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY theme_outcome_links_policy ON dev.theme_outcome_links
            USING (user_id = private.get_user_id_from_jwt())
            WITH CHECK (user_id = private.get_user_id_from_jwt()); 

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.theme_outcome_links TO {settings.postgrest_authenticated_role};
            """
        )
    )

    op.create_index(
        "ix_theme_outcome_links_theme_id",
        "theme_outcome_links",
        ["theme_id"],
        schema="dev",
    )

    op.create_index(
        "ix_theme_outcome_links_outcome_id",
        "theme_outcome_links",
        ["outcome_id"],
        schema="dev",
    )


def downgrade() -> None:
    """Drop strategic planning tables."""

    # Drop theme_outcome_links table
    op.drop_index(
        "ix_theme_outcome_links_outcome_id",
        table_name="theme_outcome_links",
        schema="dev",
    )

    op.drop_index(
        "ix_theme_outcome_links_theme_id",
        table_name="theme_outcome_links",
        schema="dev",
    )

    op.drop_table("theme_outcome_links", schema="dev")

    # Drop outcome_pillar_links table
    op.drop_index(
        "ix_outcome_pillar_links_pillar_id",
        table_name="outcome_pillar_links",
        schema="dev",
    )

    op.drop_index(
        "ix_outcome_pillar_links_outcome_id",
        table_name="outcome_pillar_links",
        schema="dev",
    )

    op.drop_table("outcome_pillar_links", schema="dev")

    # Drop roadmap_themes table
    op.drop_index(
        "ix_roadmap_themes_workspace_id",
        table_name="roadmap_themes",
        schema="dev",
    )

    op.drop_table("roadmap_themes", schema="dev")

    # Drop product_outcomes table
    op.drop_index(
        "ix_product_outcomes_workspace_id_display_order",
        table_name="product_outcomes",
        schema="dev",
    )

    op.drop_index(
        "ix_product_outcomes_workspace_id",
        table_name="product_outcomes",
        schema="dev",
    )

    op.drop_table("product_outcomes", schema="dev")

    # Drop strategic_pillars table
    op.drop_index(
        "ix_strategic_pillars_workspace_id_display_order",
        table_name="strategic_pillars",
        schema="dev",
    )

    op.drop_index(
        "ix_strategic_pillars_workspace_id",
        table_name="strategic_pillars",
        schema="dev",
    )

    op.drop_table("strategic_pillars", schema="dev")

    # Drop workspace_vision table
    op.drop_index(
        "ix_workspace_vision_workspace_id",
        table_name="workspace_vision",
        schema="dev",
    )

    op.drop_table("workspace_vision", schema="dev")
