from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text, MetaData
from alembic import context
import os
import sys

# Add the project root directory to the Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.core.config import get_settings
from app.models.models import Base

config = context.config
settings = get_settings()

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Create a new MetaData object that excludes the alembic_version table
metadata = MetaData()
for table in Base.metadata.tables.values():
    if table.name != 'alembic_version':
        table.tometadata(metadata)

target_metadata = metadata

def get_url():
    url = settings.SQLALCHEMY_DATABASE_URI
    print(f"Database URL: {url}")
    return url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="public",
        include_schemas=True,
        include_object=lambda obj, name, type_, reflected, compare_to: name != 'alembic_version'
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="public",
            include_schemas=True,
            compare_type=True,
            include_object=lambda obj, name, type_, reflected, compare_to: name != 'alembic_version'
        )

        with context.begin_transaction():
            # Ensure we're in the public schema
            connection.execute(text("SET search_path TO public"))
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

print(f"Database URL: {get_url()}") 