"""description defaults

Revision ID: 91eb68186629
Revises: 99304db1efde
Create Date: 2025-08-12 18:42:26.402702

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '91eb68186629'
down_revision: Union[str, None] = '99304db1efde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE dev.initiative SET description='' where description IS NULL")
    op.execute("UPDATE dev.task SET description='' where description IS NULL")

    op.alter_column("initiative", "description", nullable=False, default="", schema='dev')
    op.alter_column("task", "description", nullable=False, default="", schema='dev')



def downgrade() -> None:
    pass
