"""title and description defaults

Revision ID: d956b708a19a
Revises: 786119209325
Create Date: 2025-08-26 06:28:57.689583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = 'd956b708a19a'
down_revision: Union[str, None] = '786119209325'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('task', 'title', nullable=False, server_default='', schema='dev')
    op.alter_column('task', 'description', nullable=False, server_default='', schema='dev')

    op.alter_column('initiative', 'title', nullable=False, server_default='', schema='dev')
    op.alter_column('initiative', 'description', nullable=False, server_default='', schema='dev')

def downgrade() -> None:
    op.alter_column('task', 'title', nullable=False, server_default=None, schema='dev')
    op.alter_column('task', 'description', nullable=False, server_default=None, schema='dev')

    op.alter_column('initiative', 'title', nullable=False, server_default=None, schema='dev')
    op.alter_column('initiative', 'description', nullable=False, server_default=None, schema='dev')
