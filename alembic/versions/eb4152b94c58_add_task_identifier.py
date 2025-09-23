"""add task identifier

Revision ID: eb4152b94c58
Revises: ec1e3cef3cf6
Create Date: 2025-01-04 13:30:59.568409

"""

from textwrap import dedent
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from src.config import settings

# revision identifiers, used by Alembic.
revision: str = "eb4152b94c58"
down_revision: Union[str, None] = "ec1e3cef3cf6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        dedent(
            f"""
            CREATE TABLE dev.user_task_counter (
            user_id UUID PRIMARY KEY REFERENCES private.users (id) ON DELETE CASCADE,
            last_value INT NOT NULL DEFAULT 0
            );

            ALTER TABLE dev.user_task_counter ENABLE ROW LEVEL SECURITY;

            CREATE POLICY user_task_counter_policy ON dev.user_task_counter
            USING (user_id = dev.get_user_id_from_jwt())
            WITH CHECK (user_id = dev.get_user_id_from_jwt());  

            GRANT SELECT, UPDATE, INSERT ON TABLE dev.user_task_counter TO {settings.postgrest_authenticated_role};
        """
        )
    )

    op.alter_column(
        "user_task_counter",
        "user_id",
        schema="dev",
        server_default=sa.text("dev.get_user_id_from_jwt()"),
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
                IF NEW.identifier IS NOT NULL THEN
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

    op.execute(
        dedent(
            """
                CREATE TRIGGER trg_task_identifier
                BEFORE INSERT ON dev.task
                FOR EACH ROW
                EXECUTE FUNCTION dev.set_task_identifier();
            """
        )
    )

    op.execute(
        dedent(
            f"""
            GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dev TO {settings.postgrest_authenticated_role};
            """
        )
    )


def downgrade() -> None:
    op.execute("SET search_path TO private, public;")
    op.execute("DROP TRIGGER trg_task_identifier ON task;")
    op.execute("DROP FUNCTION set_task_identifier();")
    op.drop_table("dev.user_task_counter")
