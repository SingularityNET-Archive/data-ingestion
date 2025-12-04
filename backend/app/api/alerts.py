"""Alerts API endpoints for the ingestion dashboard."""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from .auth import require_read_only_or_admin, require_admin, User

router = APIRouter(prefix="/alerts", tags=["alerts"])


class Alert(BaseModel):
    """Alert model for recent failures and validation errors."""
    id: str
    timestamp: datetime
    source_url: Optional[str]
    error_type: str
    message: str
    ingestion_run_id: Optional[str]
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


class AlertAckRequest(BaseModel):
    """Request to acknowledge an alert."""
    alert_id: str


@router.get("", response_model=List[Alert])
async def list_alerts(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to include"),
    error_type: Optional[str] = Query(default=None, description="Filter by error type"),
    acknowledged: Optional[bool] = Query(default=None, description="Filter by acknowledged status"),
    current_user: User = Depends(require_read_only_or_admin),
):
    """List recent failures and schema-validation errors.

    Returns alerts from error logs within the specified time window.
    Admins can see all alerts; read-only users see unacknowledged alerts by default.

    Args:
        hours: Number of hours of history to include (default: 24, max: 168)
        error_type: Optional filter by error type
        acknowledged: Optional filter by acknowledged status (None = all for admins, unacknowledged for read-only)
        current_user: Current authenticated user

    Returns:
        List of alerts with error details and acknowledgment status
    """
    from ..db.connection import get_database_url, get_db_pool

    database_url = get_database_url()
    if not database_url:
        # Return empty alerts list for development when DATABASE_URL is not configured
        return []

    # Calculate time threshold
    threshold = datetime.utcnow() - timedelta(hours=hours)

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Build query
            query = """
                SELECT 
                    el.id,
                    el.timestamp,
                    el.source_url,
                    el.error_type,
                    el.message,
                    el.ingestion_run_id,
                    COALESCE(alert_acks.acknowledged, false) AS acknowledged,
                    alert_acks.acknowledged_at,
                    alert_acks.acknowledged_by
                FROM public.error_log_view el
                LEFT JOIN (
                    SELECT 
                        alert_id,
                        true AS acknowledged,
                        acknowledged_at,
                        acknowledged_by
                    FROM public.alert_acknowledgments
                ) alert_acks ON alert_acks.alert_id = el.id::text
                WHERE el.timestamp >= $1
            """
            params = [threshold]

            param_idx = 2
            if error_type:
                query += f" AND el.error_type = ${param_idx}"
                params.append(error_type)
                param_idx += 1

            # For read-only users, default to unacknowledged only
            if not current_user.is_admin() and acknowledged is None:
                query += f" AND COALESCE(alert_acks.acknowledged, false) = false"
            elif acknowledged is not None:
                query += f" AND COALESCE(alert_acks.acknowledged, false) = ${param_idx}"
                params.append(acknowledged)
                param_idx += 1

            query += " ORDER BY el.timestamp DESC LIMIT 100"

            rows = await conn.fetch(query, *params)
            alerts = []
            for row in rows:
                alerts.append(Alert(
                    id=str(row["id"]),
                    timestamp=row["timestamp"],
                    source_url=row["source_url"],
                    error_type=row["error_type"],
                    message=row["message"],
                    ingestion_run_id=str(row["ingestion_run_id"]) if row["ingestion_run_id"] else None,
                    acknowledged=row["acknowledged"],
                    acknowledged_at=row["acknowledged_at"],
                    acknowledged_by=row["acknowledged_by"],
                ))
            return alerts
    except Exception as e:
        error_msg = str(e)
        # Handle common async/event loop errors gracefully
        if "Event loop is closed" in error_msg or "another operation is in progress" in error_msg:
            return []
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching alerts: {error_msg}",
        )


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(require_admin),
):
    """Acknowledge an alert (admin only).

    Records that an admin has acknowledged and reviewed the alert.

    Args:
        alert_id: ID of the alert to acknowledge
        current_user: Current authenticated user (must be admin)

    Returns:
        Success message
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
            # Check if alert exists
            alert_row = await conn.fetchrow(
                "SELECT id FROM public.error_log_view WHERE id::text = $1",
                alert_id
            )
            if not alert_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Alert {alert_id} not found",
                )

            # Create acknowledgment table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS public.alert_acknowledgments (
                    alert_id TEXT PRIMARY KEY,
                    acknowledged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    acknowledged_by TEXT NOT NULL
                )
            """)

            # Upsert acknowledgment
            await conn.execute("""
                INSERT INTO public.alert_acknowledgments (alert_id, acknowledged_by)
                VALUES ($1, $2)
                ON CONFLICT (alert_id) DO UPDATE SET
                    acknowledged_at = NOW(),
                    acknowledged_by = EXCLUDED.acknowledged_by
            """, alert_id, current_user.user_id)

            return {"message": f"Alert {alert_id} acknowledged", "acknowledged_by": current_user.user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error acknowledging alert: {str(e)}",
        )

