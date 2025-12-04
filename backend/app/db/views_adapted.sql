-- Adapted read-only view definitions for the Ingestion Dashboard
-- These views are adapted to match the actual database schema:
-- - meetings (not meeting_summary)
-- - ingestion_runs (not ingestion_run)
-- - workgroups table exists

-- Meeting summary view (adapted from meetings table)
CREATE OR REPLACE VIEW public.meeting_summary_view AS
SELECT
  m.id,
  NULL::uuid AS source_id,  -- No source table, use NULL
  NULL::text AS source_name,  -- No source table
  w.name AS workgroup,
  m.date AS meeting_date,
  m.created_at AS ingested_at,
  COALESCE(m.purpose, '') AS title,  -- Use purpose as title, or empty string
  jsonb_build_object(
    'type', m.type,
    'host', m.host,
    'documenter', m.documenter,
    'attendees', m.attendees,
    'purpose', m.purpose,
    'video_links', m.video_links
  ) AS normalized_fields,
  0 AS validation_warnings_count,  -- No validation warnings in current schema
  NULL::jsonb AS missing_fields,  -- No missing fields tracking
  jsonb_build_object(
    'source_url', NULL,  -- No source URL in current schema
    'downloader_id', NULL,
    'ingestion_run_id', NULL
  ) AS provenance,
  NULL::text AS raw_json_reference  -- raw_json is in the table itself
FROM meetings m
LEFT JOIN workgroups w ON w.id = m.workgroup_id;

-- Ingestion run view (adapted from ingestion_runs table)
CREATE OR REPLACE VIEW public.ingestion_run_view AS
SELECT
  ir.id,
  ir.processed_at AS started_at,  -- Use processed_at as started_at
  ir.processed_at AS finished_at,  -- Use processed_at as finished_at (no separate finished_at)
  ir.status,
  ir.record_count AS records_processed,  -- Use record_count as records_processed
  0 AS records_failed,  -- No records_failed in current schema
  0 AS duplicates_avoided  -- No duplicates_avoided in current schema
FROM ingestion_runs ir;

-- Error log view (create empty view since error_log table doesn't exist)
CREATE OR REPLACE VIEW public.error_log_view AS
SELECT
  gen_random_uuid()::text AS id,  -- Generate UUID for compatibility
  NOW() AS timestamp,
  NULL::text AS source_url,
  'info' AS error_type,
  'No error log table in current schema' AS message,
  NULL::uuid AS ingestion_run_id,
  NULL::text AS raw_payload_reference
WHERE FALSE;  -- Always returns no rows

