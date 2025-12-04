import os
from typing import Optional

# Async connection pool using asyncpg. We provide helpers to initialize
# and close the pool. The pool is lazily created on first use.
_pool = None


def get_database_url() -> Optional[str]:
    """Return configured DATABASE_URL or None if not set.
    
    Reads from environment each time to support dynamic changes in tests.
    """
    return os.environ.get("DATABASE_URL")


def reset_pool():
    """Reset the pool (useful for testing)."""
    global _pool
    _pool = None


async def init_db_pool(min_size: int = 1, max_size: int = 5):
    """Initialize and return an asyncpg pool (singleton).

    Raises RuntimeError if `DATABASE_URL` is not configured.
    """
    global _pool
    if _pool is None:
        database_url = get_database_url()
        if not database_url:
            raise RuntimeError("DATABASE_URL not configured")
        import asyncpg

        # Disable statement cache for pgbouncer compatibility
        _pool = await asyncpg.create_pool(
            dsn=database_url, 
            min_size=min_size, 
            max_size=max_size,
            statement_cache_size=0  # Required for pgbouncer compatibility
        )
    return _pool


async def get_db_pool():
    """Return an initialized pool, creating it if necessary.
    
    Returns None if DATABASE_URL is not configured (instead of raising).
    Also resets the pool if DATABASE_URL was removed after pool creation.
    """
    global _pool
    database_url = get_database_url()
    if not database_url:
        # If DATABASE_URL is not set, reset pool if it exists
        if _pool is not None:
            reset_pool()
        return None
    if _pool is None:
        try:
            return await init_db_pool()
        except Exception:
            # If pool initialization fails, return None
            return None
    return _pool


async def close_db_pool():
    """Close and clear the pool if initialized."""
    global _pool
    if _pool is not None:
        try:
            await _pool.close()
        except Exception:
            # Ignore errors when closing (pool might already be closed)
            pass
        _pool = None
