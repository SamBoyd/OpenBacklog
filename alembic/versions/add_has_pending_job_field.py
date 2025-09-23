"""Add has_pending_job field to initiative and task

Revision ID: add_has_pending_job_field
Revises: create_ai_improvement_jobs
Create Date: 2023-12-02 14:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_has_pending_job_field'
down_revision: Union[str, None] = 'create_ai_improvement_jobs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add has_pending_job field to initiative table
    op.add_column('initiative', sa.Column('has_pending_job', sa.Boolean(), server_default='false', nullable=False), schema='dev')
    
    # Add has_pending_job field to task table
    op.add_column('task', sa.Column('has_pending_job', sa.Boolean(), server_default='false', nullable=False), schema='dev')


def downgrade() -> None:
    # Remove has_pending_job field from initiative table
    op.drop_column('initiative', 'has_pending_job', schema='dev')
    
    # Remove has_pending_job field from task table
    op.drop_column('task', 'has_pending_job', schema='dev')
