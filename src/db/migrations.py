"""Database migration utility to execute SQL schema script."""

import os
from pathlib import Path
from typing import Optional

import asyncpg

from src.lib.logger import get_logger

logger = get_logger(__name__)


async def run_migration(
    database_url: Optional[str] = None,
    schema_file: Optional[str] = None,
) -> None:
    """
    Execute SQL schema migration script.

    Args:
        database_url: PostgreSQL connection string. If None, reads from DATABASE_URL env var.
        schema_file: Path to SQL schema file. If None, uses default scripts/setup_db.sql

    Raises:
        FileNotFoundError: If schema file does not exist
        asyncpg.PostgresError: If database operation fails
    """
    if schema_file is None:
        # Default to scripts/setup_db.sql relative to project root
        project_root = Path(__file__).parent.parent.parent
        schema_file = project_root / "scripts" / "setup_db.sql"

    schema_path = Path(schema_file)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Read SQL script
    logger.info(f"Reading schema file: {schema_path}")
    with open(schema_path, encoding="utf-8") as f:
        sql_script = f.read()

    # Get database URL
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL must be provided either as argument or environment variable"
            )

    # Extract password if provided separately
    db_password = os.getenv("DB_PASSWORD")
    if db_password and "password" not in database_url.lower():
        if "@" in database_url:
            parts = database_url.split("@")
            if len(parts) == 2:
                database_url = f"{parts[0]}:{db_password}@{parts[1]}"

    # Connect to database and execute script
    logger.info("Connecting to database...")
    conn = await asyncpg.connect(database_url)

    try:
        logger.info("Executing schema migration...")
        await conn.execute(sql_script)
        logger.info("Schema migration completed successfully")
    except asyncpg.PostgresError as e:
        logger.error(f"Database error during migration: {e}")
        raise
    finally:
        await conn.close()
        logger.info("Database connection closed")


async def verify_schema(database_url: Optional[str] = None) -> bool:
    """
    Verify that all required tables exist in the database.

    Args:
        database_url: PostgreSQL connection string. If None, reads from DATABASE_URL env var.

    Returns:
        True if all tables exist, False otherwise
    """
    required_tables = [
        "workgroups",
        "meetings",
        "agenda_items",
        "action_items",
        "decision_items",
        "discussion_points",
    ]

    if database_url is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL must be provided either as argument or environment variable"
            )

    # Extract password if provided separately
    db_password = os.getenv("DB_PASSWORD")
    if db_password and "password" not in database_url.lower():
        if "@" in database_url:
            parts = database_url.split("@")
            if len(parts) == 2:
                database_url = f"{parts[0]}:{db_password}@{parts[1]}"

    conn = await asyncpg.connect(database_url)

    try:
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = ANY($1::text[])
        """
        result = await conn.fetch(query, required_tables)
        existing_tables = {row["table_name"] for row in result}

        missing_tables = set(required_tables) - existing_tables
        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
            return False

        logger.info("All required tables exist")
        return True
    finally:
        await conn.close()
