import os
from typing import Optional

DATABASE_URL = os.environ.get("DATABASE_URL")

# Async connection pool using asyncpg. We provide helpers to initialize
# and close the pool. The pool is lazily created on first use.
_pool = None


def get_database_url() -> Optional[str]:
    """Return configured DATABASE_URL or None if not set."""
    return DATABASE_URL


async def init_db_pool(min_size: int = 1, max_size: int = 5):
    """Initialize and return an asyncpg pool (singleton).

    Raises RuntimeError if `DATABASE_URL` is not configured.
    """
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL not configured")
        import asyncpg

        # Disable statement cache for pgbouncer compatibility
        _pool = await asyncpg.create_pool(
            dsn=DATABASE_URL, 
            min_size=min_size, 
            max_size=max_size,
            statement_cache_size=0  # Required for pgbouncer compatibility
        )
    return _pool


async def get_db_pool():
    """Return an initialized pool, creating it if necessary."""
    global _pool
    if _pool is None:
        return await init_db_pool()
    return _pool


async def close_db_pool():
    """Close and clear the pool if initialized."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
