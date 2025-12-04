"""KPI API endpoints for the ingestion dashboard."""
from fastapi import APIRouter, Depends, HTTPException
from .auth import require_read_only_or_admin, User

router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("")
async def get_kpis(
    current_user: User = Depends(require_read_only_or_admin),
):
    """Get operational KPIs for the ingestion dashboard.

    Returns a single-row mapping of KPI columns to values from the
    materialized view `mv_ingestion_kpis`. The endpoint uses an asyncpg
    pool for efficient connections.

    Requires: read-only or admin role

    Returns:
        dict: KPI metrics including:
            - total_ingested: Total number of meeting summaries ingested
            - sources_count: Number of distinct sources processed
            - success_rate: Success rate percentage (0-100)
            - duplicates_avoided: Total number of duplicates avoided via UPSERTs
            - last_run_timestamp: Timestamp of the last ingestion run
    """
    from ..db.connection import get_database_url, get_db_pool

    database_url = get_database_url()
    if not database_url:
        # Return empty KPIs for development when DATABASE_URL is not configured
        return {
            "total_ingested": 0,
            "sources_count": 0,
            "success_rate": 100.0,
            "duplicates_avoided": 0,
            "last_run_timestamp": None,
        }

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM public.mv_ingestion_kpis LIMIT 1;")
            if row is None:
                # Return empty KPIs if view is empty (no data yet)
                return {
                    "total_ingested": 0,
                    "sources_count": 0,
                    "success_rate": 100.0,
                    "duplicates_avoided": 0,
                    "last_run_timestamp": None,
                }
            # asyncpg Record is mappable to dict
            return dict(row)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching KPIs: {str(e)}",
        )

