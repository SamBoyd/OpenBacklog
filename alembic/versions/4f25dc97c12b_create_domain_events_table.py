"""create domain events table

Revision ID: 4f25dc97c12b
Revises: 44fb652b2515
Create Date: 2025-10-19 09:49:22.577005

"""

from textwrap import dedent
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from src.config import settings

# revision identifiers, used by Alembic.
revision: str = "4f25dc97c12b"
down_revision: Union[str, None] = "44fb652b2515"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create domain_events table with indexes for event sourcing."""
    op.create_table(
        "domain_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("private.get_user_id_from_jwt()"),
        ),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="dev",
    )

    op.create_index(
        "ix_domain_events_aggregate_id", "domain_events", ["aggregate_id"], schema="dev"
    )
    op.create_index(
        "ix_domain_events_event_type", "domain_events", ["event_type"], schema="dev"
    )
    op.create_index(
        "ix_domain_events_occurred_at",
        "domain_events",
        ["occurred_at"],
        schema="dev",
        postgresql_using="btree",
        postgresql_ops={"occurred_at": "DESC"},
    )

    op.execute(
        dedent(
            f"""
            ALTER TABLE dev.domain_events ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY domain_events_policy ON dev.domain_events
                USING (user_id = private.get_user_id_from_jwt())
                WITH CHECK (user_id = private.get_user_id_from_jwt()); 

            GRANT SELECT, UPDATE, DELETE, INSERT ON TABLE dev.domain_events TO {settings.postgrest_authenticated_role};
            """
        )
    )


def downgrade() -> None:
    """Drop domain_events table and all indexes."""
    op.drop_index(
        "ix_domain_events_occurred_at", table_name="domain_events", schema="dev"
    )
    op.drop_index(
        "ix_domain_events_event_type", table_name="domain_events", schema="dev"
    )
    op.drop_index(
        "ix_domain_events_aggregate_id", table_name="domain_events", schema="dev"
    )
    op.drop_table("domain_events", schema="dev")
