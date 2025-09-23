"""Add subscription cancellation tracking

Revision ID: e3b36d2f2150
Revises: 888b65665436
Create Date: 2025-09-08 04:25:24.548025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = 'e3b36d2f2150'
down_revision: Union[str, None] = '888b65665436'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add subscription cancellation tracking fields to user_account_details table
    op.add_column('user_account_details', sa.Column('subscription_cancel_at', sa.DateTime(), nullable=True), schema='private')
    op.add_column('user_account_details', sa.Column('subscription_canceled_at', sa.DateTime(), nullable=True), schema='private')
    op.add_column('user_account_details', sa.Column('subscription_cancel_at_period_end', sa.Boolean(), nullable=True), schema='private')


def downgrade() -> None:
    # Remove subscription cancellation tracking fields from user_account_details table
    op.drop_column('user_account_details', 'subscription_cancel_at_period_end', schema='private')
    op.drop_column('user_account_details', 'subscription_canceled_at', schema='private')
    op.drop_column('user_account_details', 'subscription_cancel_at', schema='private')
