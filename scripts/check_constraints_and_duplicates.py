#!/usr/bin/env python3
"""
Check database constraints and find duplicate records.

This script verifies that all tables have proper PRIMARY KEY constraints
and identifies any duplicate records that shouldn't exist.
"""

import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Load environment variables from .env file
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Try loading from current directory
    load_dotenv()

# Add src to path
sys.path.insert(0, str(project_root))

from src.lib.logger import get_logger

logger = get_logger(__name__)


async def check_constraints(conn: asyncpg.Connection) -> dict:
    """
    Check that all tables have PRIMARY KEY constraints on id column.
    
    Returns:
        Dictionary with constraint check results
    """
    tables = [
        "workgroups",
        "meetings",
        "agenda_items",
        "action_items",
        "decision_items",
        "discussion_points",
    ]
    
    results = {}
    
    for table in tables:
        query = """
            SELECT 
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = 'public'
                AND tc.table_name = $1
                AND tc.constraint_type = 'PRIMARY KEY'
                AND kcu.column_name = 'id'
        """
        
        constraint = await conn.fetchrow(query, table)
        
        if constraint:
            results[table] = {
                "has_primary_key": True,
                "constraint_name": constraint["constraint_name"],
            }
            logger.info(f"✓ {table}: PRIMARY KEY constraint exists on 'id'")
        else:
            results[table] = {
                "has_primary_key": False,
                "constraint_name": None,
            }
            logger.error(f"✗ {table}: MISSING PRIMARY KEY constraint on 'id'")
    
    return results


async def find_duplicate_uuids(conn: asyncpg.Connection) -> dict:
    """
    Find duplicate UUIDs in each table (should never happen with PRIMARY KEY).
    
    Returns:
        Dictionary with duplicate counts per table
    """
    tables = [
        "workgroups",
        "meetings",
        "agenda_items",
        "action_items",
        "decision_items",
        "discussion_points",
    ]
    
    results = {}
    
    for table in tables:
        query = f"""
            SELECT 
                id,
                COUNT(*) as duplicate_count,
                array_agg(created_at ORDER BY created_at) as creation_times
            FROM {table}
            GROUP BY id
            HAVING COUNT(*) > 1
        """
        
        duplicates = await conn.fetch(query)
        
        if duplicates:
            results[table] = {
                "has_duplicates": True,
                "duplicate_count": len(duplicates),
                "details": [
                    {
                        "id": str(row["id"]),
                        "count": row["duplicate_count"],
                        "creation_times": row["creation_times"],
                    }
                    for row in duplicates
                ],
            }
            logger.error(
                f"✗ {table}: Found {len(duplicates)} duplicate UUID(s)"
            )
            for dup in duplicates:
                logger.error(
                    f"  - UUID {dup['id']}: {dup['duplicate_count']} copies "
                    f"(created at: {dup['creation_times']})"
                )
        else:
            results[table] = {
                "has_duplicates": False,
                "duplicate_count": 0,
            }
            logger.info(f"✓ {table}: No duplicate UUIDs found")
    
    return results


async def find_content_duplicates(conn: asyncpg.Connection) -> dict:
    """
    Find records with same content that should have same deterministic UUID.
    
    Returns:
        Dictionary with content-based duplicate analysis
    """
    results = {}
    
    # Check meetings with same workgroup_id + date + host + purpose
    query = """
        SELECT 
            workgroup_id,
            date,
            host,
            purpose,
            COUNT(DISTINCT id) as unique_ids,
            array_agg(DISTINCT id) as meeting_ids,
            array_agg(created_at ORDER BY created_at) as creation_times
        FROM meetings
        GROUP BY workgroup_id, date, host, purpose
        HAVING COUNT(DISTINCT id) > 1
        ORDER BY COUNT(DISTINCT id) DESC
    """
    
    meeting_duplicates = await conn.fetch(query)
    if meeting_duplicates:
        results["meetings"] = {
            "has_content_duplicates": True,
            "count": len(meeting_duplicates),
            "details": [
                {
                    "workgroup_id": str(row["workgroup_id"]),
                    "date": str(row["date"]),
                    "host": row["host"],
                    "purpose": row["purpose"],
                    "unique_ids": len(row["meeting_ids"]),
                    "meeting_ids": [str(id) for id in row["meeting_ids"]],
                    "creation_times": row["creation_times"],
                }
                for row in meeting_duplicates
            ],
        }
        logger.warning(
            f"⚠ meetings: Found {len(meeting_duplicates)} groups with same content but different UUIDs"
        )
    else:
        results["meetings"] = {
            "has_content_duplicates": False,
            "count": 0,
        }
        logger.info("✓ meetings: No content-based duplicates found")
    
    # Check agenda items with same meeting_id + order_index
    query = """
        SELECT 
            meeting_id,
            order_index,
            COUNT(DISTINCT id) as unique_ids,
            array_agg(DISTINCT id) as agenda_item_ids,
            array_agg(created_at ORDER BY created_at) as creation_times
        FROM agenda_items
        GROUP BY meeting_id, order_index
        HAVING COUNT(DISTINCT id) > 1
        ORDER BY COUNT(DISTINCT id) DESC
    """
    
    agenda_duplicates = await conn.fetch(query)
    if agenda_duplicates:
        results["agenda_items"] = {
            "has_content_duplicates": True,
            "count": len(agenda_duplicates),
            "details": [
                {
                    "meeting_id": str(row["meeting_id"]),
                    "order_index": row["order_index"],
                    "unique_ids": len(row["agenda_item_ids"]),
                    "agenda_item_ids": [str(id) for id in row["agenda_item_ids"]],
                    "creation_times": row["creation_times"],
                }
                for row in agenda_duplicates
            ],
        }
        logger.warning(
            f"⚠ agenda_items: Found {len(agenda_duplicates)} groups with same content but different UUIDs"
        )
    else:
        results["agenda_items"] = {
            "has_content_duplicates": False,
            "count": 0,
        }
        logger.info("✓ agenda_items: No content-based duplicates found")
    
    return results


