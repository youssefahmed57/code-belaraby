from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

# Async Engine
engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600
    if "asyncpg" in settings.DATABASE_URL:
        engine_kwargs["connect_args"] = {"prepared_statement_cache_size": 0}

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    **engine_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Sync Engine (for Alembic & Seed data)
sync_engine_kwargs = {}
if settings.SYNC_DATABASE_URL.startswith("sqlite"):
    sync_engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    sync_engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    sync_engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    sync_engine_kwargs["pool_pre_ping"] = True
    sync_engine_kwargs["pool_recycle"] = 3600

sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    **sync_engine_kwargs
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
