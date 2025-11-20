"""add narrative models

Revision ID: 980e54f90a8b
Revises: 5ae7f69b22ae
Create Date: 2025-11-19 12:09:57.907983

"""

from textwrap import dedent
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from src.config import settings

# revision identifiers, used by Alembic.
revision: str = "980e54f90a8b"
down_revision: Union[str, None] = "5ae7f69b22ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create PostgreSQL enums
    op.execute(
        "CREATE TYPE dev.villain_type AS ENUM ('EXTERNAL', 'INTERNAL', 'TECHNICAL', 'WORKFLOW', 'OTHER')"
    )
    op.execute(
        "CREATE TYPE dev.conflict_status AS ENUM ('OPEN', 'ESCALATING', 'RESOLVING', 'RESOLVED')"
    )
    op.execute(
        "CREATE TYPE dev.significance AS ENUM ('MINOR', 'MODERATE', 'MAJOR', 'CLIMACTIC')"
    )

    # Create workspace-based counter tables
    op.execute(
        dedent(
            f"""
            CREATE TABLE dev.workspace_hero_counter (
                workspace_id UUID PRIMARY KEY REFERENCES dev.workspace (id) ON DELETE CASCADE,
                last_value INT NOT NULL DEFAULT 0
            );

            ALTER TABLE dev.workspace_hero_counter ENABLE ROW LEVEL SECURITY;

            CREATE POLICY workspace_hero_counter_policy ON dev.workspace_hero_counter
                USING (workspace_id IN (SELECT id FROM dev.workspace WHERE user_id = private.get_user_id_from_jwt()))
                WITH CHECK (workspace_id IN (SELECT id FROM dev.workspace WHERE user_id = private.get_user_id_from_jwt()));

            GRANT SELECT, UPDATE, INSERT ON TABLE dev.workspace_hero_counter TO {settings.postgrest_authenticated_role};
            """
        )
    )

    op.execute(
        dedent(
            f"""
            CREATE TABLE dev.workspace_villain_counter (
                workspace_id UUID PRIMARY KEY REFERENCES dev.workspace (id) ON DELETE CASCADE,
                last_value INT NOT NULL DEFAULT 0
            );

            ALTER TABLE dev.workspace_villain_counter ENABLE ROW LEVEL SECURITY;

            CREATE POLICY workspace_villain_counter_policy ON dev.workspace_villain_counter
                USING (workspace_id IN (SELECT id FROM dev.workspace WHERE user_id = private.get_user_id_from_jwt()))
                WITH CHECK (workspace_id IN (SELECT id FROM dev.workspace WHERE user_id = private.get_user_id_from_jwt()));

            GRANT SELECT, UPDATE, INSERT ON TABLE dev.workspace_villain_counter TO {settings.postgrest_authenticated_role};
            """
        )
    )

    op.execute(
        dedent(
            f"""
            CREATE TABLE dev.workspace_conflict_counter (
                workspace_id UUID PRIMARY KEY REFERENCES dev.workspace (id) ON DELETE CASCADE,
                last_value INT NOT NULL DEFAULT 0
            );

            ALTER TABLE dev.workspace_conflict_counter ENABLE ROW LEVEL SECURITY;

            CREATE POLICY workspace_conflict_counter_policy ON dev.workspace_conflict_counter
                USING (workspace_id IN (SELECT id FROM dev.workspace WHERE user_id = private.get_user_id_from_jwt()))
                WITH CHECK (workspace_id IN (SELECT id FROM dev.workspace WHERE user_id = private.get_user_id_from_jwt()));

            GRANT SELECT, UPDATE, INSERT ON TABLE dev.workspace_conflict_counter TO {settings.postgrest_authenticated_role};
            """
        )
    )

    op.execute(
        dedent(
            f"""
            CREATE TABLE dev.workspace_turning_point_counter (
                workspace_id UUID PRIMARY KEY REFERENCES dev.workspace (id) ON DELETE CASCADE,
                last_value INT NOT NULL DEFAULT 0
            );

            ALTER TABLE dev.workspace_turning_point_counter ENABLE ROW LEVEL SECURITY;

            CREATE POLICY workspace_turning_point_counter_policy ON dev.workspace_turning_point_counter
                USING (workspace_id IN (SELECT id FROM dev.workspace WHERE user_id = private.get_user_id_from_jwt()))
                WITH CHECK (workspace_id IN (SELECT id FROM dev.workspace WHERE user_id = private.get_user_id_from_jwt()));

            GRANT SELECT, UPDATE, INSERT ON TABLE dev.workspace_turning_point_counter TO {settings.postgrest_authenticated_role};
            """
        )
    )

    # Create trigger functions for identifier generation
    op.execute(
        dedent(
            """
            CREATE OR REPLACE FUNCTION dev.set_hero_identifier() 
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

                -- 1) Lock the counter for the specific workspace
                --    Insert a row if it doesn't exist (i.e., first time for that workspace)
                INSERT INTO dev.workspace_hero_counter(workspace_id, last_value)
                    VALUES (NEW.workspace_id, 0)
                    ON CONFLICT (workspace_id) DO NOTHING; 
                
                -- 2) Fetch & increment the last_value in one shot (atomic)
                UPDATE dev.workspace_hero_counter
                    SET last_value = last_value + 1
                    WHERE workspace_id = NEW.workspace_id
                    RETURNING last_value INTO new_value;
                
                -- 3) Build the identifier string
                NEW.identifier = 'H-' || to_char(new_value, 'FM0000');  -- e.g. "H-0001", "H-2003"
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )

    op.execute(
        dedent(
            """
            CREATE OR REPLACE FUNCTION dev.set_villain_identifier() 
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

                -- 1) Lock the counter for the specific workspace
                INSERT INTO dev.workspace_villain_counter(workspace_id, last_value)
                    VALUES (NEW.workspace_id, 0)
                    ON CONFLICT (workspace_id) DO NOTHING; 
                
                -- 2) Fetch & increment the last_value in one shot (atomic)
                UPDATE dev.workspace_villain_counter
                    SET last_value = last_value + 1
                    WHERE workspace_id = NEW.workspace_id
                    RETURNING last_value INTO new_value;
                
                -- 3) Build the identifier string
                NEW.identifier = 'V-' || to_char(new_value, 'FM0000');  -- e.g. "V-0001", "V-2003"
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )

    op.execute(
        dedent(
            """
            CREATE OR REPLACE FUNCTION dev.set_conflict_identifier() 
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

                -- 1) Lock the counter for the specific workspace
                INSERT INTO dev.workspace_conflict_counter(workspace_id, last_value)
                    VALUES (NEW.workspace_id, 0)
                    ON CONFLICT (workspace_id) DO NOTHING; 
                
                -- 2) Fetch & increment the last_value in one shot (atomic)
                UPDATE dev.workspace_conflict_counter
                    SET last_value = last_value + 1
                    WHERE workspace_id = NEW.workspace_id
                    RETURNING last_value INTO new_value;
                
                -- 3) Build the identifier string
                NEW.identifier = 'C-' || to_char(new_value, 'FM0000');  -- e.g. "C-0001", "C-2003"
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )

    op.execute(
        dedent(
            """
            CREATE OR REPLACE FUNCTION dev.set_turning_point_identifier() 
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

                -- 1) Lock the counter for the specific workspace
                INSERT INTO dev.workspace_turning_point_counter(workspace_id, last_value)
                    VALUES (NEW.workspace_id, 0)
                    ON CONFLICT (workspace_id) DO NOTHING; 
                
                -- 2) Fetch & increment the last_value in one shot (atomic)
                UPDATE dev.workspace_turning_point_counter
                    SET last_value = last_value + 1
                    WHERE workspace_id = NEW.workspace_id
                    RETURNING last_value INTO new_value;
                
                -- 3) Build the identifier string
                NEW.identifier = 'TP-' || to_char(new_value, 'FM0000');  -- e.g. "TP-0001", "TP-2003"
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )

    # Create heroes table
    op.create_table(
        "heroes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("identifier", sa.String(length=20), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("private.get_user_id_from_jwt()"),
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["dev.workspace.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["private.users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "workspace_id", "identifier", name="uq_heroes_workspace_id_identifier"
        ),
        sa.UniqueConstraint("workspace_id", "name", name="uq_heroes_workspace_id_name"),
        schema="dev",
    )

    op.create_index("ix_heroes_workspace_id", "heroes", ["workspace_id"], schema="dev")
    op.create_index("ix_heroes_identifier", "heroes", ["identifier"], schema="dev")
    op.create_index("ix_heroes_is_primary", "heroes", ["is_primary"], schema="dev")

    op.execute(
        dedent(
            f"""
            CREATE TRIGGER trg_hero_identifier
            BEFORE INSERT ON dev.heroes
            FOR EACH ROW
            EXECUTE FUNCTION dev.set_hero_identifier();


            ALTER TABLE dev.heroes ENABLE ROW LEVEL SECURITY;

            CREATE POLICY heroes_policy ON dev.heroes
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt());

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.heroes TO {settings.postgrest_authenticated_role};
            """
        )
    )

    # Create villains table
    villain_type_enum = postgresql.ENUM(
        "EXTERNAL",
        "INTERNAL",
        "TECHNICAL",
        "WORKFLOW",
        "OTHER",
        name="villain_type",
        schema="dev",
        create_type=False,
    )
    op.create_table(
        "villains",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("identifier", sa.String(length=20), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("private.get_user_id_from_jwt()"),
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("villain_type", villain_type_enum, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("is_defeated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["dev.workspace.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["private.users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "workspace_id", "identifier", name="uq_villains_workspace_id_identifier"
        ),
        sa.UniqueConstraint(
            "workspace_id", "name", name="uq_villains_workspace_id_name"
        ),
        sa.CheckConstraint(
            "severity >= 1 AND severity <= 5", name="ck_villains_severity_range"
        ),
        schema="dev",
    )

    op.create_index(
        "ix_villains_workspace_id", "villains", ["workspace_id"], schema="dev"
    )
    op.create_index("ix_villains_identifier", "villains", ["identifier"], schema="dev")
    op.create_index(
        "ix_villains_is_defeated", "villains", ["is_defeated"], schema="dev"
    )

    op.execute(
        dedent(
            f"""
            CREATE TRIGGER trg_villain_identifier
            BEFORE INSERT ON dev.villains
            FOR EACH ROW
            EXECUTE FUNCTION dev.set_villain_identifier();

            ALTER TABLE dev.villains ENABLE ROW LEVEL SECURITY;

            CREATE POLICY villains_policy ON dev.villains
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt());

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.villains TO {settings.postgrest_authenticated_role};
            """
        )
    )

    # Create conflicts table
    conflict_status_enum = postgresql.ENUM(
        "OPEN",
        "ESCALATING",
        "RESOLVING",
        "RESOLVED",
        name="conflict_status",
        schema="dev",
        create_type=False,
    )
    op.create_table(
        "conflicts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("identifier", sa.String(length=20), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("private.get_user_id_from_jwt()"),
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hero_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("villain_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status", conflict_status_enum, nullable=False, server_default="OPEN"
        ),
        sa.Column("story_arc_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolved_by_initiative_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["dev.workspace.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["private.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hero_id"], ["dev.heroes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["villain_id"], ["dev.villains.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["story_arc_id"], ["dev.roadmap_themes.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_initiative_id"], ["dev.initiative.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint(
            "workspace_id", "identifier", name="uq_conflicts_workspace_id_identifier"
        ),
        schema="dev",
    )

    op.create_index(
        "ix_conflicts_workspace_id", "conflicts", ["workspace_id"], schema="dev"
    )
    op.create_index(
        "ix_conflicts_identifier", "conflicts", ["identifier"], schema="dev"
    )
    op.create_index("ix_conflicts_status", "conflicts", ["status"], schema="dev")
    op.create_index("ix_conflicts_hero_id", "conflicts", ["hero_id"], schema="dev")
    op.create_index(
        "ix_conflicts_villain_id", "conflicts", ["villain_id"], schema="dev"
    )

    op.execute(
        dedent(
            f"""
            CREATE TRIGGER trg_conflict_identifier
            BEFORE INSERT ON dev.conflicts
            FOR EACH ROW
            EXECUTE FUNCTION dev.set_conflict_identifier();

            ALTER TABLE dev.conflicts ENABLE ROW LEVEL SECURITY;

            CREATE POLICY conflicts_policy ON dev.conflicts
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt());

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.conflicts TO {settings.postgrest_authenticated_role};
            """
        )
    )

    # Create turning_points table
    significance_enum = postgresql.ENUM(
        "MINOR",
        "MODERATE",
        "MAJOR",
        "CLIMACTIC",
        name="significance",
        schema="dev",
        create_type=False,
    )
    op.create_table(
        "turning_points",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("identifier", sa.String(length=20), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("private.get_user_id_from_jwt()"),
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "domain_event_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
        ),
        sa.Column("narrative_description", sa.Text(), nullable=False),
        sa.Column("significance", significance_enum, nullable=False),
        sa.Column("conflict_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("story_arc_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("initiative_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["dev.workspace.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["private.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["domain_event_id"], ["dev.domain_events.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["conflict_id"], ["dev.conflicts.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["story_arc_id"], ["dev.roadmap_themes.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["initiative_id"], ["dev.initiative.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["task_id"], ["dev.task.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "workspace_id",
            "identifier",
            name="uq_turning_points_workspace_id_identifier",
        ),
        sa.UniqueConstraint(
            "domain_event_id", name="uq_turning_points_domain_event_id"
        ),
        schema="dev",
    )

    op.create_index(
        "ix_turning_points_workspace_id",
        "turning_points",
        ["workspace_id"],
        schema="dev",
    )
    op.create_index(
        "ix_turning_points_identifier", "turning_points", ["identifier"], schema="dev"
    )
    op.create_index(
        "ix_turning_points_significance",
        "turning_points",
        ["significance"],
        schema="dev",
    )
    op.create_index(
        "ix_turning_points_conflict_id",
        "turning_points",
        ["conflict_id"],
        schema="dev",
    )
    op.create_index(
        "ix_turning_points_created_at",
        "turning_points",
        ["created_at"],
        schema="dev",
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )

    op.execute(
        dedent(
            f"""
            CREATE TRIGGER trg_turning_point_identifier
            BEFORE INSERT ON dev.turning_points
            FOR EACH ROW
            EXECUTE FUNCTION dev.set_turning_point_identifier();

            ALTER TABLE dev.turning_points ENABLE ROW LEVEL SECURITY;

            CREATE POLICY turning_points_policy ON dev.turning_points
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt());

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.turning_points TO {settings.postgrest_authenticated_role};
            """
        )
    )

    # Grant execute permissions on functions
    op.execute(
        dedent(
            f"""
            GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dev TO {settings.postgrest_authenticated_role};
            """
        )
    )


def downgrade() -> None:
    # Drop triggers
    op.execute(
        "DROP TRIGGER IF EXISTS trg_turning_point_identifier ON dev.turning_points"
    )
    op.execute("DROP TRIGGER IF EXISTS trg_conflict_identifier ON dev.conflicts")
    op.execute("DROP TRIGGER IF EXISTS trg_villain_identifier ON dev.villains")
    op.execute("DROP TRIGGER IF EXISTS trg_hero_identifier ON dev.heroes")

    # Drop tables
    op.drop_table("turning_points", schema="dev")
    op.drop_table("conflicts", schema="dev")
    op.drop_table("villains", schema="dev")
    op.drop_table("heroes", schema="dev")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS dev.set_turning_point_identifier()")
    op.execute("DROP FUNCTION IF EXISTS dev.set_conflict_identifier()")
    op.execute("DROP FUNCTION IF EXISTS dev.set_villain_identifier()")
    op.execute("DROP FUNCTION IF EXISTS dev.set_hero_identifier()")

    # Drop counter tables
    op.drop_table("workspace_turning_point_counter", schema="dev")
    op.drop_table("workspace_conflict_counter", schema="dev")
    op.drop_table("workspace_villain_counter", schema="dev")
    op.drop_table("workspace_hero_counter", schema="dev")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS dev.significance")
    op.execute("DROP TYPE IF EXISTS dev.conflict_status")
    op.execute("DROP TYPE IF EXISTS dev.villain_type")
