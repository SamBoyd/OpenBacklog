"""move enum for fsm event to private

Revision ID: dcb115bfa0ce
Revises: 800920ba0972
Create Date: 2025-07-20 17:45:36.939398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = 'dcb115bfa0ce'
down_revision: Union[str, None] = '800920ba0972'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum in the private schema
    op.execute("CREATE TYPE private.billingstatetransitionevent AS ENUM ('ONBOARD_COMPLETE', 'TOP_UP', 'USAGE_RECORDED', 'REFUND_APPROVED')")
    
    # Update the column to use the new enum type
    op.execute("ALTER TABLE private.billing_state_transitions ALTER COLUMN event TYPE private.billingstatetransitionevent USING event::text::private.billingstatetransitionevent")
    
    # Drop the old enum from dev schema
    op.execute("DROP TYPE dev.billingstatetransitionevent")


def downgrade() -> None:
    # Create the enum back in the dev schema
    op.execute("CREATE TYPE dev.billingstatetransitionevent AS ENUM ('ONBOARD_COMPLETE', 'TOP_UP', 'USAGE_RECORDED', 'REFUND_APPROVED')")
    
    # Update the column to use the dev schema enum type
    op.execute("ALTER TABLE private.billing_state_transitions ALTER COLUMN event TYPE dev.billingstatetransitionevent USING event::text::dev.billingstatetransitionevent")
    
    # Drop the enum from private schema
    op.execute("DROP TYPE private.billingstatetransitionevent")
