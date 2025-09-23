"""remove initiative and task order

Revision ID: 55e07bbddf93
Revises: 76b244695258
Create Date: 2025-06-09 16:14:19.822828

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '55e07bbddf93'
down_revision: Union[str, None] = '76b244695258'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('task', 'order', schema='dev')
    op.drop_column('initiative', 'order', schema='dev')


def downgrade() -> None:
    pass
