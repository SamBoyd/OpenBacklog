"""subscription legder source

Revision ID: 610afe0fa470
Revises: 8602870427dc
Create Date: 2025-08-31 16:45:25.905749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '610afe0fa470'
down_revision: Union[str, None] = '8602870427dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the new enum type with updated values
    op.execute("""
        CREATE TYPE private.ledger_source_new AS ENUM (
            'STRIPE',
            'INCLUDED_USAGE',
            'BALANCE_USAGE', 
            'FREE_TIER',
            'REFUND',
            'CHARGEBACK'
        )
    """)
    
    # Switch the column to use the new enum type and convert USAGE to BALANCE_USAGE in one step
    op.execute("""
        ALTER TABLE private.ledger
        ALTER COLUMN source TYPE private.ledger_source_new
        USING CASE 
            WHEN source::text = 'USAGE' THEN 'BALANCE_USAGE'::private.ledger_source_new
            ELSE source::text::private.ledger_source_new
        END
    """)
    
    # Drop the old enum type
    op.execute("DROP TYPE private.ledger_source")
    
    # Rename the new enum type to the original name
    op.execute("ALTER TYPE private.ledger_source_new RENAME TO ledger_source")

def downgrade() -> None:
    # Create the old enum type
    op.execute("""
        CREATE TYPE private.ledger_source_old AS ENUM (
            'STRIPE',
            'USAGE',
            'FREE_TIER',
            'REFUND',
            'CHARGEBACK'
        )
    """)
    
    # Switch the column to use the old enum type and convert back to USAGE in one step
    op.execute("""
        ALTER TABLE private.ledger
        ALTER COLUMN source TYPE private.ledger_source_old
        USING CASE 
            WHEN source::text IN ('INCLUDED_USAGE', 'BALANCE_USAGE') THEN 'USAGE'::private.ledger_source_old
            ELSE source::text::private.ledger_source_old
        END
    """)
    
    # Drop the current enum type
    op.execute("DROP TYPE private.ledger_source")
    
    # Rename the old enum type to the original name
    op.execute("ALTER TYPE private.ledger_source_old RENAME TO ledger_source")
