import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, MetaData

from alembic import context

# Ensure the application's modules can be imported by Alembic
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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
from patient_generator.models_db import Base # Import Base from our models file
target_metadata = Base.metadata # Point Alembic to our models' metadata

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
    # Get the DATABASE_URL from environment variable if available
    db_url_from_env = os.environ.get('DATABASE_URL')

    if db_url_from_env:
        # If DATABASE_URL is set, use it directly to create the engine
        # This ensures that when running inside Docker, it uses the service name (e.g., 'db')
        # We need to create a configuration dictionary for create_engine
        # or directly pass the URL. For simplicity, we'll pass the URL.
        # However, engine_from_config expects a dictionary-like section.
        # A cleaner way is to update the config object if env var is present.
        
        # Create a new configuration dictionary for the engine
        # or update the existing one from alembic.ini
        configuration = config.get_section(config.config_ini_section, {})
        configuration['sqlalchemy.url'] = db_url_from_env
        
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    else:
        # Fallback to alembic.ini configuration if DATABASE_URL is not set
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
