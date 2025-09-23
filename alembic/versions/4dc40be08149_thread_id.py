"""thread id

Revision ID: 4dc40be08149
Revises: 122d98e56e8c
Create Date: 2025-05-24 10:21:49.336552

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '4dc40be08149'
down_revision: Union[str, None] = '122d98e56e8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ai_improvement_job', sa.Column('thread_id', sa.String(), nullable=True), schema='dev')


def downgrade() -> None:
    op.drop_column('ai_improvement_job', 'thread_id', schema='dev')
