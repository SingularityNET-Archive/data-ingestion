"""Workgroup database model."""

import uuid
from typing import Optional, Dict, Any
import asyncpg
from datetime import datetime


class Workgroup:
    """Workgroup database model."""

    def __init__(
        self,
        id: uuid.UUID,
        name: str,
        raw_json: Dict[str, Any],
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize workgroup model.

        Args:
            id: Workgroup UUID
            name: Workgroup name
            raw_json: Original JSON data
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.name = name
        self.raw_json = raw_json
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    async def upsert(
        cls,
        conn: asyncpg.Connection,
        id: uuid.UUID,
        name: str,
        raw_json: Dict[str, Any],
    ) -> uuid.UUID:
        """
        UPSERT workgroup record with conflict logging.

        Args:
            conn: Database connection
            id: Workgroup UUID
            name: Workgroup name
            raw_json: Original JSON data

        Returns:
            Workgroup UUID
        """
        import json
        from src.lib.logger import get_logger

        logger = get_logger(__name__)

        # Check if record exists (for conflict logging)
        existing = await conn.fetchrow("SELECT id, updated_at FROM workgroups WHERE id = $1", id)
        is_update = existing is not None

        await conn.execute(
            "SELECT upsert_workgroup($1, $2, $3::jsonb)",
            id,
            name,
            json.dumps(raw_json),
        )

        if is_update:
            logger.info(
                f"Updated workgroup {id}",
                extra={
                    "event": "upsert_conflict",
                    "record_id": str(id),
                    "conflict_type": "workgroup_update",
                    "record_type": "workgroup",
                },
            )

        return id

    @classmethod
    async def get_by_id(cls, conn: asyncpg.Connection, id: uuid.UUID) -> Optional["Workgroup"]:
        """
        Get workgroup by ID.

        Args:
            conn: Database connection
            id: Workgroup UUID

        Returns:
            Workgroup instance or None
        """
        row = await conn.fetchrow(
            "SELECT id, name, raw_json, created_at, updated_at FROM workgroups WHERE id = $1",
            id,
        )

        if not row:
            return None

        return cls(
            id=row["id"],
            name=row["name"],
            raw_json=row["raw_json"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
