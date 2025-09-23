"""github installations cascade delete

Revision ID: 6c61afaa1e50
Revises: 716d67a6b822
Create Date: 2025-07-07 08:57:21.771193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '6c61afaa1e50'
down_revision: Union[str, None] = '716d67a6b822'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "github_installation",
        "user_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    op.drop_constraint(
        "github_installation_user_id_fkey",
        "github_installation",
        type_="foreignkey",
        schema="private",
    )

    op.create_foreign_key(
        "github_installation_user_id_fkey",
        "github_installation",
        "users",
        ["user_id"],
        ["id"],
        source_schema="private",
        referent_schema="private",
        ondelete="CASCADE",
    )

def downgrade() -> None:
    pass
