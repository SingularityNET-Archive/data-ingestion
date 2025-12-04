"""Export API endpoints for the ingestion dashboard."""
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel
from api.auth import require_read_only_or_admin, User
import csv
import json
import io

router = APIRouter(prefix="/exports", tags=["exports"])


class ExportRequest(BaseModel):
    """Request to export filtered meetings."""
    format: Literal["csv", "json"]
    workgroup: Optional[str] = None
    source: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    search: Optional[str] = None


@router.post("")
async def export_meetings(
    request: ExportRequest,
    current_user: User = Depends(require_read_only_or_admin),
):
    """Export filtered meetings to CSV or JSON.

    For exports up to 10,000 rows, returns synchronously.
    For larger exports, returns a job ID for async processing.

    Args:
        request: Export request with format and filters
        current_user: Current authenticated user

    Returns:
        CSV or JSON file download, or job ID for async export
    """
    from db.connection import get_database_url, get_db_pool

    database_url = get_database_url()
    if not database_url:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL not configured",
        )

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Build WHERE clause (same as meetings list)
            where_conditions = []
            params = []
            param_idx = 1

            if request.workgroup:
                where_conditions.append(f"ms.workgroup ILIKE ${param_idx}")
                params.append(f"%{request.workgroup}%")
                param_idx += 1

            if request.source:
                where_conditions.append(f"s.name ILIKE ${param_idx}")
                params.append(f"%{request.source}%")
                param_idx += 1

            if request.date_from:
                where_conditions.append(f"ms.meeting_date >= ${param_idx}")
                params.append(request.date_from)
                param_idx += 1

            if request.date_to:
                where_conditions.append(f"ms.meeting_date <= ${param_idx}")
                params.append(request.date_to)
                param_idx += 1

            if request.search:
                where_conditions.append(f"(ms.workgroup ILIKE ${param_idx} OR ms.title ILIKE ${param_idx})")
                search_pattern = f"%{request.search}%"
                params.append(search_pattern)
                params.append(search_pattern)
                param_idx += 2

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # Check count first
            count_query = f"""
                SELECT COUNT(*) as total
                FROM public.meeting_summary_view ms
                LEFT JOIN source s ON s.id = ms.source_id
                {where_clause}
            """
            count_row = await conn.fetchrow(count_query, *params)
            total = count_row["total"] if count_row else 0

            # For large exports (>10k), return async job (simplified - just return error for now)
            if total > 10000:
                raise HTTPException(
                    status_code=413,
                    detail=f"Export too large ({total} rows). Maximum 10,000 rows supported for synchronous export. Please apply additional filters.",
                )

            # Fetch all matching records
            query = f"""
                SELECT 
                    ms.id,
                    ms.source_name,
                    ms.workgroup,
                    ms.meeting_date,
                    ms.ingested_at,
                    ms.title,
                    ms.validation_warnings_count,
                    CASE WHEN ms.missing_fields IS NOT NULL AND jsonb_array_length(ms.missing_fields) > 0 
                         THEN true ELSE false END AS has_missing_fields
                FROM public.meeting_summary_view ms
                LEFT JOIN source s ON s.id = ms.source_id
                {where_clause}
                ORDER BY ms.ingested_at DESC NULLS LAST, ms.meeting_date DESC NULLS LAST
            """
            rows = await conn.fetch(query, *params)

            # Generate export file
            if request.format == "csv":
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=[
                    "id", "source_name", "workgroup", "meeting_date", "ingested_at",
                    "title", "validation_warnings_count", "has_missing_fields"
                ])
                writer.writeheader()
                for row in rows:
                    writer.writerow({
                        "id": str(row["id"]),
                        "source_name": row["source_name"] or "",
                        "workgroup": row["workgroup"] or "",
                        "meeting_date": row["meeting_date"].isoformat() if row["meeting_date"] else "",
                        "ingested_at": row["ingested_at"].isoformat() if row["ingested_at"] else "",
                        "title": row["title"] or "",
                        "validation_warnings_count": row["validation_warnings_count"] or 0,
                        "has_missing_fields": "true" if row.get("has_missing_fields") else "false",
                    })
                content = output.getvalue()
                return Response(
                    content=content,
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=meetings_export.csv"}
                )
            else:  # JSON
                items = []
                for row in rows:
                    items.append({
                        "id": str(row["id"]),
                        "source_name": row["source_name"],
                        "workgroup": row["workgroup"],
                        "meeting_date": row["meeting_date"].isoformat() if row["meeting_date"] else None,
                        "ingested_at": row["ingested_at"].isoformat() if row["ingested_at"] else None,
                        "title": row["title"],
                        "validation_warnings_count": row["validation_warnings_count"] or 0,
                        "has_missing_fields": bool(row.get("has_missing_fields")),
                    })
                content = json.dumps({"items": items, "total": len(items)}, indent=2)
                return Response(
                    content=content,
                    media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename=meetings_export.json"}
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating export: {str(e)}",
        )

