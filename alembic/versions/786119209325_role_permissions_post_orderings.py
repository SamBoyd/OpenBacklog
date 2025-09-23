"""role permissions post orderings

Revision ID: 786119209325
Revises: 7bf0ed5e8056
Create Date: 2025-08-16 11:06:51.580984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.config import settings

# revision identifiers, used by Alembic.
revision: str = '786119209325'
down_revision: Union[str, None] = '7bf0ed5e8056'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(f"""
        REVOKE INSERT, DELETE, TRUNCATE ON TABLE dev.orderings from {settings.postgrest_authenticated_role};
    """)

    op.execute(f"""
        REVOKE INSERT, DELETE, TRUNCATE ON TABLE dev.initiative from {settings.postgrest_authenticated_role};
    """)

    op.execute(f"""
        REVOKE INSERT, DELETE, TRUNCATE ON TABLE dev.task from {settings.postgrest_authenticated_role};
    """)

    op.execute(f"""
        REVOKE INSERT, DELETE, UPDATE, TRUNCATE ON TABLE dev.initiative_group from {settings.postgrest_authenticated_role};
    """)

    op.execute(f"""
        REVOKE ALL ON TABLE dev.user_task_counter from {settings.postgrest_authenticated_role};
    """)
    
    

def downgrade() -> None:
    pass
