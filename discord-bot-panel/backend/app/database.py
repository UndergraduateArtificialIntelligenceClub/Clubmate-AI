"""
Database Connection Management
==============================
Async SQLAlchemy engine and session management.
Supports both SQLite (dev) and PostgreSQL (production).

Architecture Notes:
- Uses aiosqlite for SQLite async support
- Uses asyncpg for PostgreSQL async support
- Connection pooling configured for production workloads
- Dependency injection pattern for clean session management
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.config import get_settings

settings = get_settings()


# ============================================================
# ENGINE CONFIGURATION
# ============================================================
# Determine if using SQLite or PostgreSQL based on URL
is_sqlite = settings.database_url.startswith("sqlite")

if is_sqlite:
    # SQLite configuration
    # - StaticPool for single connection (SQLite limitation)
    # - check_same_thread=False required for async
    # - Create data directory if needed
    db_path = Path(settings.database_url.replace("sqlite+aiosqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL configuration
    # - Connection pooling for production
    # - pool_pre_ping for connection health checks
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
    )


# ============================================================
# SESSION FACTORY
# ============================================================
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================
# DEPENDENCY INJECTION
# ============================================================
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.
    
    Usage in routes:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            ...
    
    The session is automatically closed after the request completes,
    and any uncommitted changes are rolled back.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================
# INITIALIZATION AND CLEANUP
# ============================================================
async def init_db() -> None:
    """
    Initialize database tables.
    
    In production, use Alembic migrations instead.
    This is provided for development convenience.
    """
    async with engine.begin() as conn:
        # Import all models to register them with SQLModel
        from app.models import (
            User,
            Contact,
            File,
            APIKey,
            ActivityLog,
            OAuthToken,
        )
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections gracefully.
    
    Called during application shutdown to ensure
    all connections are properly released.
    """
    await engine.dispose()


@asynccontextmanager
async def get_session_context():
    """
    Context manager for database sessions outside of request context.
    
    Useful for background tasks, scripts, and testing.
    
    Usage:
        async with get_session_context() as session:
            result = await session.execute(query)
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
