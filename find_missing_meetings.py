#!/usr/bin/env python3
"""Script to find meetings that failed to ingest."""

import asyncio
import httpx
import os
from dotenv import load_dotenv
from src.db.connection import get_db_connection
from src.lib.validators import parse_date

load_dotenv()


async def find_missing_meetings():
    """Find meetings from 2024 source that are missing from database."""
    # Download 2024 source data
    url = "https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2024/meeting-summaries-array.json"
    
    print("Downloading 2024 source data...")
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        source_data = response.json()
    
    print(f"Source has {len(source_data)} records")
    
    # Get meetings from database for 2024
    db_url = os.getenv("DATABASE_URL")
    db = get_db_connection(db_url)
    await db.create_pool(min_size=1, max_size=2)
    
    db_meetings = await db.fetch(
        """
        SELECT id, workgroup_id, date, host, purpose
        FROM meetings
        WHERE date >= '2024-01-01' AND date < '2025-01-01'
        ORDER BY date, workgroup_id
        """
    )
    
    print(f"Database has {len(db_meetings)} meetings for 2024")
    
    # Create a set of (workgroup_id, date) tuples from database
    db_keys = set()
    for m in db_meetings:
        db_keys.add((str(m["workgroup_id"]), str(m["date"])))
    
    # Check each source record
    missing = []
    for idx, record in enumerate(source_data):
        try:
            workgroup_id = record.get("workgroup_id")
            meeting_info = record.get("meetingInfo", {})
            date_str = meeting_info.get("date")
            
            if not workgroup_id or not date_str:
                missing.append(
                    {
                        "index": idx,
                        "reason": "Missing workgroup_id or date",
                        "workgroup_id": workgroup_id,
                        "date": date_str,
                    }
                )
                continue
            
            # Parse date
            date_obj = parse_date(date_str)
            if not date_obj:
                missing.append(
                    {
                        "index": idx,
                        "reason": f"Invalid date: {date_str}",
                        "workgroup_id": workgroup_id,
                        "date": date_str,
                    }
                )
                continue
            
            date_str_normalized = str(date_obj.date())
            key = (workgroup_id, date_str_normalized)
            
            if key not in db_keys:
                missing.append(
                    {
                        "index": idx,
                        "workgroup_id": workgroup_id,
                        "date": date_str_normalized,
                        "host": meeting_info.get("host"),
                        "purpose": (
                            meeting_info.get("purpose", "")[:100]
                            if meeting_info.get("purpose")
                            else None
                        ),
                        "workgroup": record.get("workgroup"),
                    }
                )
        except Exception as e:
            missing.append(
                {
                    "index": idx,
                    "reason": f"Error processing: {e}",
                    "record_preview": str(record)[:200],
                }
            )
    
    print(f"\nFound {len(missing)} missing meetings:")
    for m in missing:
        print(f"\n  Index {m['index']}:")
        if "reason" in m:
            print(f"    Reason: {m['reason']}")
            if "workgroup_id" in m:
                print(f"    Workgroup ID: {m['workgroup_id']}")
            if "date" in m:
                print(f"    Date: {m['date']}")
        else:
            print(f"    Workgroup: {m.get('workgroup', 'N/A')}")
            print(f"    Workgroup ID: {m['workgroup_id']}")
            print(f"    Date: {m['date']}")
            print(f"    Host: {m.get('host', 'N/A')}")
            print(f"    Purpose: {m.get('purpose', 'N/A')}")
    
    # Check for duplicates in source
    from collections import defaultdict
    source_keys = defaultdict(int)
    for record in source_data:
        workgroup_id = record.get("workgroup_id")
        date_str = record.get("meetingInfo", {}).get("date")
        if workgroup_id and date_str:
            date_obj = parse_date(date_str)
            if date_obj:
                key = (workgroup_id, str(date_obj.date()))
                source_keys[key] += 1
    
    source_duplicates = {k: v for k, v in source_keys.items() if v > 1}
    if source_duplicates:
        print(f"\n\nDuplicate combinations in SOURCE (same workgroup_id + date): {len(source_duplicates)}")
        for key, count in list(source_duplicates.items())[:10]:
            print(f"  {key}: {count} occurrences in source")
        print(f"\nThis explains why we have fewer meetings in database!")
        print(f"Source has {len(source_data)} records but only {len(source_keys)} unique combinations")
        print(f"Database has {len(db_meetings)} meetings (one per unique combination)")
    
    try:
        await asyncio.wait_for(db.close_pool(), timeout=5.0)
    except:
        pass


if __name__ == "__main__":
    asyncio.run(find_missing_meetings())

