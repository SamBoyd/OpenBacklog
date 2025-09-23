"""empty message

Revision ID: b45c044a0903
Revises: 16c078217323, 1aeb37e5886c
Create Date: 2025-06-04 15:03:27.078883

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = 'b45c044a0903'
down_revision: Union[str, None] = ('16c078217323', '1aeb37e5886c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
