"""add context document

Revision ID: 32795b3b5f76
Revises: 33de8a75753d
Create Date: 2025-05-02 10:05:29.044695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from src.config import settings

# revision identifiers, used by Alembic.
revision: str = '32795b3b5f76'
down_revision: Union[str, None] = '33de8a75753d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'context_document',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['private.users.id'], ondelete='cascade'),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['dev.workspace.id'], ondelete='cascade'),
        sa.PrimaryKeyConstraint('id'),
        schema='dev'
    )

    op.alter_column(
        "context_document",
        "user_id",
        schema="dev",
        server_default=sa.text("dev.get_user_id_from_jwt()"),
    )

    op.execute(
        f"""
            ALTER TABLE dev.context_document ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY context_document_policy ON dev.context_document
                USING (user_id = dev.get_user_id_from_jwt())
                WITH CHECK (user_id = dev.get_user_id_from_jwt()); 

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.context_document TO {settings.postgrest_authenticated_role};
        """
    )


def downgrade() -> None:
    op.drop_table('context_document', schema='dev')
