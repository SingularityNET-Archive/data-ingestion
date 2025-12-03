"""Meeting database model."""

import json
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import asyncpg


class Meeting:
    """Meeting database model."""

    def __init__(
        self,
        id: uuid.UUID,
        workgroup_id: uuid.UUID,
        date: date,
        type: Optional[str] = None,
        host: Optional[str] = None,
        documenter: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        purpose: Optional[str] = None,
        video_links: Optional[List[str]] = None,
        working_docs: Optional[Dict[str, Any]] = None,
        timestamped_video: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, Any]] = None,
        raw_json: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize meeting model.

        Args:
            id: Meeting UUID
            workgroup_id: Parent workgroup UUID
            date: Meeting date
            type: Meeting type
            host: Meeting host
            documenter: Person who documented the meeting
            attendees: List of attendee names
            purpose: Meeting purpose
            video_links: List of video URLs
            working_docs: Working documents (JSONB)
            timestamped_video: Timestamped video segments (JSONB)
            tags: Tags metadata (JSONB)
            raw_json: Original JSON data
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.workgroup_id = workgroup_id
        self.date = date
        self.type = type
        self.host = host
        self.documenter = documenter
        self.attendees = attendees or []
        self.purpose = purpose
        self.video_links = video_links or []
        self.working_docs = working_docs
        self.timestamped_video = timestamped_video
        self.tags = tags
        self.raw_json = raw_json or {}
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    async def upsert(
        cls,
        conn: asyncpg.Connection,
        id: uuid.UUID,
        workgroup_id: uuid.UUID,
        date: date,
        type: Optional[str],
        host: Optional[str],
        documenter: Optional[str],
        attendees: Optional[List[str]],
        purpose: Optional[str],
        video_links: Optional[List[str]],
        working_docs: Optional[Dict[str, Any]],
        timestamped_video: Optional[Dict[str, Any]],
        tags: Optional[Dict[str, Any]],
        raw_json: Dict[str, Any],
    ) -> uuid.UUID:
        """
        UPSERT meeting record.

        Args:
            conn: Database connection
            id: Meeting UUID
            workgroup_id: Parent workgroup UUID
            date: Meeting date
            type: Meeting type
            host: Meeting host
            documenter: Person who documented the meeting
            attendees: List of attendee names
            purpose: Meeting purpose
            video_links: List of video URLs
            working_docs: Working documents (JSONB)
            timestamped_video: Timestamped video segments (JSONB)
            tags: Tags metadata (JSONB)
            raw_json: Original JSON data

        Returns:
            Meeting UUID
        """
        await conn.execute(
            "SELECT upsert_meeting($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb)",
            id,
            workgroup_id,
            date,
            type,
            host,
            documenter,
            attendees or [],
            purpose,
            video_links or [],
            json.dumps(working_docs) if working_docs else None,
            json.dumps(timestamped_video) if timestamped_video else None,
            json.dumps(tags) if tags else None,
            json.dumps(raw_json),
        )
        return id
