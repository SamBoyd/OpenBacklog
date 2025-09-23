"""next billing cycle starts

Revision ID: 34e11907e5f4
Revises: e3b36d2f2150
Create Date: 2025-09-08 17:25:59.265875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '34e11907e5f4'
down_revision: Union[str, None] = 'e3b36d2f2150'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add monthly credits tracking fields to user_account_details table
    op.add_column('user_account_details', sa.Column('monthly_credits_total', sa.Integer(), nullable=False, server_default='0'), schema='private')
    op.add_column('user_account_details', sa.Column('monthly_credits_used', sa.Integer(), nullable=False, server_default='0'), schema='private')
    op.add_column('user_account_details', sa.Column('next_billing_cycle_starts', sa.DateTime(), nullable=True), schema='private')


def downgrade() -> None:
    # Remove monthly credits tracking fields from user_account_details table
    op.drop_column('user_account_details', 'next_billing_cycle_starts', schema='private')
    op.drop_column('user_account_details', 'monthly_credits_used', schema='private')
    op.drop_column('user_account_details', 'monthly_credits_total', schema='private')
