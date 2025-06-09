"""PostgreSQL database configuration and connection management."""

from __future__ import annotations

import logging
import os
from typing import AsyncGenerator, Optional

import asyncpg
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger("miles.database")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class DatabaseManager:
    """Manages PostgreSQL database connections and sessions."""

    def __init__(self) -> None:
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._url: Optional[str] = None

    def get_database_url(self) -> str:
        """Get database URL from environment variables."""
        # Support multiple environment variable names
        database_url = (
            os.getenv("DATABASE_URL")
            or os.getenv("POSTGRES_URL")
            or os.getenv("POSTGRESQL_URL")
        )

        if not database_url:
            # Fallback to local development database
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            user = os.getenv("POSTGRES_USER", "postgres")
            password = os.getenv("POSTGRES_PASSWORD", "postgres")
            database = os.getenv("POSTGRES_DB", "miles")

            database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        # Convert postgres:// to postgresql:// for SQLAlchemy
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        # Ensure async driver
        if not database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        return database_url

    async def initialize(self) -> None:
        """Initialize database connection and create engine."""
        try:
            self._url = self.get_database_url()
            logger.info("Initializing database connection...")

            # Create async engine
            self.engine = create_async_engine(
                self._url,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true",
                pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
                pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
                pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            )

            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # Test connection
            await self.test_connection()
            logger.info("✅ Database connection established successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            # Don't raise - allow fallback to file storage
            self.engine = None
            self.session_factory = None

    async def test_connection(self) -> bool:
        """Test database connection."""
        if not self.engine:
            return False

        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")

        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")

    @property
    def is_available(self) -> bool:
        """Check if database is available."""
        return self.engine is not None and self.session_factory is not None


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function to get database session."""
    async for session in db_manager.get_session():
        yield session


async def init_database() -> None:
    """Initialize database on startup."""
    await db_manager.initialize()


async def close_database() -> None:
    """Close database on shutdown."""
    await db_manager.close()


# Direct connection utilities for migrations and setup
async def get_raw_connection() -> asyncpg.Connection:
    """Get raw asyncpg connection for migrations."""
    url = db_manager.get_database_url()
    # Convert back to asyncpg format
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.connect(url)


async def create_database_if_not_exists() -> None:
    """Create database if it doesn't exist (for development)."""
    try:
        url = db_manager.get_database_url()
        # Extract database name
        db_name = url.split("/")[-1].split("?")[0]

        # Connect to postgres database to create our database
        admin_url = url.rsplit("/", 1)[0] + "/postgres"
        admin_url = admin_url.replace("postgresql+asyncpg://", "postgresql://")

        conn = await asyncpg.connect(admin_url)
        try:
            # Check if database exists
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", db_name
            )
            if not exists:
                await conn.execute(f'CREATE DATABASE "{db_name}"')
                logger.info(f"✅ Created database: {db_name}")
            else:
                logger.info(f"Database {db_name} already exists")
        finally:
            await conn.close()

    except Exception as e:
        logger.warning(f"Could not create database: {e}")


# Import text for raw SQL queries
from sqlalchemy import text  # noqa: E402

__all__ = [
    "Base",
    "DatabaseManager",
    "db_manager",
    "get_db_session",
    "init_database",
    "close_database",
    "get_raw_connection",
    "create_database_if_not_exists",
]
