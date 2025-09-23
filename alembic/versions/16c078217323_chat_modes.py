"""chat modes

Revision ID: 16c078217323
Revises: 3d9b35a13bd1
Create Date: 2025-05-30 20:08:00.647184

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '16c078217323'
down_revision: Union[str, None] = '3d9b35a13bd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE dev.chatmode AS ENUM ('DISCUSS', 'EDIT')")
    op.add_column("ai_improvement_job", sa.Column("mode", sa.Enum("DISCUSS", "EDIT", name="chatmode", schema="dev"), nullable=True), schema="dev")


def downgrade() -> None:
    op.drop_column("ai_improvement_job", "mode")
