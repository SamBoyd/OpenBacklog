"""user_id default from jwt

Revision ID: ec1e3cef3cf6
Revises: de6f4e4e0398
Create Date: 2025-01-05 08:30:59.850334

"""

from textwrap import dedent


from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from src.config import settings

# revision identifiers, used by Alembic.
revision: str = "ec1e3cef3cf6"
down_revision: Union[str, None] = "de6f4e4e0398"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        dedent(
            """
        CREATE OR REPLACE FUNCTION dev.get_user_id_from_jwt() 
        RETURNS uuid AS $$
        DECLARE
            user_uuid uuid;
        BEGIN
            SELECT user_id 
            INTO user_uuid
            FROM private.oauth_account
            WHERE account_id = (current_setting('request.jwt.claims', true)::json->>'sub');
            RETURN user_uuid;
        END;
        $$ LANGUAGE plpgsql STABLE SECURITY DEFINER;
            """
        )
    )

    op.alter_column(
        "checklist",
        "user_id",
        schema="dev",
        server_default=sa.text("dev.get_user_id_from_jwt()"),
    )

    op.alter_column(
        "task",
        "user_id",
        schema="dev",
        server_default=sa.text("dev.get_user_id_from_jwt()"),
    )

    op.alter_column(
        "initiative",
        "user_id",
        schema="dev",
        server_default=sa.text("dev.get_user_id_from_jwt()"),
    )

    op.execute(
        dedent(
            """
                ALTER TABLE dev.task ENABLE ROW LEVEL SECURITY;
                ALTER TABLE dev.initiative ENABLE ROW LEVEL SECURITY;
                ALTER TABLE dev.checklist ENABLE ROW LEVEL SECURITY;
            """
        )
    )

    op.execute(
        dedent(
            """
                CREATE POLICY task_policy ON dev.task
                USING (user_id = dev.get_user_id_from_jwt())
                WITH CHECK (user_id = dev.get_user_id_from_jwt()); 

                CREATE POLICY initiative_policy ON dev.initiative
                USING (user_id = dev.get_user_id_from_jwt())
                WITH CHECK (user_id = dev.get_user_id_from_jwt()); 

                CREATE POLICY checklist_policy ON dev.checklist
                USING (user_id = dev.get_user_id_from_jwt())
                WITH CHECK (user_id = dev.get_user_id_from_jwt());
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
    pass
