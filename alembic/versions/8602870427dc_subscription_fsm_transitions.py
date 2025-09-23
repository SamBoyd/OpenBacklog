"""subscription fsm transitions

Revision ID: 8602870427dc
Revises: 5bfdc54202cf
Create Date: 2025-08-31 10:50:01.326297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '8602870427dc'
down_revision: Union[str, None] = '5bfdc54202cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the new enum type with all new values
    new_enum = sa.Enum(
        'SIGNUP_SUBSCRIPTION',
        'CANCEL_SUBSCRIPTION', 
        'REACTIVATE_SUBSCRIPTION',
        'START_BILLING_CYCLE',
        'TOPUP_BALANCE',
        'USAGE_RECORDED',
        'REFUND_BALANCE',
        'CHARGEBACK_DETECTED',
        name='billingstatetransitionevent_new',
        schema='private'
    )
    new_enum.create(op.get_bind())
    
    # Update the column to use the new enum
    op.execute("ALTER TABLE private.billing_state_transitions ALTER COLUMN event TYPE private.billingstatetransitionevent_new USING event::text::private.billingstatetransitionevent_new")
    
    # Drop the old enum
    op.execute("DROP TYPE IF EXISTS private.billingstatetransitionevent")
    
    # Rename the new enum to the original name
    op.execute("ALTER TYPE private.billingstatetransitionevent_new RENAME TO billingstatetransitionevent")


def downgrade() -> None:
    # Create the old enum type with original values
    old_enum = sa.Enum(
        'ONBOARD_COMPLETE',
        'TOP_UP',
        'USAGE_RECORDED',
        'REFUND_APPROVED',
        'CHARGEBACK_DETECTED',
        name='billingstatetransitionevent_old',
        schema='private'
    )
    old_enum.create(op.get_bind())
    
    # Map new values to old values where possible (data migration)
    # Note: This will lose data for subscription-specific events that don't map to old events
    mapping_updates = [
        ("UPDATE private.billing_state_transitions SET event = 'ONBOARD_COMPLETE' WHERE event = 'SIGNUP_SUBSCRIPTION'", "Map signup to onboard"),
        ("UPDATE private.billing_state_transitions SET event = 'CHARGEBACK_DETECTED' WHERE event = 'CANCEL_SUBSCRIPTION'", "Map cancel to chargeback (lossy)"),
        ("UPDATE private.billing_state_transitions SET event = 'ONBOARD_COMPLETE' WHERE event = 'REACTIVATE_SUBSCRIPTION'", "Map reactivate to onboard"),
        ("UPDATE private.billing_state_transitions SET event = 'TOP_UP' WHERE event = 'START_BILLING_CYCLE'", "Map cycle to topup (lossy)"),
        ("UPDATE private.billing_state_transitions SET event = 'TOP_UP' WHERE event = 'TOPUP_BALANCE'", "Map topup balance to topup"),
        ("UPDATE private.billing_state_transitions SET event = 'REFUND_APPROVED' WHERE event = 'REFUND_BALANCE'", "Map balance refund to refund"),
    ]
    
    for sql, comment in mapping_updates:
        op.execute(sql + f" -- {comment}")
    
    # Update the column to use the old enum
    op.execute("ALTER TABLE private.billing_state_transitions ALTER COLUMN event TYPE private.billingstatetransitionevent_old USING event::text::private.billingstatetransitionevent_old")
    
    # Drop the new enum
    op.execute("DROP TYPE IF EXISTS private.billingstatetransitionevent")
    
    # Rename the old enum to the original name
    op.execute("ALTER TYPE private.billingstatetransitionevent_old RENAME TO billingstatetransitionevent")
