"""invalidate access token

Revision ID: 07c6d6036168
Revises: 34e11907e5f4
Create Date: 2025-09-16 18:22:00.830825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.config import settings


# revision identifiers, used by Alembic.
revision: str = '07c6d6036168'
down_revision: Union[str, None] = '34e11907e5f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create dev.verify_token function to validate tokens against the database
    op.execute("""
        CREATE OR REPLACE FUNCTION dev.verify_token()
        RETURNS void AS $$
        DECLARE
            auth_header text;
            token_part text;
            token_exists boolean := false;
        BEGIN
            -- Extract the Authorization header from the request
            BEGIN
                auth_header := current_setting('request.headers', true)::json->>'authorization';
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE EXCEPTION 'Invalid or missing authorization header';
            END;

            -- Check if we have an Authorization header
            IF auth_header IS NULL THEN
                RAISE EXCEPTION 'Missing authorization header';
            END IF;

            -- Extract the token from "Bearer <token>" format
            IF auth_header LIKE 'Bearer %' THEN
                token_part := substring(auth_header from 8); -- Remove "Bearer " prefix
            ELSE
                -- Could also handle cookie-based tokens here if needed
                RAISE EXCEPTION 'Invalid authorization header format';
            END IF;

            -- Check if the token exists in the access_token table (for session tokens)
            SELECT EXISTS(
                SELECT 1
                FROM private.access_token
                WHERE token = token_part
            ) INTO token_exists;

            -- If not found in access_token, check user_key table for OpenBacklog API tokens
            IF NOT token_exists THEN
                SELECT EXISTS(
                    SELECT 1
                    FROM dev.user_key
                    WHERE access_token = token_part
                    AND provider = 'OPENBACKLOG'
                    AND is_valid = true
                    AND deleted_at IS NULL
                ) INTO token_exists;
            END IF;

            -- If token not found anywhere, raise exception
            IF NOT token_exists THEN
                RAISE EXCEPTION 'Invalid or expired token';
            END IF;

            -- If we reach here, token is valid - function completes without error
        EXCEPTION
            WHEN OTHERS THEN
                -- Re-raise any exception that occurred
                RAISE;
        END;
        $$ LANGUAGE plpgsql STABLE SECURITY DEFINER;
    """)

    # Grant execute permission to PostgREST roles
    op.execute(f"GRANT EXECUTE ON FUNCTION dev.verify_token() TO {settings.postgrest_authenticator__role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION dev.verify_token() TO {settings.postgrest_authenticated_role}")


def downgrade() -> None:
    # Remove the function and schema
    op.execute("DROP FUNCTION IF EXISTS dev.verify_token()")
