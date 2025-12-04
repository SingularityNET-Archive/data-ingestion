import os
from typing import Optional

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_database_url() -> Optional[str]:
    """Return configured DATABASE_URL or None if not set."""
    return DATABASE_URL
