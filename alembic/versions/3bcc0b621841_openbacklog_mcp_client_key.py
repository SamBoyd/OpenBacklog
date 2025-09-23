"""openbacklog mcp client key

Revision ID: 3bcc0b621841
Revises: dcb115bfa0ce
Create Date: 2025-07-25 12:31:46.551109

"""
from textwrap import dedent
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3bcc0b621841'
down_revision: Union[str, None] = 'dcb115bfa0ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add OPENBACKLOG to APIProvider enum
    op.execute("ALTER TYPE dev.apiprovider ADD VALUE 'OPENBACKLOG'")
    
    # Add last_used_at column to user_key table
    op.add_column('user_key', 
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        schema='dev'
    )
    
    # Add access_token column to user_key table for storing full OpenBacklog tokens
    op.add_column('user_key', 
        sa.Column('access_token', sa.String(2048), nullable=True),
        schema='dev'
    )
    
    # Create function to extract key_id from JWT
    op.execute(
        dedent(
            """
            CREATE OR REPLACE FUNCTION private.get_key_id_from_jwt() 
            RETURNS uuid AS $$
            DECLARE
                key_uuid uuid;
            BEGIN
                SELECT uuid(current_setting('request.jwt.claims', true)::json->>'key_id')
                INTO key_uuid;
                RETURN key_uuid;
            EXCEPTION
                WHEN OTHERS THEN
                    RETURN NULL;
            END;
            $$ LANGUAGE plpgsql STABLE SECURITY DEFINER;
            """
        )
    )
    
    # Create function to update last_used_at for OpenBacklog tokens when data is accessed
    op.execute(
        dedent(
            """
            CREATE OR REPLACE FUNCTION private.update_user_key_last_used()
            RETURNS trigger AS $$
            DECLARE
                user_uuid uuid;
                key_uuid uuid;
            BEGIN
                -- Get user ID from JWT
                user_uuid := private.get_user_id_from_jwt();
                
                -- Get key ID from JWT
                key_uuid := private.get_key_id_from_jwt();
                
                -- Update last_used_at for the specific token if key_id is present
                IF key_uuid IS NOT NULL THEN
                    UPDATE dev.user_key 
                    SET last_used_at = NOW()
                    WHERE id = key_uuid 
                      AND user_id = user_uuid;
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql SECURITY DEFINER;
            """
        )
    )
    
    # Create triggers on tables that should update last_used_at when accessed via MCP
    op.execute(
        dedent(
            """
            CREATE TRIGGER update_openbacklog_last_used_initiative
                AFTER INSERT OR UPDATE OR DELETE ON dev.initiative
                FOR EACH ROW
                EXECUTE FUNCTION private.update_user_key_last_used();
            """
        )
    )
    
    op.execute(
        dedent(
            """
            CREATE TRIGGER update_openbacklog_last_used_task
                AFTER INSERT OR UPDATE OR DELETE ON dev.task
                FOR EACH ROW
                EXECUTE FUNCTION private.update_user_key_last_used();
            """
        )
    )
    
    op.execute(
        dedent(
            """
            CREATE TRIGGER update_openbacklog_last_used_checklist
                AFTER INSERT OR UPDATE OR DELETE ON dev.checklist
                FOR EACH ROW
                EXECUTE FUNCTION private.update_user_key_last_used();
            """
        )
    )


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_openbacklog_last_used_checklist ON dev.checklist")
    op.execute("DROP TRIGGER IF EXISTS update_openbacklog_last_used_task ON dev.task")  
    op.execute("DROP TRIGGER IF EXISTS update_openbacklog_last_used_initiative ON dev.initiative")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS private.update_user_key_last_used()")
    op.execute("DROP FUNCTION IF EXISTS private.get_key_id_from_jwt()")
    
    # Remove columns
    op.drop_column('user_key', 'access_token', schema='dev')
    op.drop_column('user_key', 'last_used_at', schema='dev')
    
    # Note: Cannot remove enum value from PostgreSQL enum type easily
    # This would require recreating the enum type, which is complex
    # For now, we'll leave the OPENBACKLOG value in the enum
