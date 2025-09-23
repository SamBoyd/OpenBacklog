"""add litellm enum

Revision ID: 45d4effd70c7
Revises: 55e07bbddf93
Create Date: 2025-06-16 10:28:20.974566

"""
from textwrap import dedent
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '45d4effd70c7'
down_revision: Union[str, None] = '55e07bbddf93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        dedent(
            f"""
            ALTER TYPE dev.apiprovider ADD VALUE 'LITELLM';
            """
        )
    )


def downgrade() -> None:
    pass
