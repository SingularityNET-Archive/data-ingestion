"""Ingestion runs API endpoints for the ingestion dashboard."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from .auth import require_read_only_or_admin, User

router = APIRouter(prefix="/runs", tags=["runs"])


class IngestionRun(BaseModel):
    """Ingestion run summary."""
    id: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    status: Optional[str]
    records_processed: int
    records_failed: int
    duplicates_avoided: int


class MonthlyAggregate(BaseModel):
    """Monthly ingestion aggregate."""
    month: str
    records_ingested: int
    records_with_warnings: int


@router.get("", response_model=List[IngestionRun])
async def list_runs(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of runs to return"),
    current_user: User = Depends(require_read_only_or_admin),
):
    """List ingestion runs.

    Returns recent ingestion runs ordered by start time (most recent first).

    Args:
        limit: Maximum number of runs to return (default: 100, max: 1000)
        current_user: Current authenticated user

    Returns:
        List of ingestion runs
    """
    from ..db.connection import get_database_url, get_db_pool

    database_url = get_database_url()
    if not database_url:
        # Return empty runs list for development when DATABASE_URL is not configured
        return []

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id,
                    started_at,
                    finished_at,
                    status,
                    records_processed,
                    records_failed,
                    duplicates_avoided
                FROM public.ingestion_run_view
                ORDER BY started_at DESC NULLS LAST, finished_at DESC NULLS LAST
                LIMIT $1
            """, limit)

            runs = []
            for row in rows:
                runs.append(IngestionRun(
                    id=str(row["id"]),
                    started_at=row["started_at"],
                    finished_at=row["finished_at"],
                    status=row["status"],
                    records_processed=row["records_processed"] or 0,
                    records_failed=row["records_failed"] or 0,
                    duplicates_avoided=row["duplicates_avoided"] or 0,
                ))
            return runs
    except Exception as e:
        error_msg = str(e)
        # Handle common async/event loop errors gracefully
        if "Event loop is closed" in error_msg or "another operation is in progress" in error_msg:
            return []
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching ingestion runs: {error_msg}",
        )


@router.get("/monthly", response_model=List[MonthlyAggregate])
async def get_monthly_aggregates(
    months: int = Query(default=12, ge=1, le=60, description="Number of months of history"),
    current_user: User = Depends(require_read_only_or_admin),
):
    """Get monthly ingestion aggregates for trend visualization.

    Returns time-series data for ingestion volume per month.
    Data comes from the materialized view `mv_ingestion_monthly`.

    Args:
        months: Number of months of history to return (default: 12, max: 60)
        current_user: Current authenticated user

    Returns:
        List of monthly aggregates ordered by month
    """
    from ..db.connection import get_database_url, get_db_pool

    database_url = get_database_url()
    if not database_url:
        # Return empty monthly aggregates for development when DATABASE_URL is not configured
        return []

    try:
        pool = await get_db_pool()
        if pool is None:
            # Return empty monthly aggregates if pool is not available
            return []
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    month,
                    records_ingested,
                    records_with_warnings
                FROM public.mv_ingestion_monthly
                ORDER BY month DESC
                LIMIT $1
            """, months)

            aggregates = []
            for row in rows:
                aggregates.append(MonthlyAggregate(
                    month=row["month"].isoformat() if row["month"] else "",
                    records_ingested=row["records_ingested"] or 0,
                    records_with_warnings=row["records_with_warnings"] or 0,
                ))
            return aggregates
    except Exception as e:
        error_msg = str(e)
        # Handle common async/event loop errors gracefully
        if "Event loop is closed" in error_msg or "another operation is in progress" in error_msg:
            return []
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching monthly aggregates: {error_msg}",
        )

