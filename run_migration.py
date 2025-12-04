#!/usr/bin/env python3
"""Run database migration using Python (works better with Supabase SSL)."""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.db.migrations import run_migration

async def main():
    """Run the database migration."""
    try:
        await run_migration()
        print("✅ Migration completed successfully!")
        return 0
    except Exception as e:
        print(f"❌ Migration failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

