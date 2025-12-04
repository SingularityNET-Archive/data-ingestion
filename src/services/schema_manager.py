"""Schema manager service for workgroup pre-processing."""

import json
import uuid
from typing import Any, Dict, List, Optional

import asyncpg

from src.lib.logger import get_logger
from src.models.meeting_summary import MeetingSummary
from src.models.workgroup import Workgroup

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
        import sys
        print(f"[DEBUG] extract_unique_workgroups ENTRY: {len(meetings)} meetings", file=sys.stderr, flush=True)
        
        workgroups: Dict[uuid.UUID, Dict[str, Any]] = {}

        # Create mapping of workgroup_id to original JSON if provided
        print(f"[DEBUG] Building json_by_workgroup mapping...", file=sys.stderr, flush=True)
        json_by_workgroup: Dict[uuid.UUID, Dict[str, Any]] = {}
        if original_json_records:
            print(f"[DEBUG] Processing {len(original_json_records)} original JSON records...", file=sys.stderr, flush=True)
            for idx, json_record in enumerate(original_json_records):
                if idx % 50 == 0:
                    print(f"[DEBUG] Processing JSON record {idx}/{len(original_json_records)}", file=sys.stderr, flush=True)
                workgroup_id = uuid.UUID(json_record.get("workgroup_id", ""))
                if workgroup_id not in json_by_workgroup:
                    json_by_workgroup[workgroup_id] = json_record
            print(f"[DEBUG] Built json_by_workgroup with {len(json_by_workgroup)} entries", file=sys.stderr, flush=True)

        print(f"[DEBUG] Processing {len(meetings)} meetings for workgroup extraction...", file=sys.stderr, flush=True)
        for idx, meeting in enumerate(meetings):
            if idx % 50 == 0 and idx > 0:
                print(f"[DEBUG] Processing meeting {idx}/{len(meetings)}", file=sys.stderr, flush=True)
                logger.debug(f"Processing meeting {idx}/{len(meetings)} for workgroup extraction")
            
            workgroup_id = uuid.UUID(meeting.workgroup_id)

            if workgroup_id not in workgroups:
                # Use original JSON if available (faster), otherwise use meeting dict
                if workgroup_id in json_by_workgroup:
                    raw_json = json_by_workgroup[workgroup_id]
                    if idx < 5:  # Only log first few
                        print(f"[DEBUG] Using original JSON for workgroup {workgroup_id}", file=sys.stderr, flush=True)
                else:
                    # Only call model_dump() if we don't have original JSON
                    print(f"[DEBUG] Calling model_dump() for workgroup {workgroup_id} (meeting {idx})", file=sys.stderr, flush=True)
                    raw_json = meeting.model_dump()
                    print(f"[DEBUG] model_dump() completed for meeting {idx}", file=sys.stderr, flush=True)

                workgroups[workgroup_id] = {
                    "id": workgroup_id,
                    "name": meeting.workgroup,
                    "raw_json": raw_json,
                }

        print(f"[DEBUG] extract_unique_workgroups COMPLETE: {len(workgroups)} workgroups", file=sys.stderr, flush=True)
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
        import sys
        print(f"[DEBUG] upsert_workgroups ENTRY: {len(workgroups)} workgroups", file=sys.stderr, flush=True)
        logger.info(f"UPSERTing {len(workgroups)} workgroups...")

        for idx, (workgroup_id, workgroup_data) in enumerate(workgroups.items()):
            if idx % 5 == 0:
                print(f"[DEBUG] UPSERTing workgroup {idx+1}/{len(workgroups)}: {workgroup_id}", file=sys.stderr, flush=True)
            try:
                print(f"[DEBUG] Calling Workgroup.upsert for {workgroup_id}...", file=sys.stderr, flush=True)
                await Workgroup.upsert(
                    conn=conn,
                    id=workgroup_id,
                    name=workgroup_data["name"],
                    raw_json=workgroup_data.get("raw_json", {}),
                )
                print(f"[DEBUG] Workgroup.upsert completed for {workgroup_id}", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"[DEBUG] ERROR in Workgroup.upsert for {workgroup_id}: {e}", file=sys.stderr, flush=True)
                logger.error(
                    f"Failed to UPSERT workgroup {workgroup_id}: {e}",
                    extra={"workgroup_id": str(workgroup_id), "error": str(e)},
                )
                raise

        print(f"[DEBUG] upsert_workgroups COMPLETE: {len(workgroups)} workgroups", file=sys.stderr, flush=True)
        logger.info(f"Successfully UPSERTed {len(workgroups)} workgroups")
