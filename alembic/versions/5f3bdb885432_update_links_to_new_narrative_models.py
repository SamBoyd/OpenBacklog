"""update links to new narrative models

Revision ID: 5f3bdb885432
Revises: 980e54f90a8b
Create Date: 2025-11-19 12:36:29.674179

"""

from textwrap import dedent
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from src.config import settings

# revision identifiers, used by Alembic.
revision: str = "5f3bdb885432"
down_revision: Union[str, None] = "980e54f90a8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create junction tables for StrategicInitiative
    op.create_table(
        "strategic_initiative_heroes",
        sa.Column(
            "strategic_initiative_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "hero_id",
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
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["strategic_initiative_id"],
            ["dev.strategic_initiatives.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["hero_id"],
            ["dev.heroes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("strategic_initiative_id", "hero_id"),
        schema="dev",
    )

    op.create_table(
        "strategic_initiative_villains",
        sa.Column(
            "strategic_initiative_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "villain_id",
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
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["strategic_initiative_id"],
            ["dev.strategic_initiatives.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["villain_id"],
            ["dev.villains.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("strategic_initiative_id", "villain_id"),
        schema="dev",
    )

    op.create_table(
        "strategic_initiative_conflicts",
        sa.Column(
            "strategic_initiative_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "conflict_id",
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
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["strategic_initiative_id"],
            ["dev.strategic_initiatives.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["conflict_id"],
            ["dev.conflicts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("strategic_initiative_id", "conflict_id"),
        schema="dev",
    )

    # Create junction tables for RoadmapTheme
    op.create_table(
        "roadmap_theme_heroes",
        sa.Column(
            "roadmap_theme_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "hero_id",
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
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["roadmap_theme_id"],
            ["dev.roadmap_themes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["hero_id"],
            ["dev.heroes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("roadmap_theme_id", "hero_id"),
        schema="dev",
    )

    op.create_table(
        "roadmap_theme_villains",
        sa.Column(
            "roadmap_theme_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "villain_id",
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
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["roadmap_theme_id"],
            ["dev.roadmap_themes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["villain_id"],
            ["dev.villains.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("roadmap_theme_id", "villain_id"),
        schema="dev",
    )

    # Create junction tables for TurningPoint
    op.create_table(
        "turning_point_story_arcs",
        sa.Column(
            "turning_point_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "story_arc_id",
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
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["turning_point_id"],
            ["dev.turning_points.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["story_arc_id"],
            ["dev.roadmap_themes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("turning_point_id", "story_arc_id"),
        schema="dev",
    )

    op.create_table(
        "turning_point_initiatives",
        sa.Column(
            "turning_point_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "initiative_id",
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
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["turning_point_id"],
            ["dev.turning_points.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["initiative_id"],
            ["dev.initiative.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("turning_point_id", "initiative_id"),
        schema="dev",
    )

    # Enable RLS and create policies for all junction tables
    junction_tables = [
        "strategic_initiative_heroes",
        "strategic_initiative_villains",
        "strategic_initiative_conflicts",
        "roadmap_theme_heroes",
        "roadmap_theme_villains",
        "turning_point_story_arcs",
        "turning_point_initiatives",
    ]

    for table in junction_tables:
        op.execute(
            dedent(
                f"""
                ALTER TABLE dev.{table} ENABLE ROW LEVEL SECURITY;
                
                CREATE POLICY {table}_policy ON dev.{table}
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt());

                GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.{table} TO {settings.postgrest_authenticated_role};
                """
            )
        )

    # Create indexes for junction tables
    op.create_index(
        "ix_strategic_initiative_heroes_strategic_initiative_id",
        "strategic_initiative_heroes",
        ["strategic_initiative_id"],
        schema="dev",
    )
    op.create_index(
        "ix_strategic_initiative_heroes_hero_id",
        "strategic_initiative_heroes",
        ["hero_id"],
        schema="dev",
    )

    op.create_index(
        "ix_strategic_initiative_villains_strategic_initiative_id",
        "strategic_initiative_villains",
        ["strategic_initiative_id"],
        schema="dev",
    )
    op.create_index(
        "ix_strategic_initiative_villains_villain_id",
        "strategic_initiative_villains",
        ["villain_id"],
        schema="dev",
    )

    op.create_index(
        "ix_strategic_initiative_conflicts_strategic_initiative_id",
        "strategic_initiative_conflicts",
        ["strategic_initiative_id"],
        schema="dev",
    )
    op.create_index(
        "ix_strategic_initiative_conflicts_conflict_id",
        "strategic_initiative_conflicts",
        ["conflict_id"],
        schema="dev",
    )

    op.create_index(
        "ix_roadmap_theme_heroes_roadmap_theme_id",
        "roadmap_theme_heroes",
        ["roadmap_theme_id"],
        schema="dev",
    )
    op.create_index(
        "ix_roadmap_theme_heroes_hero_id",
        "roadmap_theme_heroes",
        ["hero_id"],
        schema="dev",
    )

    op.create_index(
        "ix_roadmap_theme_villains_roadmap_theme_id",
        "roadmap_theme_villains",
        ["roadmap_theme_id"],
        schema="dev",
    )
    op.create_index(
        "ix_roadmap_theme_villains_villain_id",
        "roadmap_theme_villains",
        ["villain_id"],
        schema="dev",
    )

    op.create_index(
        "ix_turning_point_story_arcs_turning_point_id",
        "turning_point_story_arcs",
        ["turning_point_id"],
        schema="dev",
    )
    op.create_index(
        "ix_turning_point_story_arcs_story_arc_id",
        "turning_point_story_arcs",
        ["story_arc_id"],
        schema="dev",
    )

    op.create_index(
        "ix_turning_point_initiatives_turning_point_id",
        "turning_point_initiatives",
        ["turning_point_id"],
        schema="dev",
    )
    op.create_index(
        "ix_turning_point_initiatives_initiative_id",
        "turning_point_initiatives",
        ["initiative_id"],
        schema="dev",
    )

    # Add narrative_intent column to strategic_initiatives
    op.add_column(
        "strategic_initiatives",
        sa.Column("narrative_intent", sa.Text(), nullable=True),
        schema="dev",
    )


def downgrade() -> None:
    # Drop indexes for junction tables
    op.drop_index(
        "ix_turning_point_initiatives_initiative_id",
        "turning_point_initiatives",
        schema="dev",
    )
    op.drop_index(
        "ix_turning_point_initiatives_turning_point_id",
        "turning_point_initiatives",
        schema="dev",
    )
    op.drop_index(
        "ix_turning_point_story_arcs_story_arc_id",
        "turning_point_story_arcs",
        schema="dev",
    )
    op.drop_index(
        "ix_turning_point_story_arcs_turning_point_id",
        "turning_point_story_arcs",
        schema="dev",
    )
    op.drop_index(
        "ix_roadmap_theme_villains_villain_id",
        "roadmap_theme_villains",
        schema="dev",
    )
    op.drop_index(
        "ix_roadmap_theme_villains_roadmap_theme_id",
        "roadmap_theme_villains",
        schema="dev",
    )
    op.drop_index(
        "ix_roadmap_theme_heroes_hero_id",
        "roadmap_theme_heroes",
        schema="dev",
    )
    op.drop_index(
        "ix_roadmap_theme_heroes_roadmap_theme_id",
        "roadmap_theme_heroes",
        schema="dev",
    )
    op.drop_index(
        "ix_strategic_initiative_conflicts_conflict_id",
        "strategic_initiative_conflicts",
        schema="dev",
    )
    op.drop_index(
        "ix_strategic_initiative_conflicts_strategic_initiative_id",
        "strategic_initiative_conflicts",
        schema="dev",
    )
    op.drop_index(
        "ix_strategic_initiative_villains_villain_id",
        "strategic_initiative_villains",
        schema="dev",
    )
    op.drop_index(
        "ix_strategic_initiative_villains_strategic_initiative_id",
        "strategic_initiative_villains",
        schema="dev",
    )
    op.drop_index(
        "ix_strategic_initiative_heroes_hero_id",
        "strategic_initiative_heroes",
        schema="dev",
    )
    op.drop_index(
        "ix_strategic_initiative_heroes_strategic_initiative_id",
        "strategic_initiative_heroes",
        schema="dev",
    )

    # Drop junction tables
    junction_tables_downgrade = [
        "turning_point_initiatives",
        "turning_point_story_arcs",
        "roadmap_theme_villains",
        "roadmap_theme_heroes",
        "strategic_initiative_conflicts",
        "strategic_initiative_villains",
        "strategic_initiative_heroes",
    ]
    for table in junction_tables_downgrade:
        op.execute(f"DROP POLICY IF EXISTS {table}_policy ON dev.{table};")
        op.drop_table(table, schema="dev")

    # Drop narrative_intent column
    op.drop_column("strategic_initiatives", "narrative_intent", schema="dev")
