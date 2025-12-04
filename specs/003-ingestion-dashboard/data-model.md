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
