"""ordering remove entity_id

Revision ID: 99304db1efde
Revises: 43e0a986ef50
Create Date: 2025-08-11 11:56:57.098749

"""
from textwrap import dedent
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '99304db1efde'
down_revision: Union[str, None] = '43e0a986ef50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('orderings', 'entity_id', schema='dev')
    op.alter_column('ordering', 'context_type')

def downgrade() -> None:
    pass
