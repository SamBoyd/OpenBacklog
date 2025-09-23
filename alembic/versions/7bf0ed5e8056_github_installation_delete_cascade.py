"""github installation delete cascade

Revision ID: 7bf0ed5e8056
Revises: 91eb68186629
Create Date: 2025-08-13 17:47:32.491502

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7bf0ed5e8056"
down_revision: Union[str, None] = "91eb68186629"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
            ALTER TABLE "github_installation"
            DROP CONSTRAINT "github_installation_workspace_id_fkey",
            ADD CONSTRAINT "github_installation_workspace_id_fkey"
            FOREIGN KEY ("workspace_id")
            REFERENCES "dev"."workspace"(id)
            ON DELETE CASCADE;
    """
    )


def downgrade() -> None:
    pass
