"""Discussion point database model."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import asyncpg


class DiscussionPoint:
    """Discussion point database model."""

    def __init__(
        self,
        id: uuid.UUID,
        agenda_item_id: uuid.UUID,
        point_text: str,
        raw_json: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize discussion point model.

        Args:
            id: Discussion point UUID
            agenda_item_id: Parent agenda item UUID
            point_text: Discussion point text
            raw_json: Original JSON data
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.agenda_item_id = agenda_item_id
        self.point_text = point_text
        self.raw_json = raw_json or {}
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    async def upsert(
        cls,
        conn: asyncpg.Connection,
        id: uuid.UUID,
        agenda_item_id: uuid.UUID,
        point_text: str,
        raw_json: Dict[str, Any],
    ) -> uuid.UUID:
        """
        UPSERT discussion point record.

        Args:
            conn: Database connection
            id: Discussion point UUID
            agenda_item_id: Parent agenda item UUID
            point_text: Discussion point text
            raw_json: Original JSON data

        Returns:
            Discussion point UUID
        """
        await conn.execute(
            "SELECT upsert_discussion_point($1, $2, $3, $4::jsonb)",
            id,
            agenda_item_id,
            point_text,
            json.dumps(raw_json),
        )
        return id


