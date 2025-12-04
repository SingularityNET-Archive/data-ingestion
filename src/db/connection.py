"""Database connection utilities using asyncpg."""

import os
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg


class DatabaseConnection:
    """Manages asyncpg connection pool for PostgreSQL database."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection manager.

        Args:
            database_url: PostgreSQL connection string. If None, reads from DATABASE_URL env var.
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL must be provided either as argument or environment variable"
            )

        # Extract password if provided separately
        db_password = os.getenv("DB_PASSWORD")
        if db_password:
            # Check if password is already in the connection string
            # Format: postgresql://user:password@host or postgresql://user@host
            has_password_in_url = False
            if "@" in self.database_url:
                # Check if there's a colon before the @ (indicating password is present)
                user_part = self.database_url.split("@")[0]
                # Remove protocol prefix to check user:password part
                if "://" in user_part:
                    auth_part = user_part.split("://", 1)[1]
                    # If there's a colon in the auth part, password is already present
                    has_password_in_url = ":" in auth_part
            
            # Insert password into connection string if not present
            if not has_password_in_url and "@" in self.database_url:
                # Format: postgresql://user@host:port/database
                parts = self.database_url.split("@")
                if len(parts) == 2:
                    self.database_url = f"{parts[0]}:{db_password}@{parts[1]}"

        self._pool: Optional[asyncpg.Pool] = None

    async def create_pool(
        self,
        min_size: int = 5,
        max_size: int = 10,
        command_timeout: int = 60,
    ) -> asyncpg.Pool:
        """
        Create connection pool.

        Args:
            min_size: Minimum number of connections in pool
            max_size: Maximum number of connections in pool
            command_timeout: Command timeout in seconds

        Returns:
            Connection pool instance
        """
        if self._pool is None:
            # Disable prepared statements for Supabase transaction pooler (port 6543)
            # Transaction pooler doesn't support PREPARE statements
            is_transaction_pooler = ":6543" in self.database_url or "pooler.supabase.com" in self.database_url
            pool_kwargs = {
                "min_size": min_size,
                "max_size": max_size,
                "command_timeout": command_timeout,
            }
            if is_transaction_pooler:
                # Disable prepared statement cache for pgbouncer transaction mode
                pool_kwargs["statement_cache_size"] = 0
                pool_kwargs["server_settings"] = {
                    "server_prepared_statement_cache_size": "0"
                }
            
            self._pool = await asyncpg.create_pool(
                self.database_url,
                **pool_kwargs,
            )
        return self._pool

    async def close_pool(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from the pool.

        Usage:
            async with db.acquire() as conn:
                await conn.execute("SELECT 1")
        """
        if self._pool is None:
            await self.create_pool()

        async with self._pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args) -> str:
        """
        Execute a query using a connection from the pool.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Query result
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """
        Fetch rows using a connection from the pool.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            List of records
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """
        Fetch a single row using a connection from the pool.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Single record or None
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """
        Fetch a single value using a connection from the pool.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Single value or None
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection(database_url: Optional[str] = None) -> DatabaseConnection:
    """
    Get or create global database connection instance.

    Args:
        database_url: PostgreSQL connection string. If None, reads from DATABASE_URL env var.

    Returns:
        DatabaseConnection instance
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection(database_url)
    return _db_connection