async def get_table_statistics(conn: asyncpg.Connection) -> dict:
    """Get basic statistics for all tables."""
    tables = [
        "workgroups",
        "meetings",
        "agenda_items",
        "action_items",
        "decision_items",
        "discussion_points",
    ]
    
    stats = {}
    
    for table in tables:
        total_query = f"SELECT COUNT(*) as total FROM {table}"
        unique_query = f"SELECT COUNT(DISTINCT id) as unique_ids FROM {table}"
        
        total = await conn.fetchval(total_query)
        unique = await conn.fetchval(unique_query)
        
        stats[table] = {
            "total_rows": total,
            "unique_ids": unique,
            "difference": total - unique,
        }
        
        if total != unique:
            logger.error(
                f"✗ {table}: {total} total rows but only {unique} unique IDs "
                f"(difference: {total - unique})"
            )
        else:
            logger.info(f"✓ {table}: {total} rows, {unique} unique IDs")
    
    return stats


async def main():
    """Main function to run all checks."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is not set")
        logger.error("")
        logger.error("Please set DATABASE_URL in one of the following ways:")
        logger.error("  1. Create a .env file in the project root with:")
        logger.error("     DATABASE_URL=postgresql://user:password@host:port/database")
        logger.error("")
        logger.error("  2. Export it in your shell:")
        logger.error("     export DATABASE_URL='postgresql://user:password@host:port/database'")
        logger.error("")
        logger.error("  3. Pass it as an environment variable when running:")
        logger.error("     DATABASE_URL='...' python scripts/check_constraints_and_duplicates.py")
        logger.error("")
        env_file = project_root / ".env"
        if not env_file.exists():
            logger.info(f"Note: No .env file found at {env_file}")
        sys.exit(1)
    
    # Extract password if provided separately
    db_password = os.getenv("DB_PASSWORD")
    if db_password and ":" in database_url and "@" in database_url:
        url_parts = database_url.split("@")
        if len(url_parts) == 2:
            user_pass_part = url_parts[0].split("://")[-1] if "://" in url_parts[0] else url_parts[0]
            if ":" not in user_pass_part:
                database_url = f"{url_parts[0]}:{db_password}@{url_parts[1]}"
    
    # Disable prepared statements for Supabase transaction pooler
    is_transaction_pooler = ":6543" in database_url or "pooler.supabase.com" in database_url
    connect_kwargs = {}
    if is_transaction_pooler:
        connect_kwargs["statement_cache_size"] = 0
        connect_kwargs["server_settings"] = {
            "server_prepared_statement_cache_size": "0"
        }
    
    logger.info("Connecting to database...")
    conn = await asyncpg.connect(database_url, **connect_kwargs)
    
    try:
        logger.info("=" * 80)
        logger.info("DATABASE CONSTRAINT AND DUPLICATE CHECK")
        logger.info("=" * 80)
        
        # Check constraints
        logger.info("\n1. Checking PRIMARY KEY constraints...")
        logger.info("-" * 80)
        constraint_results = await check_constraints(conn)
        
        # Check for duplicate UUIDs
        logger.info("\n2. Checking for duplicate UUIDs...")
        logger.info("-" * 80)
        uuid_duplicates = await find_duplicate_uuids(conn)
        
        # Check for content-based duplicates
        logger.info("\n3. Checking for content-based duplicates...")
        logger.info("-" * 80)
        content_duplicates = await find_content_duplicates(conn)
        
        # Get statistics
        logger.info("\n4. Table statistics...")
        logger.info("-" * 80)
        stats = await get_table_statistics(conn)
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        
        has_issues = False
        
        # Check constraint issues
        missing_constraints = [
            table for table, result in constraint_results.items()
            if not result["has_primary_key"]
        ]
        if missing_constraints:
            logger.error(f"✗ Missing PRIMARY KEY constraints: {', '.join(missing_constraints)}")
            has_issues = True
        
        # Check UUID duplicates
        uuid_duplicate_tables = [
            table for table, result in uuid_duplicates.items()
            if result["has_duplicates"]
        ]
        if uuid_duplicate_tables:
            logger.error(f"✗ Tables with duplicate UUIDs: {', '.join(uuid_duplicate_tables)}")
            has_issues = True
        
        # Check content duplicates
        content_duplicate_tables = [
            table for table, result in content_duplicates.items()
            if result.get("has_content_duplicates", False)
        ]
        if content_duplicate_tables:
            logger.warning(f"⚠ Tables with content-based duplicates: {', '.join(content_duplicate_tables)}")
            has_issues = True
        
        # Check statistics
        stat_issues = [
            table for table, stat in stats.items()
            if stat["difference"] > 0
        ]
        if stat_issues:
            logger.error(f"✗ Tables with row count mismatches: {', '.join(stat_issues)}")
            has_issues = True
        
        if not has_issues:
            logger.info("✓ All checks passed! No issues found.")
            return 0
        else:
            logger.error("✗ Issues found! See details above.")
            return 1
    
    finally:
        await conn.close()


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

