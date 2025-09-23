"""subscription billing fsm states

Revision ID: 5bfdc54202cf
Revises: d956b708a19a
Create Date: 2025-08-31 09:53:01.542767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '5bfdc54202cf'
down_revision: Union[str, None] = 'd956b708a19a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create new enum type with subscription-based states
    op.execute("CREATE TYPE useraccountstatus_new AS ENUM ('NEW', 'ACTIVE_SUBSCRIPTION', 'NO_SUBSCRIPTION', 'METERED_BILLING', 'SUSPENDED', 'CLOSED')")
    
    # Update private.user_account_details.status column
    op.execute("""
        ALTER TABLE private.user_account_details 
        ALTER COLUMN status TYPE useraccountstatus_new 
        USING CASE 
            WHEN status = 'NEW' THEN 'NEW'::useraccountstatus_new
            WHEN status IN ('EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE') THEN 'ACTIVE_SUBSCRIPTION'::useraccountstatus_new
            WHEN status = 'SUSPENDED' THEN 'SUSPENDED'::useraccountstatus_new
            WHEN status = 'CLOSED' THEN 'CLOSED'::useraccountstatus_new
            ELSE 'NEW'::useraccountstatus_new
        END
    """)
    
    # Update private.billing_state_transitions.from_state column
    op.execute("""
        ALTER TABLE private.billing_state_transitions 
        ALTER COLUMN from_state TYPE useraccountstatus_new 
        USING CASE 
            WHEN from_state = 'NEW' THEN 'NEW'::useraccountstatus_new
            WHEN from_state IN ('EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE') THEN 'ACTIVE_SUBSCRIPTION'::useraccountstatus_new
            WHEN from_state = 'SUSPENDED' THEN 'SUSPENDED'::useraccountstatus_new
            WHEN from_state = 'CLOSED' THEN 'CLOSED'::useraccountstatus_new
            WHEN from_state IS NULL THEN NULL
            ELSE 'NEW'::useraccountstatus_new
        END
    """)
    
    # Update private.billing_state_transitions.to_state column  
    op.execute("""
        ALTER TABLE private.billing_state_transitions 
        ALTER COLUMN to_state TYPE useraccountstatus_new 
        USING CASE 
            WHEN to_state = 'NEW' THEN 'NEW'::useraccountstatus_new
            WHEN to_state IN ('EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE') THEN 'ACTIVE_SUBSCRIPTION'::useraccountstatus_new
            WHEN to_state = 'SUSPENDED' THEN 'SUSPENDED'::useraccountstatus_new
            WHEN to_state = 'CLOSED' THEN 'CLOSED'::useraccountstatus_new
            ELSE 'NEW'::useraccountstatus_new
        END
    """)
    
    # Drop old enum type and rename new one
    op.execute("DROP TYPE useraccountstatus")
    op.execute("ALTER TYPE useraccountstatus_new RENAME TO useraccountstatus")

def downgrade() -> None:
    # Create old enum type
    op.execute("CREATE TYPE useraccountstatus_old AS ENUM ('NEW', 'EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE', 'SUSPENDED', 'CLOSED')")
    
    # Revert private.user_account_details.status column
    op.execute("""
        ALTER TABLE private.user_account_details 
        ALTER COLUMN status TYPE useraccountstatus_old 
        USING CASE 
            WHEN status = 'NEW' THEN 'NEW'::useraccountstatus_old
            WHEN status IN ('ACTIVE_SUBSCRIPTION', 'NO_SUBSCRIPTION', 'METERED_BILLING') THEN 'ACTIVE'::useraccountstatus_old
            WHEN status = 'SUSPENDED' THEN 'SUSPENDED'::useraccountstatus_old
            WHEN status = 'CLOSED' THEN 'CLOSED'::useraccountstatus_old
            ELSE 'NEW'::useraccountstatus_old
        END
    """)
    
    # Revert private.billing_state_transitions.from_state column
    op.execute("""
        ALTER TABLE private.billing_state_transitions 
        ALTER COLUMN from_state TYPE useraccountstatus_old 
        USING CASE 
            WHEN from_state = 'NEW' THEN 'NEW'::useraccountstatus_old
            WHEN from_state IN ('ACTIVE_SUBSCRIPTION', 'NO_SUBSCRIPTION', 'METERED_BILLING') THEN 'ACTIVE'::useraccountstatus_old
            WHEN from_state = 'SUSPENDED' THEN 'SUSPENDED'::useraccountstatus_old
            WHEN from_state = 'CLOSED' THEN 'CLOSED'::useraccountstatus_old
            WHEN from_state IS NULL THEN NULL
            ELSE 'NEW'::useraccountstatus_old
        END
    """)
    
    # Revert private.billing_state_transitions.to_state column
    op.execute("""
        ALTER TABLE private.billing_state_transitions 
        ALTER COLUMN to_state TYPE useraccountstatus_old 
        USING CASE 
            WHEN to_state = 'NEW' THEN 'NEW'::useraccountstatus_old
            WHEN to_state IN ('ACTIVE_SUBSCRIPTION', 'NO_SUBSCRIPTION', 'METERED_BILLING') THEN 'ACTIVE'::useraccountstatus_old
            WHEN to_state = 'SUSPENDED' THEN 'SUSPENDED'::useraccountstatus_old
            WHEN to_state = 'CLOSED' THEN 'CLOSED'::useraccountstatus_old
            ELSE 'NEW'::useraccountstatus_old
        END
    """)
    
    # Drop new enum type and rename old one back
    op.execute("DROP TYPE useraccountstatus")
    op.execute("ALTER TYPE useraccountstatus_old RENAME TO useraccountstatus")
