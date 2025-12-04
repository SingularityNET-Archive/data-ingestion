#!/usr/bin/env bash
set -euo pipefail

# Refresh materialized views used by the ingestion dashboard.
# Usage: DATABASE_URL=postgresql://user:pass@host:port/dbname ./refresh_materialized_views.sh

if [ -z "${DATABASE_URL:-}" ]; then
  echo "Error: DATABASE_URL must be set (export DATABASE_URL=... )" >&2
  exit 1
fi

echo "Refreshing materialized view: mv_ingestion_kpis"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 --quiet -c "REFRESH MATERIALIZED VIEW public.mv_ingestion_kpis;"

echo "Refreshing materialized view: mv_ingestion_monthly"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 --quiet -c "REFRESH MATERIALIZED VIEW public.mv_ingestion_monthly;"

echo "Materialized views refreshed"
