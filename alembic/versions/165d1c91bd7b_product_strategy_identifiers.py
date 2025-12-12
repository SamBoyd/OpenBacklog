"""product strategy identifiers

Revision ID: 165d1c91bd7b
Revises: 70115a3aa83f
Create Date: 2025-12-12 12:24:15.644076

"""

from textwrap import dedent
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from src.config import settings

revision: str = "165d1c91bd7b"
down_revision: Union[str, None] = "70115a3aa83f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ENTITY_CONFIGS = [
    {
        "name": "pillar",
        "table": "strategic_pillars",
        "prefix": "P",
        "needs_column": True,
    },
    {
        "name": "outcome",
        "table": "product_outcomes",
        "prefix": "O",
        "needs_column": True,
    },
    {
        "name": "theme",
        "table": "roadmap_themes",
        "prefix": "T",
        "needs_column": True,
    },
    {
        "name": "hero",
        "table": "heroes",
        "prefix": "H",
        "needs_column": False,
    },
    {
        "name": "villain",
        "table": "villains",
        "prefix": "V",
        "needs_column": False,
    },
    {
        "name": "conflict",
        "table": "conflicts",
        "prefix": "C",
        "needs_column": False,
    },
]


def upgrade() -> None:
    op.execute("SET search_path TO dev, private, public;")

    for config in ENTITY_CONFIGS:
        name = config["name"]
        table = config["table"]
        prefix = config["prefix"]
        needs_column = config["needs_column"]

        if needs_column:
            op.add_column(
                table,
                sa.Column("identifier", sa.String(20), nullable=True),
                schema="dev",
            )

        op.execute(
            dedent(
                f"""
                CREATE TABLE IF NOT EXISTS dev.user_{name}_counter (
                    user_id UUID PRIMARY KEY REFERENCES private.users (id) ON DELETE CASCADE,
                    last_value INT NOT NULL DEFAULT 0
                );

                ALTER TABLE dev.user_{name}_counter ENABLE ROW LEVEL SECURITY;

                DROP POLICY IF EXISTS user_{name}_counter_policy ON dev.user_{name}_counter;
                CREATE POLICY user_{name}_counter_policy ON dev.user_{name}_counter
                    USING (user_id = private.get_user_id_from_jwt())
                    WITH CHECK (user_id = private.get_user_id_from_jwt());

                GRANT SELECT, UPDATE, INSERT ON TABLE dev.user_{name}_counter TO {settings.postgrest_authenticated_role};
                """
            )
        )

        op.alter_column(
            f"user_{name}_counter",
            "user_id",
            schema="dev",
            server_default=sa.text("private.get_user_id_from_jwt()"),
        )

        op.execute(
            dedent(
                f"""
                CREATE OR REPLACE FUNCTION dev.set_{name}_identifier()
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
                INSERT INTO dev.user_{name}_counter(user_id, last_value)
                    VALUES (NEW.user_id, 0)
                    ON CONFLICT (user_id) DO NOTHING;

                -- 2) Fetch & increment the last_value in one shot (atomic)
                UPDATE dev.user_{name}_counter
                    SET last_value = last_value + 1
                    WHERE user_id = NEW.user_id
                    RETURNING last_value INTO new_value;

                -- 3) Build the identifier string
                NEW.identifier = '{prefix}-' || to_char(new_value, 'FM000');

                RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """
            )
        )

        op.execute(
            dedent(
                f"""
                DROP TRIGGER IF EXISTS trg_{name}_identifier ON dev.{table};
                CREATE TRIGGER trg_{name}_identifier
                BEFORE INSERT ON dev.{table}
                FOR EACH ROW
                EXECUTE FUNCTION dev.set_{name}_identifier();
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

    _backfill_existing_records()

    for config in ENTITY_CONFIGS:
        if config["needs_column"]:
            op.alter_column(
                config["table"],
                "identifier",
                nullable=False,
                schema="dev",
            )

            op.create_unique_constraint(
                f"uq_{config['table']}_workspace_id_identifier",
                config["table"],
                ["workspace_id", "identifier"],
                schema="dev",
            )


def _backfill_existing_records() -> None:
    """Backfill identifiers for any existing records."""
    for config in ENTITY_CONFIGS:
        name = config["name"]
        table = config["table"]
        prefix = config["prefix"]

        op.execute(
            dedent(
                f"""
                DO $$
                DECLARE
                    rec RECORD;
                    new_value INT;
                BEGIN
                    FOR rec IN
                        SELECT id, user_id
                        FROM dev.{table}
                        WHERE identifier IS NULL OR identifier = ''
                        ORDER BY created_at
                    LOOP
                        INSERT INTO dev.user_{name}_counter(user_id, last_value)
                            VALUES (rec.user_id, 0)
                            ON CONFLICT (user_id) DO NOTHING;

                        UPDATE dev.user_{name}_counter
                            SET last_value = last_value + 1
                            WHERE user_id = rec.user_id
                            RETURNING last_value INTO new_value;

                        UPDATE dev.{table}
                            SET identifier = '{prefix}-' || to_char(new_value, 'FM000')
                            WHERE id = rec.id;
                    END LOOP;
                END;
                $$;
                """
            )
        )


def downgrade() -> None:
    op.execute("SET search_path TO dev, private, public;")

    for config in ENTITY_CONFIGS:
        name = config["name"]
        table = config["table"]
        needs_column = config["needs_column"]

        if needs_column:
            op.drop_constraint(
                f"uq_{config['table']}_workspace_id_identifier",
                config["table"],
                schema="dev",
            )
            op.drop_column(table, "identifier", schema="dev")

        op.execute(f"DROP TRIGGER IF EXISTS trg_{name}_identifier ON dev.{table};")
        op.execute(f"DROP FUNCTION IF EXISTS dev.set_{name}_identifier();")
        op.execute(f"DROP TABLE IF EXISTS dev.user_{name}_counter;")
