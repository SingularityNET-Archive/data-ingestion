-- Read-only view definitions for the Ingestion Dashboard
-- These views are intended to be created against a development or read-replica database.
-- Adjust table names below to match the actual schema if different.

-- Meeting summary view
CREATE OR REPLACE VIEW public.meeting_summary_view AS
SELECT
  ms.id,
  ms.source_id,
  s.name AS source_name,
  ms.workgroup,
  ms.meeting_date,
  ms.ingested_at,
  ms.title,
  ms.normalized_fields,
  COALESCE(jsonb_array_length(ms.validation_warnings), 0) AS validation_warnings_count,
  ms.missing_fields,
  ms.provenance,
  ms.raw_json_reference
FROM meeting_summary ms
LEFT JOIN source s ON s.id = ms.source_id;

-- Ingestion run view
CREATE OR REPLACE VIEW public.ingestion_run_view AS
SELECT
  ir.id,
  ir.started_at,
  ir.finished_at,
  ir.status,
  ir.records_processed,
  ir.records_failed,
  ir.duplicates_avoided
FROM ingestion_run ir;

-- Error log view
CREATE OR REPLACE VIEW public.error_log_view AS
SELECT
  el.id,
  el.timestamp,
  el.source_url,
  el.error_type,
  el.message,
  el.ingestion_run_id,
  el.raw_payload_reference
FROM error_log el;
