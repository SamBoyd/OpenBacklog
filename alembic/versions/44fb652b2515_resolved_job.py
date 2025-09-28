"""resolved job

Revision ID: 44fb652b2515
Revises: 4ad1dd0bfa19
Create Date: 2025-09-28 14:02:23.882050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.config import settings


# revision identifiers, used by Alembic.
revision: str = '44fb652b2515'
down_revision: Union[str, None] = '4ad1dd0bfa19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add RESOLVED status to the existing JobStatus enum
    op.execute("ALTER TYPE dev.job_status ADD VALUE 'RESOLVED'")
    op.execute(f"GRANT UPDATE ON TABLE dev.ai_improvement_job TO {settings.postgrest_authenticated_role}")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave this as a no-op since RESOLVED values
    # won't break the application if the migration is rolled back
    op.execute(f"REVOKE UPDATE ON TABLE dev.ai_improvement_job FROM {settings.postgrest_authenticated_role}")
