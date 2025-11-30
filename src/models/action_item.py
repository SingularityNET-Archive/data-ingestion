"""Action item database model."""

import uuid
from typing import Optional, Dict, Any
import asyncpg
from datetime import datetime, date
import json


class ActionItem:
    """Action item database model."""

    def __init__(
        self,
        id: uuid.UUID,
        agenda_item_id: uuid.UUID,
        text: str,
        assignee: Optional[str] = None,
        due_date: Optional[date] = None,
        status: Optional[str] = None,
        raw_json: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize action item model.

        Args:
            id: Action item UUID
            agenda_item_id: Parent agenda item UUID
            text: Action item text
            assignee: Person assigned to action
            due_date: Due date
            status: Action item status
            raw_json: Original JSON data
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.agenda_item_id = agenda_item_id
        self.text = text
        self.assignee = assignee
        self.due_date = due_date
        self.status = status
        self.raw_json = raw_json or {}
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    async def upsert(
        cls,
        conn: asyncpg.Connection,
        id: uuid.UUID,
        agenda_item_id: uuid.UUID,
        text: str,
        assignee: Optional[str],
        due_date: Optional[date],
        status: Optional[str],
        raw_json: Dict[str, Any],
    ) -> uuid.UUID:
        """
        UPSERT action item record.

        Args:
            conn: Database connection
            id: Action item UUID
            agenda_item_id: Parent agenda item UUID
            text: Action item text
            assignee: Person assigned to action
            due_date: Due date
            status: Action item status
            raw_json: Original JSON data

        Returns:
            Action item UUID
        """
        await conn.execute(
            "SELECT upsert_action_item($1, $2, $3, $4, $5, $6, $7::jsonb)",
            id,
            agenda_item_id,
            text,
            assignee,
            due_date,
            status,
            json.dumps(raw_json),
        )
        return id
