"""Database connection and migration management."""

import asyncpg
import logging
import os
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections and migrations."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager.

        Args:
            database_url: PostgreSQL connection URL. If None, uses DATABASE_URL env var.
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.pool: Optional[asyncpg.Pool] = None

        if not self.database_url:
            raise ValueError("DATABASE_URL not configured")

        # Convert postgres:// to postgresql:// for asyncpg compatibility
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)

        logger.info("Database manager initialized")

    async def connect(self, min_size: int = 10, max_size: int = 20):
        """Create connection pool.

        Args:
            min_size: Minimum number of connections in pool
            max_size: Maximum number of connections in pool
        """
        if self.pool:
            logger.warning("Connection pool already exists")
            return

        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=min_size,
                max_size=max_size,
                command_timeout=60
            )
            logger.info(f"Database connection pool created (min={min_size}, max={max_size})")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool.

        Usage:
            async with db.acquire() as conn:
                result = await conn.fetch("SELECT * FROM table")
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")

        async with self.pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args):
        """Execute a query without returning results.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Status message from database
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Fetch all rows from a query.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            List of Record objects
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch a single row from a query.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Record object or None
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Fetch a single value from a query.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single value or None
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def run_migration(self, migration_file: Path):
        """Run a SQL migration file.

        Args:
            migration_file: Path to .sql migration file
        """
        logger.info(f"Running migration: {migration_file.name}")

        with open(migration_file, 'r') as f:
            sql = f.read()

        async with self.acquire() as conn:
            await conn.execute(sql)

        logger.info(f"Migration completed: {migration_file.name}")

    async def initialize_schema(self):
        """Initialize database schema from migration files."""
        migrations_dir = Path(__file__).parent.parent.parent / "migrations"

        if not migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {migrations_dir}")
            return

        # Get all .sql files sorted by name
        migration_files = sorted(migrations_dir.glob("*.sql"))

        if not migration_files:
            logger.warning("No migration files found")
            return

        logger.info(f"Found {len(migration_files)} migration(s)")

        for migration_file in migration_files:
            try:
                await self.run_migration(migration_file)
            except Exception as e:
                logger.error(f"Migration failed: {migration_file.name} - {e}")
                raise

        logger.info("All migrations completed successfully")

    async def check_connection(self) -> bool:
        """Check if database connection is working.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            async with self.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False


# Global database instance
db: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Get global database instance.

    Returns:
        DatabaseManager instance

    Raises:
        RuntimeError: If database not initialized
    """
    if db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db


async def init_db(database_url: Optional[str] = None, run_migrations: bool = True):
    """Initialize global database instance.

    Args:
        database_url: PostgreSQL connection URL
        run_migrations: Whether to run migrations on startup
    """
    global db

    if db is not None:
        logger.warning("Database already initialized")
        return db

    db = DatabaseManager(database_url)
    await db.connect()

    # Run migrations if requested
    if run_migrations:
        await db.initialize_schema()

    logger.info("Database initialized successfully")
    return db


async def close_db():
    """Close global database instance."""
    global db

    if db:
        await db.disconnect()
        db = None
        logger.info("Database closed")
