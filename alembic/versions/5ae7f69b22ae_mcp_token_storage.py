"""mcp token storage

Revision ID: 5ae7f69b22ae
Revises: 8fdf98a4b84f
Create Date: 2025-11-08 17:17:49.062845

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5ae7f69b22ae"
down_revision: Union[str, None] = "8fdf98a4b84f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create MCP OAuth storage table for persisting FastMCP tokens
    op.execute(
        """
        CREATE TABLE private.mcp_oauth_storage (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            collection VARCHAR(255),
            key VARCHAR(512) NOT NULL,
            value JSONB NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX idx_mcp_oauth_storage_expires_at
            ON private.mcp_oauth_storage (expires_at)
            WHERE expires_at IS NOT NULL;

        CREATE INDEX idx_mcp_oauth_storage_collection
            ON private.mcp_oauth_storage (collection);
        
        CREATE UNIQUE INDEX idx_unique_collection_key
        ON private.mcp_oauth_storage (collection, key)
        WHERE collection IS NOT NULL;

        CREATE UNIQUE INDEX idx_unique_null_collection_key
        ON private.mcp_oauth_storage (key)
        WHERE collection IS NULL;
    """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS private.idx_unique_null_collection_key;")
    op.execute("DROP INDEX IF EXISTS private.idx_unique_collection_key;")
    op.execute("DROP TABLE IF EXISTS private.mcp_oauth_storage CASCADE;")
