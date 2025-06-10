from logging.config import fileConfig
import os
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure the application's modules can be imported by Alembic
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# Import your models' MetaData object here.
from patient_generator.models_db import Base  # Import Base from our models file

target_metadata = Base.metadata  # Point Alembic to our models' metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


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
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get the database URL from the environment variable first
    db_url = os.getenv("DATABASE_URL")

    # If DATABASE_URL is not set, fall back to alembic.ini configuration
    if db_url is None:
        ini_section = config.get_section(config.config_ini_section, {})
        # Ensure 'sqlalchemy.url' is present in the ini_section or handle its absence
        if "sqlalchemy.url" not in ini_section:
            raise ValueError(
                "sqlalchemy.url not found in alembic.ini and DATABASE_URL environment variable is not set."
            )
        connectable = engine_from_config(
            ini_section,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    else:
        # If DATABASE_URL is set, create engine configuration directly
        # This assumes DATABASE_URL is a complete SQLAlchemy URL
        from sqlalchemy import create_engine

        connectable = create_engine(db_url)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
