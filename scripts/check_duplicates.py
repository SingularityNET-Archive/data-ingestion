#!/usr/bin/env python3
"""Script to identify and optionally clean up duplicate meeting records."""

import asyncio
import os
from dotenv import load_dotenv
from src.db.connection import get_db_connection

load_dotenv()


async def find_duplicates():
    """Find duplicate meetings by workgroup_id + date."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        return

    db = get_db_connection(db_url)
    await db.create_pool()

    try:
        # Find meetings with same workgroup_id and date
        duplicates = await db.fetch(
            """
            SELECT 
                workgroup_id, 
                date, 
                COUNT(*) as count,
                array_agg(id ORDER BY updated_at DESC) as meeting_ids,
                array_agg(updated_at ORDER BY updated_at DESC) as update_times
            FROM meetings 
            GROUP BY workgroup_id, date 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            """
        )

        print(f"\nFound {len(duplicates)} duplicate groups (same workgroup_id + date)")
        print(f"Total duplicate meetings: {sum(d['count'] - 1 for d in duplicates)}")
        print("\nTop 10 duplicate groups:")
        for i, d in enumerate(duplicates[:10], 1):
            print(
                f"\n{i}. Workgroup {d['workgroup_id']}, Date {d['date']}: {d['count']} meetings"
            )
            print(f"   Meeting IDs: {d['meeting_ids'][:3]}...")
            print(f"   Most recent: {d['update_times'][0]}")

        # Get total stats
        total_meetings = await db.fetchval("SELECT COUNT(*) FROM meetings")
        unique_combos = await db.fetchval(
            "SELECT COUNT(DISTINCT (workgroup_id, date)) FROM meetings"
        )

        print(f"\n--- Summary ---")
        print(f"Total meetings: {total_meetings}")
        print(f"Unique workgroup_id + date combinations: {unique_combos}")
        print(f"Potential duplicates: {total_meetings - unique_combos}")

        return duplicates

    finally:
        try:
            await asyncio.wait_for(db.close_pool(), timeout=5.0)
        except:
            pass


async def cleanup_duplicates(keep_latest=True):
    """
    Clean up duplicate meetings, keeping only the most recent one.
    
    Args:
        keep_latest: If True, keep the most recently updated record. 
                     If False, keep the oldest record.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        return

    db = get_db_connection(db_url)
    await db.create_pool()

    try:
        # Find duplicates and delete all but one (keeping the most recent)
        result = await db.execute(
            """
            DELETE FROM meetings
            WHERE id IN (
                SELECT id
                FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY workgroup_id, date 
                               ORDER BY updated_at DESC
                           ) as rn
                    FROM meetings
                ) ranked
                WHERE rn > 1
            )
            """
        )

        print(f"\nCleaned up duplicate meetings")
        print(f"Deleted records: {result}")

    finally:
        try:
            await asyncio.wait_for(db.close_pool(), timeout=5.0)
        except:
            pass


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        print("WARNING: This will delete duplicate meetings!")
        response = input("Are you sure? (yes/no): ")
        if response.lower() == "yes":
            asyncio.run(cleanup_duplicates())
        else:
            print("Cancelled.")
    else:
        asyncio.run(find_duplicates())
        print("\nTo clean up duplicates, run: python check_duplicates.py --cleanup")



