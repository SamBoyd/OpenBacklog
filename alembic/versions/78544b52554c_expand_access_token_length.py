"""expand access token length

Revision ID: 78544b52554c
Revises: 46c1780ab415
Create Date: 2025-07-13 16:40:06.936347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '78544b52554c'
down_revision: Union[str, None] = '46c1780ab415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'access_token',
        'token',
        schema='private',
        existing_type=sa.String(length=43),
        type_=sa.String(length=1024),
        nullable=False
    )


def downgrade() -> None:
    pass
