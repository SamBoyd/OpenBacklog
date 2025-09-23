"""user profile picture

Revision ID: 40c8f769b104
Revises: f56f2a0d49b4
Create Date: 2025-02-17 12:10:29.865907

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = "40c8f769b104"
down_revision: Union[str, None] = "f56f2a0d49b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("profile_picture_url", sa.String(), nullable=True),
        schema="private",
    )


def downgrade() -> None:
    op.drop_column("users", "profile_picture_url", schema="private")
