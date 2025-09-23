"""remove initiative_group position

Revision ID: 76b244695258
Revises: b45c044a0903
Create Date: 2025-06-08 11:20:57.305149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '76b244695258'
down_revision: Union[str, None] = 'b45c044a0903'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('initiative_group', 'position', schema='dev')


def downgrade() -> None:
    op.add_column('initiative_group', sa.Column('position', sa.Integer(), nullable=False))
