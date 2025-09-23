"""Add postgrest roles and db schema

Revision ID: e1cce05dbbec
Revises: 
Create Date: 2025-01-07 19:50:45.307920

"""
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from src.config import settings

# revision identifiers, used by Alembic.
revision: str = 'e1cce05dbbec'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

POSTGREST__AUTHENTICATOR__ROLE = settings.postgrest_authenticator__role
POSTGREST__AUTHENTICATOR__PASSWORD = settings.postgrest_authenticator__password
POSTGREST__ANONYMOUS__ROLE = settings.postgrest_anonymous__role
POSTGREST__AUTHENTICATED_ROLE = settings.postgrest_authenticated_role


def upgrade() -> None:
    # Create 'dev' & 'private' schema and set it as the default schema for the user
    op.execute(f"CREATE SCHEMA dev AUTHORIZATION {settings.database_app_user_username};")
    op.execute(f"ALTER ROLE {settings.database_app_user_username} SET search_path TO dev, private;")

    # Grant all privileges on database to app user (they already have this as owner)
    op.execute(f"GRANT ALL PRIVILEGES ON DATABASE {settings.database_name} TO {settings.database_app_user_username};")

    # Create roles for PostgREST
    if not os.environ.get("ENVIRONMENT") == "test":
        op.execute(f"CREATE ROLE {POSTGREST__AUTHENTICATOR__ROLE} NOINHERIT NOCREATEDB NOCREATEROLE NOSUPERUSER LOGIN password '{POSTGREST__AUTHENTICATOR__PASSWORD}';")
        op.execute(f"CREATE ROLE {POSTGREST__ANONYMOUS__ROLE} NOLOGIN;")
        op.execute(f"CREATE ROLE {POSTGREST__AUTHENTICATED_ROLE} NOLOGIN;")

    # Grant usage on the dev schema to the postgrest roles
    op.execute(f"GRANT USAGE ON SCHEMA dev TO {POSTGREST__AUTHENTICATOR__ROLE};")
    op.execute(f"GRANT USAGE ON SCHEMA dev TO {POSTGREST__ANONYMOUS__ROLE};")
    op.execute(f"GRANT USAGE ON SCHEMA dev TO {POSTGREST__AUTHENTICATED_ROLE};")

    # Grant usage on the roles to the authenticator role
    op.execute(f"GRANT {POSTGREST__ANONYMOUS__ROLE} TO {POSTGREST__AUTHENTICATOR__ROLE};")
    op.execute(f"GRANT {POSTGREST__AUTHENTICATED_ROLE} TO {POSTGREST__AUTHENTICATOR__ROLE};")
    
    # Grant select on all tables in the dev schema to the postgrest roles
    op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA dev TO {POSTGREST__AUTHENTICATOR__ROLE};")
    op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA dev TO {POSTGREST__ANONYMOUS__ROLE};")
    op.execute(f"GRANT SELECT, UPDATE, DELETE, INSERT ON ALL TABLES IN SCHEMA dev TO {POSTGREST__AUTHENTICATED_ROLE};")

    # Set the search path for the postgrest roles
    op.execute(f"ALTER ROLE {POSTGREST__AUTHENTICATOR__ROLE} SET search_path TO dev;")
    op.execute(f"ALTER ROLE {POSTGREST__ANONYMOUS__ROLE} SET search_path TO dev;")
    op.execute(f"ALTER ROLE {POSTGREST__AUTHENTICATED_ROLE} SET search_path TO dev;")


def downgrade() -> None:
    pass
