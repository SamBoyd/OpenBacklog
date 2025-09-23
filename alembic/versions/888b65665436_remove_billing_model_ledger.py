"""remove billing model ledger

Revision ID: 888b65665436
Revises: a3e00afa4a85
Create Date: 2025-09-05 09:28:01.138064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '888b65665436'
down_revision: Union[str, None] = 'a3e00afa4a85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("ledger", schema="private")


def downgrade() -> None:
    pass
