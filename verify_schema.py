#!/usr/bin/env python3
"""Verify database schema was created successfully."""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.db.migrations import verify_schema

async def main():
    """Verify the database schema."""
    try:
        print("🔍 Verifying database schema...")
        is_valid = await verify_schema()
        if is_valid:
            print("✅ All required tables exist!")
            return 0
        else:
            print("❌ Some tables are missing. Please check the schema.")
            return 1
    except Exception as e:
        print(f"❌ Verification failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)




