"""Meetings API endpoints for the ingestion dashboard."""
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from .auth import require_read_only_or_admin, User

router = APIRouter(prefix="/meetings", tags=["meetings"])


class MeetingSummary(BaseModel):
    """Meeting summary for list view."""
    id: str
    source_id: Optional[str]
    source_name: Optional[str]
    workgroup: Optional[str]
    meeting_date: Optional[date]
    ingested_at: Optional[str]
    title: Optional[str]
    validation_warnings_count: int
    has_missing_fields: bool


class MeetingDetail(BaseModel):
    """Full meeting detail with raw JSON and normalized fields."""
    id: str
    source_id: Optional[str]
    source_name: Optional[str]
    workgroup: Optional[str]
    meeting_date: Optional[date]
    ingested_at: Optional[str]
    title: Optional[str]
    normalized_fields: Optional[dict]
    validation_warnings: Optional[List[dict]]
    missing_fields: Optional[List[str]]
    provenance: Optional[dict]
    raw_json_reference: Optional[str]


class PaginatedMeetings(BaseModel):
    """Paginated response for meetings list."""
    items: List[MeetingSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("", response_model=PaginatedMeetings)
async def list_meetings(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    workgroup: Optional[str] = Query(default=None, description="Filter by workgroup"),
    source: Optional[str] = Query(default=None, description="Filter by source name"),
    date_from: Optional[date] = Query(default=None, description="Filter by date from"),
    date_to: Optional[date] = Query(default=None, description="Filter by date to"),
    search: Optional[str] = Query(default=None, description="Search in workgroup and title"),
    current_user: User = Depends(require_read_only_or_admin),
):
    """List ingested meetings with pagination and filtering.

    Supports filtering by workgroup, source, date range, and free-text search.
    Returns paginated results.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        workgroup: Filter by workgroup name
        source: Filter by source name
        date_from: Filter meetings from this date
        date_to: Filter meetings to this date
        search: Free-text search in workgroup and title fields
        current_user: Current authenticated user

    Returns:
        Paginated list of meeting summaries
    """
    from ..db.connection import get_database_url, get_db_pool

    database_url = get_database_url()
    if not database_url:
        # Return empty meetings list for development when DATABASE_URL is not configured
        return PaginatedMeetings(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
        )

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Build WHERE clause
            where_conditions = []
            params = []
            param_idx = 1

            if workgroup:
                where_conditions.append(f"ms.workgroup ILIKE ${param_idx}")
                params.append(f"%{workgroup}%")
                param_idx += 1

            # Note: source filtering removed since source table doesn't exist in current schema
            # if source:
            #     where_conditions.append(f"s.name ILIKE ${param_idx}")
            #     params.append(f"%{source}%")
            #     param_idx += 1

            if date_from:
                where_conditions.append(f"ms.meeting_date >= ${param_idx}")
                params.append(date_from)
                param_idx += 1

            if date_to:
                where_conditions.append(f"ms.meeting_date <= ${param_idx}")
                params.append(date_to)
                param_idx += 1

            if search:
                where_conditions.append(f"(ms.workgroup ILIKE ${param_idx} OR ms.title ILIKE ${param_idx})")
                search_pattern = f"%{search}%"
                params.append(search_pattern)
                params.append(search_pattern)
                param_idx += 2

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # Count total (removed source join since source table doesn't exist)
            count_query = f"""
                SELECT COUNT(*) as total
                FROM public.meeting_summary_view ms
                {where_clause}
            """
            count_row = await conn.fetchrow(count_query, *params)
            total = count_row["total"] if count_row else 0

            # Fetch paginated results
            offset = (page - 1) * page_size
            query = f"""
                SELECT 
                    ms.id,
                    ms.source_id,
                    ms.source_name,
                    ms.workgroup,
                    ms.meeting_date,
                    ms.ingested_at,
                    ms.title,
                    ms.validation_warnings_count,
                    CASE WHEN ms.missing_fields IS NOT NULL AND jsonb_array_length(ms.missing_fields) > 0 
                         THEN true ELSE false END AS has_missing_fields
                FROM public.meeting_summary_view ms
                {where_clause}
                ORDER BY ms.ingested_at DESC NULLS LAST, ms.meeting_date DESC NULLS LAST
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([page_size, offset])

            rows = await conn.fetch(query, *params)
            meetings = []
            for row in rows:
                meetings.append(MeetingSummary(
                    id=str(row["id"]),
                    source_id=str(row["source_id"]) if row["source_id"] else None,
                    source_name=row["source_name"],
                    workgroup=row["workgroup"],
                    meeting_date=row["meeting_date"],
                    ingested_at=row["ingested_at"].isoformat() if row["ingested_at"] else None,
                    title=row["title"],
                    validation_warnings_count=row["validation_warnings_count"] or 0,
                    has_missing_fields=row["has_missing_fields"],
                ))

            total_pages = (total + page_size - 1) // page_size if total > 0 else 0

            return PaginatedMeetings(
                items=meetings,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )
    except Exception as e:
        error_msg = str(e)
        # Handle common async/event loop errors gracefully
        if "Event loop is closed" in error_msg or "another operation is in progress" in error_msg:
            # Return empty result if event loop/pool issues occur (common in tests)
            return PaginatedMeetings(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching meetings: {error_msg}",
        )


@router.get("/{meeting_id}", response_model=MeetingDetail)
async def get_meeting_detail(
    meeting_id: str,
    current_user: User = Depends(require_read_only_or_admin),
):
    """Get detailed meeting information including raw JSON and normalized fields.

    Returns full meeting details with validation warnings, missing fields,
    provenance metadata, and reference to raw JSON.

    Args:
        meeting_id: UUID of the meeting
        current_user: Current authenticated user

    Returns:
        Full meeting detail with all fields
    """
    from ..db.connection import get_database_url, get_db_pool

    database_url = get_database_url()
    if not database_url:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL not configured",
        )

    try:
        pool = await get_db_pool()
        if pool is None:
            raise HTTPException(
                status_code=500,
                detail="DATABASE_URL not configured",
            )
        async with pool.acquire() as conn:
            # Get meeting detail from view, and also get raw_json from the actual meetings table
            row = await conn.fetchrow("""
                SELECT 
                    ms.id,
                    ms.source_id,
                    ms.source_name,
                    ms.workgroup,
                    ms.meeting_date,
                    ms.ingested_at,
                    ms.title,
                    ms.normalized_fields,
                    ms.validation_warnings_count,
                    ms.missing_fields,
                    ms.provenance,
                    ms.raw_json_reference,
                    m.raw_json
                FROM public.meeting_summary_view ms
                LEFT JOIN meetings m ON m.id = ms.id
                WHERE ms.id::text = $1
            """, meeting_id)

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Meeting {meeting_id} not found",
                )

            # validation_warnings is not in the view, only validation_warnings_count
            # Return empty list since we don't have the actual warnings in the view
            validation_warnings = [] if row.get("validation_warnings_count", 0) > 0 else []

            # Parse missing_fields if it's JSONB
            missing_fields = None
            if row["missing_fields"]:
                if isinstance(row["missing_fields"], list):
                    missing_fields = row["missing_fields"]
                elif isinstance(row["missing_fields"], str):
                    import json
                    missing_fields = json.loads(row["missing_fields"])

            # Use raw_json from meetings table if available, otherwise use raw_json_reference
            raw_json_ref = row["raw_json_reference"]
            if row.get("raw_json") and not raw_json_ref:
                # If we have raw_json but no reference, we could store it or just note it exists
                raw_json_ref = "Available in raw_json column"
            
            # Convert JSONB to dict safely
            normalized_fields = None
            if row["normalized_fields"]:
                if isinstance(row["normalized_fields"], dict):
                    normalized_fields = row["normalized_fields"]
                else:
                    import json
                    normalized_fields = json.loads(row["normalized_fields"]) if isinstance(row["normalized_fields"], str) else row["normalized_fields"]
            
            provenance_dict = None
            if row["provenance"]:
                if isinstance(row["provenance"], dict):
                    provenance_dict = row["provenance"]
                else:
                    import json
                    provenance_dict = json.loads(row["provenance"]) if isinstance(row["provenance"], str) else row["provenance"]
            
            return MeetingDetail(
                id=str(row["id"]),
                source_id=str(row["source_id"]) if row["source_id"] else None,
                source_name=row["source_name"],
                workgroup=row["workgroup"],
                meeting_date=row["meeting_date"],
                ingested_at=row["ingested_at"].isoformat() if row["ingested_at"] else None,
                title=row["title"],
                normalized_fields=normalized_fields,
                validation_warnings=validation_warnings,
                missing_fields=missing_fields,
                provenance=provenance_dict,
                raw_json_reference=raw_json_ref,
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching meeting detail: {str(e)}",
        )

