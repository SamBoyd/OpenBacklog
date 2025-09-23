"""remove duplicate enum

Revision ID: 800920ba0972
Revises: da9d26dea13a
Create Date: 2025-07-20 17:25:15.500289

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '800920ba0972'
down_revision: Union[str, None] = 'da9d26dea13a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the new unified enum type in the private schema
    op.execute("CREATE TYPE private.useraccountstatus AS ENUM ('NEW', 'EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE', 'SUSPENDED', 'CLOSED')")
    
    # Add temporary columns with the new enum type
    op.add_column('billing_state_transitions', 
                  sa.Column('from_state_new', sa.Enum('NEW', 'EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE', 'SUSPENDED', 'CLOSED', 
                                                     name='useraccountstatus', schema='private', native_enum=True), nullable=True),
                  schema='private')
    op.add_column('billing_state_transitions', 
                  sa.Column('to_state_new', sa.Enum('NEW', 'EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE', 'SUSPENDED', 'CLOSED', 
                                                   name='useraccountstatus', schema='private', native_enum=True), nullable=True),
                  schema='private')
    
    op.add_column('user_account_details', 
                  sa.Column('status_new', sa.Enum('NEW', 'EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE', 'SUSPENDED', 'CLOSED', 
                                                 name='useraccountstatus', schema='private', native_enum=True), nullable=True),
                  schema='private')
    
    # Copy data from old columns to new columns
    op.execute("UPDATE private.billing_state_transitions SET from_state_new = from_state::text::private.useraccountstatus")
    op.execute("UPDATE private.billing_state_transitions SET to_state_new = to_state::text::private.useraccountstatus")
    op.execute("UPDATE private.user_account_details SET status_new = status::text::private.useraccountstatus")
    
    # Drop old columns
    op.drop_column('billing_state_transitions', 'from_state', schema='private')
    op.drop_column('billing_state_transitions', 'to_state', schema='private')
    op.drop_column('user_account_details', 'status', schema='private')
    
    # Rename new columns to original names
    op.alter_column('billing_state_transitions', 'from_state_new', new_column_name='from_state', schema='private')
    op.alter_column('billing_state_transitions', 'to_state_new', new_column_name='to_state', schema='private')
    op.alter_column('user_account_details', 'status_new', new_column_name='status', schema='private')
    
    # Set NOT NULL constraint on to_state and status columns
    op.alter_column('billing_state_transitions', 'to_state', nullable=False, schema='private')
    op.alter_column('user_account_details', 'status', nullable=False, schema='private')
    
    # Drop the old enum types
    op.execute("DROP TYPE IF EXISTS dev.useraccountstatus")
    op.execute("DROP TYPE IF EXISTS private.user_account_status")

def downgrade() -> None:
    # Recreate the old enum types
    op.execute("CREATE TYPE dev.useraccountstatus AS ENUM ('NEW', 'EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE', 'SUSPENDED', 'CLOSED')")
    op.execute("CREATE TYPE private.user_account_status AS ENUM ('NEW', 'EMPTY_BALANCE', 'LOW_BALANCE', 'ACTIVE', 'SUSPENDED', 'CLOSED')")
    
    # Add temporary columns with the old enum types
    op.add_column('billing_state_transitions', 
                  sa.Column('from_state_old', sa.Enum('NEW', 'EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE', 'SUSPENDED', 'CLOSED', 
                                                     name='useraccountstatus', schema='dev', native_enum=True), nullable=True),
                  schema='private')
    op.add_column('billing_state_transitions', 
                  sa.Column('to_state_old', sa.Enum('NEW', 'EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE', 'SUSPENDED', 'CLOSED', 
                                                   name='useraccountstatus', schema='dev', native_enum=True), nullable=True),
                  schema='private')
    
    op.add_column('user_account_details', 
                  sa.Column('status_old', sa.Enum('NEW', 'EMPTY_BALANCE', 'LOW_BALANCE', 'ACTIVE', 'SUSPENDED', 'CLOSED', 
                                                 name='user_account_status', schema='private', native_enum=True), nullable=True),
                  schema='private')
    
    # Copy data from new columns to old columns
    op.execute("UPDATE private.billing_state_transitions SET from_state_old = from_state::text::dev.useraccountstatus")
    op.execute("UPDATE private.billing_state_transitions SET to_state_old = to_state::text::dev.useraccountstatus")
    op.execute("UPDATE private.user_account_details SET status_old = status::text::private.user_account_status")
    
    # Drop new columns
    op.drop_column('billing_state_transitions', 'from_state', schema='private')
    op.drop_column('billing_state_transitions', 'to_state', schema='private')
    op.drop_column('user_account_details', 'status', schema='private')
    
    # Rename old columns back to original names
    op.alter_column('billing_state_transitions', 'from_state_old', new_column_name='from_state', schema='private')
    op.alter_column('billing_state_transitions', 'to_state_old', new_column_name='to_state', schema='private')
    op.alter_column('user_account_details', 'status_old', new_column_name='status', schema='private')
    
    # Set NOT NULL constraint on to_state and status columns
    op.alter_column('billing_state_transitions', 'to_state', nullable=False, schema='private')
    op.alter_column('user_account_details', 'status', nullable=False, schema='private')
    
    # Drop the unified enum type
    op.execute("DROP TYPE IF EXISTS private.useraccountstatus")