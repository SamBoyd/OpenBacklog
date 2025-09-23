"""get_user_from_jwt to private

Revision ID: 1623674e8a8a
Revises: 1c3f36ec02bf
Create Date: 2025-05-12 11:35:05.098328

"""

from textwrap import dedent
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from src.models import InitiativeGroup


# revision identifiers, used by Alembic.
revision: str = "1623674e8a8a"
down_revision: Union[str, None] = "1c3f36ec02bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


tables = [
    "ai_improvement_job",
    "checklist",
    "context_document",
    "field_definition",
    "group",
    "initiative",
    "initiative_group",
    "task",
    "user_initiative_counter",
    "user_task_counter",
    "workspace",
    "user_key", # This was missing the default on user_id
]

# Server defaults in dev schema
# table                   | column      | server_default
# ai_improvement_job      | user_id     | private.get_user_id_from_jwt()
# checklist               | user_id     | private.get_user_id_from_jwt()
# context_document        | user_id     | private.get_user_id_from_jwt()
# field_definition        | user_id     | private.get_user_id_from_jwt()
# group                   | user_id     | dev.get_user_id_from_jwt()
# initiative              | user_id     | dev.get_user_id_from_jwt()
# initiative_group        | user_id     | dev.get_user_id_from_jwt()
# task                    | user_id     | dev.get_user_id_from_jwt()
# user_initiative_counter | user_id     | dev.get_user_id_from_jwt()
# user_task_counter       | user_id     | dev.get_user_id_from_jwt()
# workspace               | user_id     | dev.get_user_id_from_jwt()

# Policies in dev schema (select * from pg_policies)
#
# SELECT table_name,
#   column_name,
#   column_default
# FROM information_schema.columns
# WHERE table_schema = 'public'
#   AND column_default = 'dev.get_user_id_from_jwt()'
# ORDER BY table_name;
#
#  schemaname |        tablename        |           policyname           | permissive |  roles   |  cmd   |                  qual                 |                      with_check
# ------------+-------------------------+-------------------------------+------------+----------+--------+----------------------------------------+-----------------------------------------
# dev        | checklist               | checklist_policy               | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())
# dev        | user_task_counter       | user_task_counter_policy       | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())
# dev        | user_initiative_counter | user_initiative_counter_policy | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())
# dev        | ai_improvement_job      | ai_improvement_job_policy      | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())
# dev        | workspace               | no_multiple_workspace_for_user | PERMISSIVE | {public} | INSERT |                                        | (NOT (EXISTS ( SELECT 1                             +
#            |                         |                                |            |          |        |                                        |    FROM dev.workspace ws                            +
#            |                         |                                |            |          |        |                                        |   WHERE (ws.user_id = dev.get_user_id_from_jwt()))))
# dev        | workspace               | user_workspace_policy          | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())
# dev        | user_key                | user_key_policy                | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())
# dev        | context_document        | context_document_policy        | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())
# dev        | task                    | task_policy                    | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())
# dev        | field_definition        | field_definition_policy        | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())
# dev        | initiative              | initiative_policy              | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())
# dev        | group                   | group_policy                   | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())
# dev        | InitiativeGroup         | initiative_group_policy        | PERMISSIVE | {public} | ALL    | (user_id = dev.get_user_id_from_jwt()) | (user_id = dev.get_user_id_from_jwt())


def upgrade() -> None:
    # Create new function in private schema
    op.execute(
        dedent(
            """
                CREATE FUNCTION private.get_user_id_from_jwt() 
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

    # Rename policy on table workspace to conform with naming convention
    op.execute(f"ALTER POLICY user_workspace_policy ON dev.workspace RENAME TO workspace_policy;")

    # Drop existing policies that depend on dev.get_user_id_from_jwt()
    for table in tables:
        policy_name = f"{table}_policy"
        op.execute(f"DROP POLICY {policy_name} ON dev.{table};")
    
    op.execute("DROP POLICY no_multiple_workspace_for_user ON dev.workspace;")

    # Update column defaults to use private.get_user_id_from_jwt()
    for table in tables:
        op.alter_column(
            table,
            "user_id",
            server_default=sa.text("private.get_user_id_from_jwt()"),
            schema="dev",
        )

    # Create new policies with the new function
    for table in tables:
        policy_name = f"{table}_policy"
        op.execute(
            dedent(
                f"""
                    CREATE POLICY {policy_name} ON dev.{table}
                    USING (user_id = private.get_user_id_from_jwt())
                    WITH CHECK (user_id = private.get_user_id_from_jwt());  
                """
            )
        )
    
    op.execute(
        dedent(
            """
            CREATE POLICY no_multiple_workspace_for_user ON dev.workspace
            FOR INSERT
            WITH CHECK (
                NOT EXISTS (
                    SELECT 1 FROM dev.workspace AS ws
                    WHERE ws.user_id = private.get_user_id_from_jwt()
                )
            );
            """
        )
    )

    # Finally drop the original function now that nothing depends on it
    op.execute("DROP FUNCTION dev.get_user_id_from_jwt();")


def downgrade() -> None:
    pass
