"""Decision item database model."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import asyncpg


class DecisionItem:
    """Decision item database model."""

    def __init__(
        self,
        id: uuid.UUID,
        agenda_item_id: uuid.UUID,
        decision_text: str,
        rationale: Optional[str] = None,
        effect_scope: Optional[str] = None,
        raw_json: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize decision item model.

        Args:
            id: Decision item UUID
            agenda_item_id: Parent agenda item UUID
            decision_text: Decision text
            rationale: Rationale for decision
            effect_scope: Scope/impact of decision
            raw_json: Original JSON data
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.agenda_item_id = agenda_item_id
        self.decision_text = decision_text
        self.rationale = rationale
        self.effect_scope = effect_scope
        self.raw_json = raw_json or {}
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    async def upsert(
        cls,
        conn: asyncpg.Connection,
        id: uuid.UUID,
        agenda_item_id: uuid.UUID,
        decision_text: str,
        rationale: Optional[str],
        effect_scope: Optional[str],
        raw_json: Dict[str, Any],
    ) -> uuid.UUID:
        """
        UPSERT decision item record.

        Args:
            conn: Database connection
            id: Decision item UUID
            agenda_item_id: Parent agenda item UUID
            decision_text: Decision text
            rationale: Rationale for decision
            effect_scope: Scope/impact of decision
            raw_json: Original JSON data

        Returns:
            Decision item UUID
        """
        await conn.execute(
            "SELECT upsert_decision_item($1, $2, $3, $4, $5, $6::jsonb)",
            id,
            agenda_item_id,
            decision_text,
            rationale,
            effect_scope,
            json.dumps(raw_json),
        )
        return id

