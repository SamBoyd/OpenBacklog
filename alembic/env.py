import os
from logging.config import fileConfig

import sqlalchemy
from sqlalchemy import engine_from_config, pool

from alembic import context
from src.config import settings
from src.db import Base
from src.github_app.models import *
from src.models import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Check for dynamic database URL override (for parallel test databases)
database_url = os.environ.get("DATABASE_URL", settings.database_url)
config.set_main_option("sqlalchemy.url", database_url)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = [Base.metadata]
target_metadata = [Base.metadata]

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_name(name, type_, parent_names):
    if type_ == "schema":
        # note this will not include the default schema
        return name in ["dev", "private"]
    else:
        return True


for md in target_metadata:
    print("DEBUG Tables in metadata:", md.tables.keys())


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="private",  # This is the schema where the alembic_version table is stored
        include_schemas=True,
        include_name=include_name,
    )

    # Ensure private schema exists for alembic_version table
    connection.execute("CREATE SCHEMA IF NOT EXISTS private;")

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="private",  # This is the schema where the alembic_version table is stored
            include_schemas=True,
            include_name=include_name,
        )

        # Ensure private schema exists for alembic_version table
        connection.execute(
            sqlalchemy.schema.CreateSchema("private", if_not_exists=True)
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
