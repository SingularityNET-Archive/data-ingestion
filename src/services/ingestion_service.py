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
        # Log immediately at function entry - use print as backup
        import sys
        print(f"[DEBUG] process_meetings ENTRY: {len(meetings)} meetings", file=sys.stderr, flush=True)
        try:
            logger.info(
                f"process_meetings ENTRY: {len(meetings)} meetings, dry_run={dry_run}",
                extra={
                    "source_url": source_url,
                    "meeting_count": len(meetings),
                    "dry_run": dry_run,
                    "has_original_json": original_json_records is not None,
                },
            )
        except Exception as e:
            # If logging fails, at least print to stderr
            print(f"ERROR: Failed to log in process_meetings: {e}", file=sys.stderr, flush=True)
            raise
        
        print(f"[DEBUG] Initializing stats...", file=sys.stderr, flush=True)
        stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "workgroups_created": 0,
        }

        if not meetings:
            logger.info(f"No meetings to process from {source_url}")
            return stats
        
        print(f"[DEBUG] Starting workgroup extraction...", file=sys.stderr, flush=True)
        logger.info(f"Extracting workgroups from {len(meetings)} meetings...")
        
        print(f"[DEBUG] Calling extract_unique_workgroups...", file=sys.stderr, flush=True)
        workgroups = self.schema_manager.extract_unique_workgroups(meetings, original_json_records)
        print(f"[DEBUG] Workgroup extraction completed: {len(workgroups)} workgroups", file=sys.stderr, flush=True)
        logger.info(f"Extracted {len(workgroups)} unique workgroups")

        if not dry_run:
            print(f"[DEBUG] Starting workgroup UPSERT for {len(workgroups)} workgroups...", file=sys.stderr, flush=True)
            logger.info(f"Starting workgroup UPSERT for {len(workgroups)} workgroups...")
            print(f"[DEBUG] About to acquire database connection...", file=sys.stderr, flush=True)
            async with self.db_connection.acquire() as conn:
                print(f"[DEBUG] Database connection acquired for workgroup UPSERT", file=sys.stderr, flush=True)
                logger.debug("Database connection acquired for workgroup UPSERT")
                print(f"[DEBUG] Calling upsert_workgroups...", file=sys.stderr, flush=True)
                await self.schema_manager.upsert_workgroups(conn, workgroups)
                print(f"[DEBUG] upsert_workgroups completed", file=sys.stderr, flush=True)
                logger.debug("Workgroup UPSERT completed")
            print(f"[DEBUG] Exited database connection context", file=sys.stderr, flush=True)
            stats["workgroups_created"] = len(workgroups)
            logger.info(f"Workgroups processed: {stats['workgroups_created']}")

        # Process each meeting in atomic transaction
        total_meetings = len(meetings)
        print(f"[DEBUG] Starting to process {total_meetings} meetings", file=sys.stderr, flush=True)
        logger.info(
            f"Starting to process {total_meetings} meetings from {source_url}",
            extra={
                "source_url": source_url,
                "total_records": total_meetings,
            },
        )
        for idx, meeting in enumerate(meetings, 1):
            try:
                # Progress logging for large datasets
                if idx % 10 == 0 or idx == total_meetings or idx == 1:
                    print(f"[DEBUG] Processing meeting {idx}/{total_meetings}", file=sys.stderr, flush=True)
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
                    print(f"[DEBUG] About to process meeting {idx} (not dry-run)", file=sys.stderr, flush=True)
                    try:
                        print(f"[DEBUG] Acquiring connection for meeting {idx}...", file=sys.stderr, flush=True)
                        async with self.db_connection.acquire() as conn:
                            print(f"[DEBUG] Connection acquired, starting transaction for meeting {idx}...", file=sys.stderr, flush=True)
                            async with conn.transaction():
                                print(f"[DEBUG] Transaction started, calling _process_single_meeting for meeting {idx}...", file=sys.stderr, flush=True)
                                await self._process_single_meeting(conn, meeting, source_url)
                                print(f"[DEBUG] _process_single_meeting completed for meeting {idx}", file=sys.stderr, flush=True)
                                stats["succeeded"] += 1
                            print(f"[DEBUG] Transaction committed for meeting {idx}", file=sys.stderr, flush=True)
                        print(f"[DEBUG] Connection released for meeting {idx}", file=sys.stderr, flush=True)
                    except Exception as e:
                        print(f"[DEBUG] Exception processing meeting {idx}: {e}", file=sys.stderr, flush=True)
                        # Log and re-raise to be caught by outer exception handler
                        meeting_id_str = "unknown"
                        try:
                            # Try to get meeting ID for logging
                            if hasattr(meeting, "id") and meeting.id:
                                meeting_id_str = str(meeting.id)
                        except:
                            pass
                        logger.error(
                            f"Error processing meeting {meeting_id_str} (idx {idx}): {e}",
                            extra={
                                "source_url": source_url,
                                "meeting_index": idx,
                                "error": str(e),
                                "error_type": type(e).__name__,
                            },
                        )
                        raise

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
        import sys
        print(f"[DEBUG] _process_single_meeting ENTRY", file=sys.stderr, flush=True)
        workgroup_id = uuid.UUID(meeting.workgroup_id)
        print(f"[DEBUG] Parsed workgroup_id: {workgroup_id}", file=sys.stderr, flush=True)

        # Parse meeting date (UTF-8 encoding support)
        date_str = str(meeting.meetingInfo.date).encode("utf-8").decode("utf-8")
        meeting_date = parse_date(date_str)
        if not meeting_date:
            raise ValueError(f"Invalid date format: {meeting.meetingInfo.date}")
        meeting_date = meeting_date.date()

        # Generate deterministic meeting ID if not present in source
        # Use a hash of the meeting content to ensure uniqueness while preventing duplicates
        # This ensures the same meeting always gets the same ID, preventing duplicates
        meeting_id = None
        if hasattr(meeting, "id") and meeting.id:
            try:
                meeting_id = uuid.UUID(meeting.id)
            except (ValueError, AttributeError):
                pass
        
        if not meeting_id:
            # Generate deterministic UUID v5 based on workgroup_id + date + key fields
            # Use host and purpose as additional uniqueness factors to distinguish
            # between different meetings that happen to have the same workgroup_id + date
            import hashlib
            
            # Generate ID based on workgroup_id + date + key identifying fields
            # This ensures different meetings with same workgroup_id + date get different IDs
            host_str = str(meeting.meetingInfo.host) if meeting.meetingInfo.host else ""
            purpose_str = str(meeting.meetingInfo.purpose) if meeting.meetingInfo.purpose else ""
            # Include agenda item count as additional uniqueness factor
            agenda_count = len(meeting.agendaItems) if meeting.agendaItems else 0
            
            # Create a stable hash from key fields
            key_fields = f"{workgroup_id}:{meeting_date}:{host_str}:{purpose_str}:{agenda_count}"
            content_hash = hashlib.sha256(key_fields.encode('utf-8')).hexdigest()[:16]
            
            MEETING_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace
            deterministic_string = f"{workgroup_id}:{meeting_date}:{content_hash}"
            meeting_id = uuid.uuid5(MEETING_NAMESPACE, deterministic_string)
            
            # Check if this ID already exists (for logging)
            existing = await conn.fetchrow("SELECT id FROM meetings WHERE id = $1", meeting_id)
            if existing:
                logger.debug(
                    f"Meeting ID {meeting_id} already exists (will be updated via UPSERT)",
                    extra={
                        "meeting_id": str(meeting_id),
                        "workgroup_id": str(workgroup_id),
                        "date": str(meeting_date),
                    },
                )

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

        # Convert to dict for JSONB storage (reuse cached version if available from ID generation)
        if hasattr(meeting, "_cached_model_dump"):
            raw_json = meeting._cached_model_dump
        else:
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
            # Generate deterministic agenda item ID if not present
            agenda_item_id = None
            if agenda_item.id:
                try:
                    agenda_item_id = uuid.UUID(agenda_item.id)
                except (ValueError, AttributeError):
                    pass
            
            if not agenda_item_id:
                # Generate deterministic UUID based on meeting_id + order_index
                AGENDA_ITEM_NAMESPACE = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
                deterministic_string = f"{meeting_id}:agenda:{idx}"
                agenda_item_id = uuid.uuid5(AGENDA_ITEM_NAMESPACE, deterministic_string)

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
            for action_idx, action_item in enumerate(agenda_item.actionItems or []):
                action_item_id = None
                if action_item.id:
                    try:
                        action_item_id = uuid.UUID(action_item.id)
                    except (ValueError, AttributeError):
                        pass
                
                if not action_item_id:
                    # Generate deterministic UUID based on agenda_item_id + order_index
                    ACTION_ITEM_NAMESPACE = uuid.UUID("6ba7b812-9dad-11d1-80b4-00c04fd430c8")
                    deterministic_string = f"{agenda_item_id}:action:{action_idx}"
                    action_item_id = uuid.uuid5(ACTION_ITEM_NAMESPACE, deterministic_string)

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
            for decision_idx, decision_item in enumerate(agenda_item.decisionItems or []):
                decision_item_id = None
                if decision_item.id:
                    try:
                        decision_item_id = uuid.UUID(decision_item.id)
                    except (ValueError, AttributeError):
                        pass
                
                if not decision_item_id:
                    # Generate deterministic UUID based on agenda_item_id + order_index
                    DECISION_ITEM_NAMESPACE = uuid.UUID("6ba7b813-9dad-11d1-80b4-00c04fd430c8")
                    deterministic_string = f"{agenda_item_id}:decision:{decision_idx}"
                    decision_item_id = uuid.uuid5(DECISION_ITEM_NAMESPACE, deterministic_string)

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
            for discussion_idx, discussion_point in enumerate(agenda_item.discussionPoints or []):
                discussion_point_id = None
                if discussion_point.id:
                    try:
                        discussion_point_id = uuid.UUID(discussion_point.id)
                    except (ValueError, AttributeError):
                        pass
                
                if not discussion_point_id:
                    # Generate deterministic UUID based on agenda_item_id + order_index
                    DISCUSSION_POINT_NAMESPACE = uuid.UUID("6ba7b814-9dad-11d1-80b4-00c04fd430c8")
                    deterministic_string = f"{agenda_item_id}:discussion:{discussion_idx}"
                    discussion_point_id = uuid.uuid5(DISCUSSION_POINT_NAMESPACE, deterministic_string)

                # UTF-8 encoding support for text fields
                point_text = str(discussion_point.point).encode("utf-8").decode("utf-8")

                await DiscussionPoint.upsert(
                    conn=conn,
                    id=discussion_point_id,
                    agenda_item_id=agenda_item_id,
                    point_text=point_text,
                    raw_json=discussion_point.model_dump(),
                )
