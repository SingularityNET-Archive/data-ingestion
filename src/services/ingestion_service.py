"""Ingestion service for processing meeting summaries into database."""

import uuid
from typing import Any, Dict, List, Optional

import asyncpg

from src.lib.logger import get_logger
from src.lib.validators import detect_circular_reference, parse_date
from src.models.action_item import ActionItem
from src.models.agenda_item import AgendaItem
from src.models.decision_item import DecisionItem
from src.models.discussion_point import DiscussionPoint
from src.models.meeting import Meeting
from src.models.meeting_summary import MeetingSummary
from src.services.schema_manager import SchemaManager

logger = get_logger(__name__)


class IngestionService:
    """Service for ingesting meeting summaries into database."""

    def __init__(self, db_connection):
        """
        Initialize ingestion service.

        Args:
            db_connection: DatabaseConnection instance
        """
        self.db_connection = db_connection
        self.schema_manager = SchemaManager()

    async def process_meetings(
        self,
        meetings: List[MeetingSummary],
        source_url: str,
        dry_run: bool = False,
        original_json_records: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, int]:
        """
        Process list of meeting summaries.

        Args:
            meetings: List of validated meeting summary models
            source_url: Source URL for logging
            dry_run: If True, validate without inserting
            original_json_records: Optional original JSON records for workgroup provenance

        Returns:
            Dictionary with processing statistics
        """
        stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "workgroups_created": 0,
        }

        if not meetings:
            logger.info(f"No meetings to process from {source_url}")
            return stats

        # Extract and UPSERT all unique workgroups first
        workgroups = self.schema_manager.extract_unique_workgroups(meetings, original_json_records)

        if not dry_run:
            async with self.db_connection.acquire() as conn:
                await self.schema_manager.upsert_workgroups(conn, workgroups)
                stats["workgroups_created"] = len(workgroups)

        # Process each meeting in atomic transaction
        total_meetings = len(meetings)
        for idx, meeting in enumerate(meetings, 1):
            try:
                # Progress logging for large datasets
                if idx % 10 == 0 or idx == total_meetings:
                    logger.info(
                        f"Processing meeting {idx}/{total_meetings} from {source_url}",
                        extra={
                            "source_url": source_url,
                            "records_processed": idx,
                            "total_records": total_meetings,
                        },
                    )
                if dry_run:
                    # In dry-run mode, just validate the structure
                    self._validate_meeting_structure(meeting)
                    stats["succeeded"] += 1
                else:
                    async with self.db_connection.acquire() as conn:
                        async with conn.transaction():
                            await self._process_single_meeting(conn, meeting, source_url)
                            stats["succeeded"] += 1

                stats["processed"] += 1

            except asyncpg.PostgresConnectionError as e:
                stats["failed"] += 1
                meeting_id = getattr(meeting, "id", "unknown")
                logger.error(
                    f"Database connection error processing meeting {meeting_id}: {e}",
                    extra={
                        "source_url": source_url,
                        "meeting_id": str(meeting_id),
                        "error": str(e),
                        "error_type": "database_connection_error",
                    },
                )
                # Continue processing other meetings
            except asyncpg.PostgresSyntaxError as e:
                stats["failed"] += 1
                meeting_id = getattr(meeting, "id", "unknown")
                logger.error(
                    f"SQL syntax error processing meeting {meeting_id}: {e}",
                    extra={
                        "source_url": source_url,
                        "meeting_id": str(meeting_id),
                        "error": str(e),
                        "error_type": "sql_syntax_error",
                    },
                )
                # Continue processing other meetings
            except asyncpg.UniqueViolationError as e:
                # This should not happen with UPSERT, but log if it does
                stats["failed"] += 1
                meeting_id = getattr(meeting, "id", "unknown")
                logger.warning(
                    f"Unique violation (should be handled by UPSERT) for meeting {meeting_id}: {e}",
                    extra={
                        "source_url": source_url,
                        "meeting_id": str(meeting_id),
                        "error": str(e),
                        "error_type": "unique_violation",
                    },
                )
                # Continue processing other meetings
            except Exception as e:
                stats["failed"] += 1
                meeting_id = getattr(meeting, "id", "unknown")
                logger.error(
                    f"Failed to process meeting {meeting_id}: {e}",
                    extra={
                        "source_url": source_url,
                        "meeting_id": str(meeting_id),
                        "error": str(e),
                        "error_type": "unknown_error",
                    },
                )
                # Continue processing other meetings

        logger.info(
            f"Processed {stats['processed']} meetings from {source_url}: "
            f"{stats['succeeded']} succeeded, {stats['failed']} failed",
            extra={
                "source_url": source_url,
                "processed": stats["processed"],
                "succeeded": stats["succeeded"],
                "failed": stats["failed"],
            },
        )

        return stats

    def _validate_meeting_structure(self, meeting: MeetingSummary) -> None:
        """Validate meeting structure (for dry-run mode)."""
        # Basic validation - Pydantic already validated the structure
        if not meeting.workgroup_id:
            raise ValueError("Missing workgroup_id")
        if not meeting.meetingInfo or not meeting.meetingInfo.date:
            raise ValueError("Missing meetingInfo.date")

    async def _process_single_meeting(
        self,
        conn: asyncpg.Connection,
        meeting: MeetingSummary,
        source_url: str,
    ) -> None:
        """
        Process a single meeting with all nested entities in atomic transaction.

        Args:
            conn: Database connection (within transaction)
            meeting: Meeting summary model
            source_url: Source URL for logging
        """
        # Generate meeting ID if not present
        meeting_id = uuid.uuid4()
        if hasattr(meeting, "id") and meeting.id:
            try:
                meeting_id = uuid.UUID(meeting.id)
            except (ValueError, AttributeError):
                pass

        workgroup_id = uuid.UUID(meeting.workgroup_id)

        # Parse meeting date (UTF-8 encoding support)
        date_str = str(meeting.meetingInfo.date).encode("utf-8").decode("utf-8")
        meeting_date = parse_date(date_str)
        if not meeting_date:
            raise ValueError(f"Invalid date format: {meeting.meetingInfo.date}")
        meeting_date = meeting_date.date()

        # Extract normalized fields (UTF-8 encoding support for Unicode/emoji)
        meeting_type = str(meeting.type).encode("utf-8").decode("utf-8") if meeting.type else None
        host = (
            str(meeting.meetingInfo.host).encode("utf-8").decode("utf-8")
            if meeting.meetingInfo.host
            else None
        )
        documenter = (
            str(meeting.meetingInfo.documenter).encode("utf-8").decode("utf-8")
            if meeting.meetingInfo.documenter
            else None
        )
        attendees = [
            str(attendee).encode("utf-8").decode("utf-8")
            for attendee in (meeting.meetingInfo.attendees or [])
        ]
        purpose = (
            str(meeting.meetingInfo.purpose).encode("utf-8").decode("utf-8")
            if meeting.meetingInfo.purpose
            else None
        )
        video_links = [
            str(link).encode("utf-8").decode("utf-8")
            for link in (meeting.meetingInfo.videoLinks or [])
        ]
        working_docs = meeting.meetingInfo.workingDocs  # JSONB handles Unicode
        timestamped_video = meeting.meetingInfo.timestampedVideo  # JSONB handles Unicode
        tags = meeting.tags or {}  # JSONB handles Unicode

        # Convert to dict for JSONB storage
        raw_json = meeting.model_dump()

        # Check for circular references (max depth check)
        if detect_circular_reference(raw_json, max_depth=10):
            logger.warning(
                f"Circular reference detected in meeting {meeting_id}, skipping",
                extra={
                    "source_url": source_url,
                    "meeting_id": str(meeting_id),
                    "error_type": "circular_reference",
                },
            )
            raise ValueError("Circular reference detected in meeting data")

        # UPSERT meeting
        await Meeting.upsert(
            conn=conn,
            id=meeting_id,
            workgroup_id=workgroup_id,
            date=meeting_date,
            type=meeting_type,
            host=host,
            documenter=documenter,
            attendees=attendees,
            purpose=purpose,
            video_links=video_links,
            working_docs=working_docs,
            timestamped_video=timestamped_video,
            tags=tags,
            raw_json=raw_json,
        )

        # Process agenda items with nested entities
        for idx, agenda_item in enumerate(meeting.agendaItems or []):
            # Generate agenda item ID if not present
            agenda_item_id = uuid.uuid4()
            if agenda_item.id:
                try:
                    agenda_item_id = uuid.UUID(agenda_item.id)
                except (ValueError, AttributeError):
                    pass

            # Extract normalized fields
            status = agenda_item.status
            order_index = idx  # Use array index as order

            # UPSERT agenda item
            await AgendaItem.upsert(
                conn=conn,
                id=agenda_item_id,
                meeting_id=meeting_id,
                status=status,
                order_index=order_index,
                raw_json=agenda_item.model_dump(),
            )

            # Process action items
            for action_item in agenda_item.actionItems or []:
                action_item_id = uuid.uuid4()
                if action_item.id:
                    try:
                        action_item_id = uuid.UUID(action_item.id)
                    except (ValueError, AttributeError):
                        pass

                # Parse due date
                due_date = None
                if action_item.dueDate:
                    parsed_date = parse_date(action_item.dueDate)
                    if parsed_date:
                        due_date = parsed_date.date()

                # UTF-8 encoding support for text fields
                action_text = str(action_item.text).encode("utf-8").decode("utf-8")
                action_assignee = (
                    str(action_item.assignee).encode("utf-8").decode("utf-8")
                    if action_item.assignee
                    else None
                )
                action_status = (
                    str(action_item.status).encode("utf-8").decode("utf-8")
                    if action_item.status
                    else None
                )

                await ActionItem.upsert(
                    conn=conn,
                    id=action_item_id,
                    agenda_item_id=agenda_item_id,
                    text=action_text,
                    assignee=action_assignee,
                    due_date=due_date,
                    status=action_status,
                    raw_json=action_item.model_dump(),
                )

            # Process decision items
            for decision_item in agenda_item.decisionItems or []:
                decision_item_id = uuid.uuid4()
                if decision_item.id:
                    try:
                        decision_item_id = uuid.UUID(decision_item.id)
                    except (ValueError, AttributeError):
                        pass

                # UTF-8 encoding support for text fields
                decision_text = str(decision_item.decision).encode("utf-8").decode("utf-8")
                decision_rationale = (
                    str(decision_item.rationale).encode("utf-8").decode("utf-8")
                    if decision_item.rationale
                    else None
                )
                decision_scope = (
                    str(decision_item.effectScope).encode("utf-8").decode("utf-8")
                    if decision_item.effectScope
                    else None
                )

                await DecisionItem.upsert(
                    conn=conn,
                    id=decision_item_id,
                    agenda_item_id=agenda_item_id,
                    decision_text=decision_text,
                    rationale=decision_rationale,
                    effect_scope=decision_scope,
                    raw_json=decision_item.model_dump(),
                )

            # Process discussion points
            for discussion_point in agenda_item.discussionPoints or []:
                discussion_point_id = uuid.uuid4()
                if discussion_point.id:
                    try:
                        discussion_point_id = uuid.UUID(discussion_point.id)
                    except (ValueError, AttributeError):
                        pass

                # UTF-8 encoding support for text fields
                point_text = str(discussion_point.point).encode("utf-8").decode("utf-8")

                await DiscussionPoint.upsert(
                    conn=conn,
                    id=discussion_point_id,
                    agenda_item_id=agenda_item_id,
                    point_text=point_text,
                    raw_json=discussion_point.model_dump(),
                )
