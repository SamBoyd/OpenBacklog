"""initiative delete cascade

Revision ID: 122d98e56e8c
Revises: 1623674e8a8a
Create Date: 2025-05-12 12:38:42.296019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '122d98e56e8c'
down_revision: Union[str, None] = '1623674e8a8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing foreign key constraints
    op.drop_constraint('task_initiative_id_fkey', 'task', schema='dev')
    op.drop_constraint('checklist_task_id_fkey', 'checklist', schema='dev')
    
    # Recreate them with ON DELETE CASCADE
    op.create_foreign_key(
        'task_initiative_id_fkey',
        'task',
        'initiative',
        ['initiative_id'],
        ['id'],
        source_schema='dev',
        referent_schema='dev',
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'checklist_task_id_fkey',
        'checklist',
        'task',
        ['task_id'],
        ['id'],
        source_schema='dev',
        referent_schema='dev',
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop the CASCADE constraints
    op.drop_constraint('task_initiative_id_fkey', 'task', schema='dev')
    op.drop_constraint('checklist_task_id_fkey', 'checklist', schema='dev')
    
    # Recreate them without CASCADE
    op.create_foreign_key(
        'task_initiative_id_fkey',
        'task',
        'initiative',
        ['initiative_id'],
        ['id'],
        source_schema='dev',
        referent_schema='dev'
    )
    
    op.create_foreign_key(
        'checklist_task_id_fkey',
        'checklist',
        'task',
        ['task_id'],
        ['id'],
        source_schema='dev',
        referent_schema='dev'
    )
