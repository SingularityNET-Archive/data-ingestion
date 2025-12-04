-- Adapted materialized views for KPI aggregates used by the dashboard
-- These are adapted to work with the actual database schema

-- KPI aggregates: single-row materialized view for fast dashboard queries
CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_ingestion_kpis AS
SELECT
  (SELECT COUNT(*) FROM public.meeting_summary_view) AS total_ingested,
  (SELECT COUNT(DISTINCT workgroup) FROM public.meeting_summary_view WHERE workgroup IS NOT NULL) AS sources_count,
  -- success rate computed from ingestion_run_view if records_processed > 0
  COALESCE(
    (1.0 - (SUM(ir.records_failed)::double precision / NULLIF(SUM(ir.records_processed),0))) * 100.0,
    100.0
  ) AS success_rate,
  (SELECT COALESCE(SUM(ir.duplicates_avoided),0) FROM public.ingestion_run_view ir) AS duplicates_avoided,
  (SELECT MAX(ir.finished_at) FROM public.ingestion_run_view ir) AS last_run_timestamp
FROM public.ingestion_run_view ir;

-- Monthly ingestion aggregates for time-series (ingestion volume per month)
CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_ingestion_monthly AS
SELECT
  date_trunc('month', ms.ingested_at) AS month,
  COUNT(*) AS records_ingested,
  SUM(CASE WHEN ms.validation_warnings_count > 0 THEN 1 ELSE 0 END) AS records_with_warnings
FROM public.meeting_summary_view ms
GROUP BY date_trunc('month', ms.ingested_at)
ORDER BY month;

