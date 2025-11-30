"""Agenda item database model."""

import uuid
from typing import Optional, Dict, Any
import asyncpg
from datetime import datetime
import json


class AgendaItem:
    """Agenda item database model."""

    def __init__(
        self,
        id: uuid.UUID,
        meeting_id: uuid.UUID,
        status: Optional[str] = None,
        order_index: Optional[int] = None,
        raw_json: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize agenda item model.

        Args:
            id: Agenda item UUID
            meeting_id: Parent meeting UUID
            status: Agenda item status
            order_index: Order/position in agenda
            raw_json: Original JSON data
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.meeting_id = meeting_id
        self.status = status
        self.order_index = order_index
        self.raw_json = raw_json or {}
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    async def upsert(
        cls,
        conn: asyncpg.Connection,
        id: uuid.UUID,
        meeting_id: uuid.UUID,
        status: Optional[str],
        order_index: Optional[int],
        raw_json: Dict[str, Any],
    ) -> uuid.UUID:
        """
        UPSERT agenda item record.

        Args:
            conn: Database connection
            id: Agenda item UUID
            meeting_id: Parent meeting UUID
            status: Agenda item status
            order_index: Order/position in agenda
            raw_json: Original JSON data

        Returns:
            Agenda item UUID
        """
        await conn.execute(
            "SELECT upsert_agenda_item($1, $2, $3, $4, $5::jsonb)",
            id,
            meeting_id,
            status,
            order_index,
            json.dumps(raw_json),
        )
        return id
