"""identifier function fix

Revision ID: 3d9b35a13bd1
Revises: 4dc40be08149
Create Date: 2025-05-28 08:51:18.690792

"""
from textwrap import dedent
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '3d9b35a13bd1'
down_revision: Union[str, None] = '4dc40be08149'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
                    NEW.user_id = dev.get_user_id_from_jwt();
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
                    NEW.user_id = dev.get_user_id_from_jwt();
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
