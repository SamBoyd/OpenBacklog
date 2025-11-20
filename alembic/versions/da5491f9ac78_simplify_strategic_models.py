"""simplify strategic models

Revision ID: da5491f9ac78
Revises: 5f3bdb885432
Create Date: 2025-11-20 11:54:14.136272

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "da5491f9ac78"
down_revision: Union[str, None] = "5f3bdb885432"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop anti_strategy from strategic_pillars
    op.drop_column("strategic_pillars", "anti_strategy", schema="dev")

    # Drop metrics from product_outcomes
    op.drop_column("product_outcomes", "metrics", schema="dev")
    op.drop_column("product_outcomes", "time_horizon_months", schema="dev")

    # Add description to roadmap_themes, then drop old fields
    op.add_column(
        "roadmap_themes",
        sa.Column("description", sa.Text(), nullable=True),
        schema="dev",
    )
    op.drop_column("roadmap_themes", "problem_statement", schema="dev")
    op.drop_column("roadmap_themes", "hypothesis", schema="dev")
    op.drop_column("roadmap_themes", "indicative_metrics", schema="dev")

    # Add description to strategic_initiatives, then drop old fields
    op.add_column(
        "strategic_initiatives",
        sa.Column("description", sa.Text(), nullable=True),
        schema="dev",
    )
    op.drop_column("strategic_initiatives", "user_need", schema="dev")
    op.drop_column("strategic_initiatives", "connection_to_vision", schema="dev")
    op.drop_column("strategic_initiatives", "success_criteria", schema="dev")
    op.drop_column("strategic_initiatives", "out_of_scope", schema="dev")


def downgrade() -> None:
    # Restore strategic_initiatives columns
    op.add_column(
        "strategic_initiatives",
        sa.Column("out_of_scope", sa.Text(), nullable=True),
        schema="dev",
    )
    op.add_column(
        "strategic_initiatives",
        sa.Column("success_criteria", sa.Text(), nullable=True),
        schema="dev",
    )
    op.add_column(
        "strategic_initiatives",
        sa.Column("connection_to_vision", sa.Text(), nullable=True),
        schema="dev",
    )
    op.add_column(
        "strategic_initiatives",
        sa.Column("user_need", sa.Text(), nullable=True),
        schema="dev",
    )
    op.drop_column("strategic_initiatives", "description", schema="dev")

    # Restore roadmap_themes columns
    op.add_column(
        "roadmap_themes",
        sa.Column("indicative_metrics", sa.Text(), nullable=True),
        schema="dev",
    )
    op.add_column(
        "roadmap_themes",
        sa.Column("hypothesis", sa.Text(), nullable=True),
        schema="dev",
    )
    op.add_column(
        "roadmap_themes",
        sa.Column("problem_statement", sa.Text(), nullable=False),
        schema="dev",
    )
    op.drop_column("roadmap_themes", "description", schema="dev")
    op.drop_column("roadmap_themes", "time_horizon_months", schema="dev")

    # Restore product_outcomes columns
    op.add_column(
        "product_outcomes", sa.Column("metrics", sa.Text(), nullable=True), schema="dev"
    )
    op.add_column(
        "product_outcomes",
        sa.Column("time_horizon_months", sa.Integer(), nullable=True),
        schema="dev",
    )

    # Restore strategic_pillars columns
    op.add_column(
        "strategic_pillars",
        sa.Column("anti_strategy", sa.Text(), nullable=True),
        schema="dev",
    )
