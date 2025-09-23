"""add onboarding

Revision ID: da9d26dea13a
Revises: 07fb5fd1eb0a
Create Date: 2025-07-17 10:41:00.412740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = 'da9d26dea13a'
down_revision: Union[str, None] = '07fb5fd1eb0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add onboarding_completed field
    op.add_column('user_account_details', sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'), schema='private')
    
    # Add free_prompts_used field
    op.add_column('user_account_details', sa.Column('free_prompts_used', sa.Integer(), nullable=False, server_default='0'), schema='private')
    
    # Add free_prompts_limit field
    op.add_column('user_account_details', sa.Column('free_prompts_limit', sa.Integer(), nullable=False, server_default='5'), schema='private')

    op.execute('ALTER TYPE private.ledger_source ADD VALUE IF NOT EXISTS \'FREE_TIER\'')


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('user_account_details', 'free_prompts_limit', schema='private')
    op.drop_column('user_account_details', 'free_prompts_used', schema='private')
    op.drop_column('user_account_details', 'onboarding_completed', schema='private')
