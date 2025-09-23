"""add ledger

Revision ID: 7ca2bbe29eed
Revises: 45d4effd70c7
Create Date: 2025-06-19 20:14:19.379404

"""
from datetime import datetime
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '7ca2bbe29eed'
down_revision: Union[str, None] = '45d4effd70c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LedgerSource = (
    "STRIPE",
    "USAGE",
    "REFUND",
    "CHARGEBACK",
)

UserAccountStatus = (
    "NEW",
    "EMPTY_BALANCE",
    "LOW_BALANCE",
    "ACTIVE",
    "SUSPENDED",
    "CLOSED",
)

def upgrade() -> None:
    op.create_table(
        "ledger",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_cents", sa.Float, nullable=False),
        sa.Column("source", sa.Enum(*LedgerSource, name="ledger_source", schema="private", native_enum=True), nullable=False),
        sa.Column("external_id", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, default=datetime.now, server_default=text("now()")),
        sa.Column("download_url", sa.String, nullable=True),
        schema="private",
    )

    op.create_index(
        "idx_ledger_user_id",
        "ledger",
        ["user_id"],
        unique=False,
        schema="private",
    )

    op.create_table(
        "user_account_details",
        sa.Column("user_id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("balance_cents", sa.Float, nullable=False, default=0),
        sa.Column("status", sa.Enum(*UserAccountStatus, name="user_account_status", schema="private", native_enum=True), nullable=False, default="NEW"),
        sa.Column("stripe_customer_id", sa.String, nullable=True),
        sa.Column("last_usage_query_time", sa.DateTime, nullable=True),
        sa.Column("last_total_cost", sa.Float, nullable=False, default=0),
        schema="private",
    )

    op.create_index(
        "idx_user_account_details_user_id",
        "user_account_details",
        ["user_id"],
        unique=True,
        schema="private",
    )

    PendingTopupStatus = (
        'PENDING',
        'COMPLETED',
        'FAILED',
        'CANCELLED',
    )

    op.create_table(
        "pending_topups",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.String, nullable=False, unique=True, index=True),
        sa.Column("amount_cents", sa.BigInteger, nullable=False),
        sa.Column("status", sa.Enum(*PendingTopupStatus, name="pending_topup_status", schema="private", native_enum=True), nullable=False, default="PENDING"),
        sa.Column("created_at", sa.DateTime, nullable=False, default=datetime.now, server_default=text("now()")),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        schema="private",
    )

    op.create_index(
        "idx_pending_topups_user_id",
        "pending_topups",
        ["user_id"],
        unique=False,
        schema="private",
    )


def downgrade() -> None:
    op.drop_table("ledger", schema="private")
    op.drop_table("user_account_details", schema="private")
    op.drop_table("pending_topups", schema="private")