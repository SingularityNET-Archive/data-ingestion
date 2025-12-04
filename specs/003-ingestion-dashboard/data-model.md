# Data Model for Ingestion Dashboard

This file documents the entities and the fields the dashboard will surface (view-level model). These are derived from the spec's Key Entities and are intended for read-only views and API responses.

Entities

- MeetingSummaryView (view over MeetingSummary raw record)
  - id: uuid
  - source_id: text
  - source_name: text
  - workgroup: text
  - meeting_date: date
  - ingested_at: timestamptz
  - title: text
  - normalized_fields: jsonb
  - validation_warnings_count: integer
  - missing_fields: jsonb  # list of missing mandatory fields
  - provenance: jsonb      # { source_url, downloader_id, ingestion_run_id }
  - raw_json_ref: text     # optional pointer to raw payload storage

- IngestionRunView (summary)
  - id: uuid
  - started_at: timestamptz
  - finished_at: timestamptz
  - status: text (success | partial | failed)
  - records_processed: integer
  - records_failed: integer
  - duplicates_avoided: integer

- ErrorLogView
  - id: uuid
  - timestamp: timestamptz
  - source_url: text
  - error_type: text
  - message: text
  - ingestion_run_id: uuid
  - raw_payload_ref: text

- SourceView
  - id: uuid
  - name: text
  - type: text
  - last_polled_at: timestamptz

Notes

- The backend will expose these as JSON responses. For performant KPIs, create materialised views such as `mv_ingestion_monthly` and `mv_ingestion_kpis` containing aggregates used by the dashboard.
- Validation warnings are stored as JSON arrays of {code, field_path, message} in `normalized_fields` or `validation_warnings` column in the base table; the view should expose a `validation_warnings_count` and optionally the warnings themselves when requested by the detail endpoint.

## Materialized View Maintenance

The dashboard relies on materialized views for performant KPI queries. These views should be refreshed periodically to ensure data accuracy.

### Refresh Schedule

Materialized views should be refreshed every 3-5 minutes to maintain the 5-minute data latency SLA. This can be done via:

1. **Cron Job** (recommended for production):
   ```bash
   # Refresh every 3 minutes
   */3 * * * * /path/to/backend/app/db/refresh_materialized_views.sh
   ```

2. **PostgreSQL pg_cron extension** (if available):
   ```sql
   SELECT cron.schedule(
     'refresh-dashboard-views',
     '*/3 * * * *',
     $$REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_ingestion_kpis;
       REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_ingestion_monthly;$$
   );
   ```

3. **Application-level scheduler** (using APScheduler or similar):
   ```python
   from apscheduler.schedulers.asyncio import AsyncIOScheduler
   from backend.app.db.connection import get_db_pool
   
   async def refresh_views():
       pool = await get_db_pool()
       async with pool.acquire() as conn:
           await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_ingestion_kpis")
           await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_ingestion_monthly")
   
   scheduler = AsyncIOScheduler()
   scheduler.add_job(refresh_views, 'interval', minutes=3)
   scheduler.start()
   ```

### Refresh Script

A shell script is provided at `backend/app/db/refresh_materialized_views.sh` for manual or cron-based refresh:

```bash
#!/bin/bash
# Refresh materialized views for dashboard KPIs

DATABASE_URL="${DATABASE_URL:-postgresql://user:password@localhost:5432/meeting_summaries}"

psql "$DATABASE_URL" -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_ingestion_kpis;"
psql "$DATABASE_URL" -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_ingestion_monthly;"
```

**Note**: `REFRESH MATERIALIZED VIEW CONCURRENTLY` requires unique indexes on the materialized views. If concurrent refresh fails, use `REFRESH MATERIALIZED VIEW` (without CONCURRENTLY) which locks the view during refresh.

### Monitoring Refresh Status

To check when views were last refreshed:

```sql
SELECT schemaname, matviewname, last_refresh 
FROM pg_matviews 
WHERE matviewname IN ('mv_ingestion_kpis', 'mv_ingestion_monthly');
```
