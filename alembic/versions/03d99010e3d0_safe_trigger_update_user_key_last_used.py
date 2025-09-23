"""safe trigger update_user_key_last_used

Revision ID: 03d99010e3d0
Revises: 3bcc0b621841
Create Date: 2025-07-31 09:00:55.646560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '03d99010e3d0'
down_revision: Union[str, None] = '3bcc0b621841'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update the trigger function to handle cases where JWT claims are not set
    op.execute("""
        CREATE OR REPLACE FUNCTION private.update_user_key_last_used()
        RETURNS trigger AS $$
        DECLARE
            user_uuid uuid;
            key_uuid uuid;
        BEGIN
            -- Safely get user ID from JWT, handling cases where claims aren't set
            BEGIN
                user_uuid := private.get_user_id_from_jwt();
            EXCEPTION WHEN OTHERS THEN
                -- If JWT claims are not set or invalid, skip the update
                RETURN NEW;
            END;
            
            -- Safely get key ID from JWT, handling cases where claims aren't set  
            BEGIN
                key_uuid := private.get_key_id_from_jwt();
            EXCEPTION WHEN OTHERS THEN
                -- If key_id is not in JWT claims or invalid, skip the update
                RETURN NEW;
            END;
            
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
    """)


def downgrade() -> None:
    # Revert to the original trigger function
    op.execute("""
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
    """)
