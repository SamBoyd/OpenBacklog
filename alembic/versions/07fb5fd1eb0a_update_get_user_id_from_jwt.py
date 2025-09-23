"""update get_user_id_from_jwt

Revision ID: 07fb5fd1eb0a
Revises: 78544b52554c
Create Date: 2025-07-14 12:16:46.341971

"""

from textwrap import dedent
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "07fb5fd1eb0a"
down_revision: Union[str, None] = "78544b52554c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        dedent(
            """
                CREATE OR REPLACE FUNCTION private.get_user_id_from_jwt() 
                RETURNS uuid AS $$
                DECLARE
                    user_uuid uuid;
                BEGIN
                    SELECT user_id
                    INTO user_uuid
                    FROM private.oauth_account
                    WHERE user_id = uuid(current_setting('request.jwt.claims', true)::json->>'sub');
                    RETURN user_uuid;
                END;
                $$ LANGUAGE plpgsql STABLE SECURITY DEFINER;
            """
        )
    )

    op.execute(
        dedent(
            """
                CREATE OR REPLACE FUNCTION dev.set_initiative_identifier() 
                RETURNS TRIGGER AS $$
                DECLARE
                new_value INT;
                BEGIN
                -- If identifier is already supplied, skip
                IF NEW.identifier IS NOT NULL AND NEW.identifier != '' THEN
                    RETURN NEW;
                END IF;

                RAISE NOTICE 'NEW.user_id initial: %', NEW.user_id;

                -- Ensure user_id is set from JWT if not already set
                IF NEW.user_id IS NULL THEN
                    NEW.user_id = private.get_user_id_from_jwt();
                END IF;
                
                RAISE NOTICE 'NEW.user_id final: %', NEW.user_id;

                -- 1) Lock the counter for the specific user 
                --    Insert a row if it doesn't exist (i.e., first time for that user)
                INSERT INTO dev.user_initiative_counter(user_id, last_value)
                    VALUES (NEW.user_id, 0)
                    ON CONFLICT (user_id) DO NOTHING; 
                
                -- 2) Fetch & increment the last_value in one shot (atomic)
                UPDATE dev.user_initiative_counter
                    SET last_value = last_value + 1
                    WHERE user_id = NEW.user_id
                    RETURNING last_value INTO new_value;
                
                -- 3) Build the identifier string
                NEW.identifier = 'I-' || to_char(new_value, 'FM000');  -- e.g. "I-001", "I-123"
                
                RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """
        )
    )

    op.execute(
        dedent(
            """
                CREATE OR REPLACE FUNCTION dev.set_task_identifier() 
                RETURNS TRIGGER AS $$
                DECLARE
                new_value INT;
                BEGIN
                -- If identifier is already supplied, skip
                IF NEW.identifier IS NOT NULL AND NEW.identifier != '' THEN
                    RETURN NEW;
                END IF;

                -- Ensure user_id is set from JWT if not already set
                IF NEW.user_id IS NULL THEN
                    NEW.user_id = private.get_user_id_from_jwt();
                END IF;
                
                -- 1) Lock the counter for the specific user
                --    Insert a row if it doesn't exist (i.e., first time for that user)
                INSERT INTO dev.user_task_counter(user_id, last_value)
                    VALUES (NEW.user_id, 0)
                    ON CONFLICT (user_id) DO NOTHING; 
                
                -- 2) Fetch & increment the last_value in one shot (atomic)
                UPDATE dev.user_task_counter
                    SET last_value = last_value + 1
                    WHERE user_id = NEW.user_id
                    RETURNING last_value INTO new_value;
                
                -- 3) Build the identifier string
                NEW.identifier = 'TM-' || to_char(new_value, 'FM000');  -- e.g. "TM-001", "TM-123"
                
                RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """
        )
    )

def downgrade() -> None:
    pass
