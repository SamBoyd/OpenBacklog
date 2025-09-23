"""user password nullable

Revision ID: 46c1780ab415
Revises: 6c61afaa1e50
Create Date: 2025-07-13 09:49:13.223101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '46c1780ab415'
down_revision: Union[str, None] = '6c61afaa1e50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'hashed_password', schema='private', existing_type=sa.String(length=1024), nullable=True)

def downgrade() -> None:
    pass
