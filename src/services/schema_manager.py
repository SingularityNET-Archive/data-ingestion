"""Schema manager service for workgroup pre-processing."""

import uuid
from typing import List, Dict, Set, Any, Optional
import asyncpg

from src.models.meeting_summary import MeetingSummary
from src.models.workgroup import Workgroup
from src.lib.logger import get_logger

logger = get_logger(__name__)


class SchemaManager:
    """Manages schema-level operations like workgroup extraction and UPSERT."""

    @staticmethod
    def extract_unique_workgroups(
        meetings: List[MeetingSummary],
        original_json_records: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[uuid.UUID, Dict[str, Any]]:
        """
        Extract unique workgroups from meeting summaries.

        Args:
            meetings: List of meeting summary models
            original_json_records: Optional list of original JSON records for provenance

        Returns:
            Dictionary mapping workgroup UUID to workgroup data
        """
        workgroups: Dict[uuid.UUID, Dict[str, Any]] = {}

        # Create mapping of workgroup_id to original JSON if provided
        json_by_workgroup: Dict[uuid.UUID, Dict[str, Any]] = {}
        if original_json_records:
            for json_record in original_json_records:
                workgroup_id = uuid.UUID(json_record.get("workgroup_id", ""))
                if workgroup_id not in json_by_workgroup:
                    json_by_workgroup[workgroup_id] = json_record

        for meeting in meetings:
            workgroup_id = uuid.UUID(meeting.workgroup_id)

            if workgroup_id not in workgroups:
                # Use original JSON if available, otherwise use meeting dict
                raw_json = json_by_workgroup.get(workgroup_id, meeting.dict())

                workgroups[workgroup_id] = {
                    "id": workgroup_id,
                    "name": meeting.workgroup,
                    "raw_json": raw_json,
                }

        logger.info(f"Extracted {len(workgroups)} unique workgroups")
        return workgroups

    @staticmethod
    async def upsert_workgroups(
        conn: asyncpg.Connection,
        workgroups: Dict[uuid.UUID, Dict[str, Any]],
    ) -> None:
        """
        UPSERT all unique workgroups into database.

        Args:
            conn: Database connection
            workgroups: Dictionary mapping workgroup UUID to workgroup data
        """
        logger.info(f"UPSERTing {len(workgroups)} workgroups...")

        for workgroup_id, workgroup_data in workgroups.items():
            try:
                await Workgroup.upsert(
                    conn=conn,
                    id=workgroup_id,
                    name=workgroup_data["name"],
                    raw_json=workgroup_data.get("raw_json", {}),
                )
            except Exception as e:
                logger.error(
                    f"Failed to UPSERT workgroup {workgroup_id}: {e}",
                    extra={"workgroup_id": str(workgroup_id), "error": str(e)},
                )
                raise

        logger.info(f"Successfully UPSERTed {len(workgroups)} workgroups")



