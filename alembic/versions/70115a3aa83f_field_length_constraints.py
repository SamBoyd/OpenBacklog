"""field length constraints

Revision ID: 70115a3aa83f
Revises: da5491f9ac78
Create Date: 2025-11-20 15:22:54.314741

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "70115a3aa83f"
down_revision: Union[str, None] = "da5491f9ac78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add check constraints for strategic_initiatives table
    op.create_check_constraint(
        "ck_strategic_initiatives_description_length",
        "strategic_initiatives",
        "description IS NULL OR char_length(description) <= 4000",
        schema="dev",
    )

    op.create_check_constraint(
        "ck_strategic_initiatives_narrative_intent_length",
        "strategic_initiatives",
        "narrative_intent IS NULL OR char_length(narrative_intent) <= 1000",
        schema="dev",
    )

    # Add check constraint for roadmap_themes table
    op.create_check_constraint(
        "ck_roadmap_themes_description_length",
        "roadmap_themes",
        "description IS NULL OR char_length(description) <= 4000",
        schema="dev",
    )


def downgrade() -> None:
    # Drop check constraints for strategic_initiatives table
    op.drop_constraint(
        "ck_strategic_initiatives_description_length",
        "strategic_initiatives",
        schema="dev",
    )

    op.drop_constraint(
        "ck_strategic_initiatives_narrative_intent_length",
        "strategic_initiatives",
        schema="dev",
    )

    # Drop check constraint for roadmap_themes table
    op.drop_constraint(
        "ck_roadmap_themes_description_length", "roadmap_themes", schema="dev"
    )
