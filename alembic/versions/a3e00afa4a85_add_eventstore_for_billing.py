"""add eventstore for billing

Revision ID: a3e00afa4a85
Revises: c47c0a3946f0
Create Date: 2025-09-04 10:37:00.318988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a3e00afa4a85'
down_revision: Union[str, None] = 'c47c0a3946f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create billing_events table for event-sourced billing architecture
    op.create_table(
        'billing_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['private.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'version', name='uq_billing_events_user_version'),
        schema='private'
    )
    
    # Create indexes for performance
    op.create_index(
        'ix_billing_events_user_id',
        'billing_events',
        ['user_id'],
        schema='private'
    )
    op.create_index(
        'ix_billing_events_event_type',
        'billing_events',
        ['event_type'],
        schema='private'
    )
    op.create_index(
        'ix_billing_events_created_at',
        'billing_events',
        ['created_at'],
        schema='private'
    )
    
    # Composite index for efficient event retrieval by user and time
    op.create_index(
        'ix_billing_events_user_created_at',
        'billing_events',
        ['user_id', 'created_at'],
        schema='private'
    )
    
    # Composite index for version-based queries
    op.create_index(
        'ix_billing_events_user_version',
        'billing_events',
        ['user_id', 'version'],
        schema='private'
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_billing_events_user_version', schema='private')
    op.drop_index('ix_billing_events_user_created_at', schema='private')
    op.drop_index('ix_billing_events_created_at', schema='private')
    op.drop_index('ix_billing_events_event_type', schema='private')
    op.drop_index('ix_billing_events_user_id', schema='private')
    
    # Drop table
    op.drop_table('billing_events', schema='private')
