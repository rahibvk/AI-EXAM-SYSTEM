"""
Alembic Environment Configuration

Purpose:
    This file acts as the bridge between Alembic (migration tool) and the FastAPI application.
    It configures the database connection for migrations and loads the SQLAlchemy models 
    so Alembic knows what the "target" schema looks like.

Key Features:
    - **Offline Mode**: Generates SQL scripts without connecting (rarely used here).
    - **Online Mode**: Connects to the DB and applies changes directly.
    - **Async Support**: Uses `asyncpg` via `run_sync` to execute migrations in an async context.
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# LOAD APPLICATION CONFIG
from app.core.config import settings
from app.models.base import Base # The Base class that models inherit from
# Import all models to ensure they are registered in metadata
from app.models import * 

# Alembic Config Object
config = context.config

# Setup Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata is what Alembic compares the DB against
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine, though an
    Engine is acceptable here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the script output.
    """
    url = settings.SQLALCHEMY_DATABASE_URI
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """
    Callback used by run_migrations_online to execute the actual migration context.
    It runs inside the sync wrapper provided by run_sync().
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine and associate a connection with the context.
    Since we are using AsyncSQLAlchemy, we create an async engine, connect, 
    and then use `.run_sync()` to run the standard synchronous Alembic commands.
    """
    configuration = config.get_section(config.config_ini_section)
    # OVERRIDE alembic.ini url with our Application Settings
    configuration["sqlalchemy.url"] = settings.SQLALCHEMY_DATABASE_URI
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
