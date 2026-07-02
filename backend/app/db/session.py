"""
Async database session management.

Provides the SQLAlchemy async engine, session factory, a FastAPI-compatible
dependency that yields sessions, and an init_db helper for table creation.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.base import Base

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
)

async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency that provides a scoped async database session."""
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    """Create all tables defined on Base.metadata (development convenience)."""
    # Import all models so metadata is fully registered before create_all
    import app.models  # noqa: F401

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
