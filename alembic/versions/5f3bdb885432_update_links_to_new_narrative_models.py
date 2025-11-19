"""update links to new narrative models

Revision ID: 5f3bdb885432
Revises: 980e54f90a8b
Create Date: 2025-11-19 12:36:29.674179

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5f3bdb885432"
down_revision: Union[str, None] = "980e54f90a8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add narrative relationship columns to roadmap_themes table
    op.add_column(
        "roadmap_themes",
        sa.Column("hero_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="dev",
    )
    op.add_column(
        "roadmap_themes",
        sa.Column("primary_villain_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="dev",
    )

    # Create foreign key constraints for roadmap_themes
    op.create_foreign_key(
        "fk_roadmap_themes_hero_id",
        "roadmap_themes",
        "heroes",
        ["hero_id"],
        ["id"],
        source_schema="dev",
        referent_schema="dev",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_roadmap_themes_primary_villain_id",
        "roadmap_themes",
        "villains",
        ["primary_villain_id"],
        ["id"],
        source_schema="dev",
        referent_schema="dev",
        ondelete="SET NULL",
    )

    # Create indexes for roadmap_themes
    op.create_index(
        "ix_roadmap_themes_hero_id", "roadmap_themes", ["hero_id"], schema="dev"
    )
    op.create_index(
        "ix_roadmap_themes_primary_villain_id",
        "roadmap_themes",
        ["primary_villain_id"],
        schema="dev",
    )

    # Add narrative relationship columns to strategic_initiatives table
    op.add_column(
        "strategic_initiatives",
        sa.Column("hero_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="dev",
    )
    op.add_column(
        "strategic_initiatives",
        sa.Column("villain_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="dev",
    )
    op.add_column(
        "strategic_initiatives",
        sa.Column("conflict_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="dev",
    )
    op.add_column(
        "strategic_initiatives",
        sa.Column("narrative_intent", sa.Text(), nullable=True),
        schema="dev",
    )

    # Create foreign key constraints for strategic_initiatives
    op.create_foreign_key(
        "fk_strategic_initiatives_hero_id",
        "strategic_initiatives",
        "heroes",
        ["hero_id"],
        ["id"],
        source_schema="dev",
        referent_schema="dev",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_strategic_initiatives_villain_id",
        "strategic_initiatives",
        "villains",
        ["villain_id"],
        ["id"],
        source_schema="dev",
        referent_schema="dev",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_strategic_initiatives_conflict_id",
        "strategic_initiatives",
        "conflicts",
        ["conflict_id"],
        ["id"],
        source_schema="dev",
        referent_schema="dev",
        ondelete="SET NULL",
    )

    # Create indexes for strategic_initiatives
    op.create_index(
        "ix_strategic_initiatives_hero_id",
        "strategic_initiatives",
        ["hero_id"],
        schema="dev",
    )
    op.create_index(
        "ix_strategic_initiatives_villain_id",
        "strategic_initiatives",
        ["villain_id"],
        schema="dev",
    )
    op.create_index(
        "ix_strategic_initiatives_conflict_id",
        "strategic_initiatives",
        ["conflict_id"],
        schema="dev",
    )


def downgrade() -> None:
    # Drop indexes for strategic_initiatives
    op.drop_index(
        "ix_strategic_initiatives_conflict_id", "strategic_initiatives", schema="dev"
    )
    op.drop_index(
        "ix_strategic_initiatives_villain_id", "strategic_initiatives", schema="dev"
    )
    op.drop_index(
        "ix_strategic_initiatives_hero_id", "strategic_initiatives", schema="dev"
    )

    # Drop foreign key constraints for strategic_initiatives
    op.drop_constraint(
        "fk_strategic_initiatives_conflict_id",
        "strategic_initiatives",
        type_="foreignkey",
        schema="dev",
    )
    op.drop_constraint(
        "fk_strategic_initiatives_villain_id",
        "strategic_initiatives",
        type_="foreignkey",
        schema="dev",
    )
    op.drop_constraint(
        "fk_strategic_initiatives_hero_id",
        "strategic_initiatives",
        type_="foreignkey",
        schema="dev",
    )

    # Drop columns from strategic_initiatives
    op.drop_column("strategic_initiatives", "narrative_intent", schema="dev")
    op.drop_column("strategic_initiatives", "conflict_id", schema="dev")
    op.drop_column("strategic_initiatives", "villain_id", schema="dev")
    op.drop_column("strategic_initiatives", "hero_id", schema="dev")

    # Drop indexes for roadmap_themes
    op.drop_index(
        "ix_roadmap_themes_primary_villain_id", "roadmap_themes", schema="dev"
    )
    op.drop_index("ix_roadmap_themes_hero_id", "roadmap_themes", schema="dev")

    # Drop foreign key constraints for roadmap_themes
    op.drop_constraint(
        "fk_roadmap_themes_primary_villain_id",
        "roadmap_themes",
        type_="foreignkey",
        schema="dev",
    )
    op.drop_constraint(
        "fk_roadmap_themes_hero_id", "roadmap_themes", type_="foreignkey", schema="dev"
    )

    # Drop columns from roadmap_themes
    op.drop_column("roadmap_themes", "primary_villain_id", schema="dev")
    op.drop_column("roadmap_themes", "hero_id", schema="dev")
