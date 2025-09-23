"""Create AI improvement jobs table

Revision ID: create_ai_improvement_jobs
Revises: # Add the previous revision ID here, or leave as is if this is the initial migration
Create Date: 2023-12-01 12:00:00.000000

"""
from textwrap import dedent
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from src.config import settings


# revision identifiers, used by Alembic.
revision: str = 'create_ai_improvement_jobs'
down_revision: Union[str, None] = '8751db1a83f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create JobStatus enum
    # op.execute("CREATE TYPE dev.job_status AS ENUM ('Pending', 'Processing', 'Completed', 'Failed')")
    # op.alter_column('task', 'status', schema='dev', existing_type=sa.Enum('TO_DO','IN_PROGRESS','BLOCKED','DONE','ARCHIVED', name='taskstatus', schema='dev'), nullable=True)
    
    # Create ai_improvement_job table
    op.create_table(
        'ai_improvement_job',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('lens', sa.Enum('TASK', 'TASKS', 'INITIATIVE', 'INITIATIVES', name='lens', schema='dev'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELED', name='job_status', schema='dev'), 
                  server_default='PENDING', nullable=False),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('dev.get_user_id_from_jwt()')),
        sa.Column('messages', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='dev'
    )
    op.create_index('ix_dev_ai_improvement_job_id', 'ai_improvement_job', ['id'], unique=False, schema='dev')

    op.execute(
        dedent(
            f"""
            GRANT SELECT, DELETE ON TABLE dev.ai_improvement_job TO {settings.postgrest_authenticated_role};
            """
        )
    )

    op.execute(
        dedent(
            f"""
            ALTER TABLE dev.ai_improvement_job ENABLE ROW LEVEL SECURITY;
            """
        )
    )

    op.execute(
        dedent(
            """
            ALTER TABLE dev.workspace ENABLE ROW LEVEL SECURITY;

            CREATE POLICY ai_improvement_job_policy ON dev.ai_improvement_job
            USING (user_id = dev.get_user_id_from_jwt())
            WITH CHECK (user_id = dev.get_user_id_from_jwt());  
        """
        )
    )

def downgrade() -> None:
    op.drop_index('ix_dev_ai_improvement_job_id', table_name='ai_improvement_job', schema='dev')
    op.drop_table('ai_improvement_job', schema='dev')
    op.execute("DROP TYPE dev.job_status")
