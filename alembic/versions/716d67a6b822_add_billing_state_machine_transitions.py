"""add billing state machine transitions

Revision ID: 716d67a6b822
Revises: 7ca2bbe29eed
Create Date: 2025-06-22 13:58:31.927403

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '716d67a6b822'
down_revision: Union[str, None] = '7ca2bbe29eed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The full set of states our application will use
FsmStates = ['NEW', 'EMPTY_BALANCE', 'ACTIVE', 'LOW_BALANCE', 'SUSPENDED', 'CLOSED']

BillingStateTransitionEvents = ['ONBOARD_COMPLETE', 'TOP_UP', 'USAGE_RECORDED', 'REFUND_APPROVED']

def upgrade() -> None:
    op.create_table(
        "billing_state_transitions",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("private.users.id", ondelete="cascade"), nullable=False, index=True),
        sa.Column("from_state", sa.Enum(*FsmStates, name='useraccountstatus', schema="dev", native_enum=True), nullable=True),
        sa.Column("to_state", sa.Enum(*FsmStates, name='useraccountstatus', schema="dev", native_enum=True), nullable=False),
        sa.Column("event", sa.Enum(*BillingStateTransitionEvents, name='billingstatetransitionevent', schema="dev", native_enum=True), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, default=datetime.now, server_default=sa.text("now()")),
        schema="private"
    )

    op.create_index(
        "ix_billing_state_transitions_user_id",
        "billing_state_transitions",
        ["user_id"],
        schema="private"
    )

    op.create_index(
        "ix_billing_state_transitions_user_id_created_at",
        "billing_state_transitions",
        ["user_id", "created_at"],
        schema="private"
    )


def downgrade() -> None:
    # Downgrading enum changes is complex and potentially destructive.
    # It's often safer to move forward with new migrations.
    # For this reason, we will leave the enum types as they are on downgrade.
    op.drop_table("billing_state_transitions", schema="private")
    # Note: We are not removing the added enum values.
    # This would require checking if any data uses them, which is beyond the scope of a typical downgrade script.
