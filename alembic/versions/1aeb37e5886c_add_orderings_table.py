"""add orderings table

Revision ID: 1aeb37e5886c
Revises: 3d9b35a13bd1
Create Date: 2025-05-30 11:39:44.397464

"""

from textwrap import dedent
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from src.config import settings

# revision identifiers, used by Alembic.
revision: str = "1aeb37e5886c"
down_revision: Union[str, None] = "3d9b35a13bd1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ContextType = (
    "GROUP",
    "STATUS_LIST",
    "TASK_CHECKLIST",
)

EntityType = (
    "INITIATIVE",
    "TASK",
    "CHECKLIST",
)


def upgrade() -> None:
    #  alter EntityType to include TASK_CHECKLIST
    op.execute('ALTER TYPE dev.entitytype ADD VALUE IF NOT EXISTS \'CHECKLIST\'')

    op.create_table(
        "orderings",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False, server_default=sa.text("private.get_user_id_from_jwt()")),
        sa.Column(
            "context_type",
            sa.Enum(*ContextType, name="contexttype", schema="dev", native_enum=True),
            nullable=False,
        ),
        sa.Column("context_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "entity_type",
            sa.Enum(*EntityType, name="orderings_entitytype", schema="dev", native_enum=True),
            nullable=False,
        ),
        sa.Column("entity_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.String, nullable=False),
        sa.Column("workspace_id", sa.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["dev.workspace.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "context_type",
            "context_id",
            "entity_type",
            "entity_id",
            name="uq_context_entity_once",
        ),
        schema="dev",
    )

    op.create_index(
        "ix_context_position",
        "orderings",
        ["context_type", "context_id", "entity_type", "position"],
        schema="dev",
    )
    op.create_index(
        "ix_entity_lookup",
        "orderings",
        ["entity_type", "entity_id"],
        schema="dev",
    )

    op.execute(
        dedent(
            f"""
            ALTER TABLE dev.orderings ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY orderings_policy ON dev.orderings
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt()); 

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.orderings TO {settings.postgrest_authenticated_role};
            """
        )
    )

def downgrade() -> None:
    op.drop_index("ix_entity_lookup", table_name="orderings", schema="dev")
    op.drop_index("ix_context_position", table_name="orderings", schema="dev")
    op.drop_table("orderings", schema="dev")
    op.execute('DROP TYPE dev.contexttype')
