"""token deleted_at

Revision ID: 33ed869554e2
Revises: 07c6d6036168
Create Date: 2025-09-17 09:19:29.149390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '33ed869554e2'
down_revision: Union[str, None] = '07c6d6036168'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add deleted_at column to user_key table for soft delete functionality
    op.add_column('user_key', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True), schema='dev')


def downgrade() -> None:
    # Remove the deleted_at column
    op.drop_column('user_key', 'deleted_at', schema='dev')
