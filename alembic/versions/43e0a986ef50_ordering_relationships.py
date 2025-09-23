"""ordering relationships

Revision ID: 43e0a986ef50
Revises: 03d99010e3d0
Create Date: 2025-08-01 20:29:09.673543

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '43e0a986ef50'
down_revision: Union[str, None] = '03d99010e3d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add foreign key columns for direct relationships
    op.add_column('orderings', sa.Column('initiative_id', sa.UUID(), nullable=True), schema="dev")
    op.add_column('orderings', sa.Column('task_id', sa.UUID(), nullable=True), schema="dev")
    
    # Create foreign key constraints
    op.create_foreign_key(
        'fk_orderings_initiative_id',
        'orderings', 'initiative',
        ['initiative_id'], ['id'],
        source_schema='dev', referent_schema='dev',
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_orderings_task_id', 
        'orderings', 'task',
        ['task_id'], ['id'],
        source_schema='dev', referent_schema='dev',
        ondelete='CASCADE'
    )
    
    # Create indexes for performance
    op.create_index('ix_orderings_initiative_id', 'orderings', ['initiative_id'], schema="dev")
    op.create_index('ix_orderings_task_id', 'orderings', ['task_id'], schema="dev")


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_orderings_task_id', 'orderings', schema="dev")
    op.drop_index('ix_orderings_initiative_id', 'orderings', schema="dev")
    
    # Drop foreign key constraints
    op.drop_constraint('fk_orderings_task_id', 'orderings', type_='foreignkey', schema="dev")
    op.drop_constraint('fk_orderings_initiative_id', 'orderings', type_='foreignkey', schema="dev")
    
    # Drop columns
    op.drop_column('orderings', 'task_id', schema="dev")
    op.drop_column('orderings', 'initiative_id', schema="dev")
