"""Add MONTHLY_CREDIT_RESET to LedgerSource enum

Revision ID: c47c0a3946f0
Revises: 610afe0fa470
Create Date: 2025-09-03 18:20:09.087519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = 'c47c0a3946f0'
down_revision: Union[str, None] = '610afe0fa470'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new enum value to LedgerSource
    op.execute("ALTER TYPE ledger_source ADD VALUE 'MONTHLY_CREDIT_RESET'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type without the value
    # and updating all references, which is complex and risky
    # For now, we'll leave this as a no-op since enum additions are generally safe
    pass
