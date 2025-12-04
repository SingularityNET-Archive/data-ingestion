#!/bin/bash
# Database setup script for ingestion dashboard
# Creates read-only views and materialized views for the dashboard API
#
# Usage:
#   DATABASE_URL=postgresql://user:pass@host:port/dbname ./setup_dashboard_dev_db.sh
#   OR
#   DB_NAME=meeting_summaries DB_USER=postgres DB_HOST=localhost ./setup_dashboard_dev_db.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DB_NAME="${DB_NAME:-meeting_summaries}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Paths relative to repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VIEWS_FILE="$REPO_ROOT/backend/app/db/views.sql"
MATERIALIZED_VIEWS_FILE="$REPO_ROOT/backend/app/db/materialized_views.sql"

echo -e "${GREEN}Ingestion Dashboard Database Setup${NC}"
echo "=========================================="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Check if DATABASE_URL is set, otherwise construct from components
if [ -n "${DATABASE_URL:-}" ]; then
    echo -e "${YELLOW}Using DATABASE_URL environment variable${NC}"
    PSQL_CMD="psql \"$DATABASE_URL\""
else
    echo -e "${YELLOW}Using individual DB connection parameters${NC}"
    PSQL_CMD="psql -h \"$DB_HOST\" -p \"$DB_PORT\" -U \"$DB_USER\" -d \"$DB_NAME\""
fi

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql command not found. Please install PostgreSQL client tools.${NC}"
    exit 1
fi

# Check if view files exist
if [ ! -f "$VIEWS_FILE" ]; then
    echo -e "${RED}Error: Views file not found: $VIEWS_FILE${NC}"
    exit 1
fi

if [ ! -f "$MATERIALIZED_VIEWS_FILE" ]; then
    echo -e "${RED}Error: Materialized views file not found: $MATERIALIZED_VIEWS_FILE${NC}"
    exit 1
fi

# Test database connection
echo -e "${YELLOW}Testing database connection...${NC}"
if [ -n "${DATABASE_URL:-}" ]; then
    if ! psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${RED}Error: Cannot connect to database. Check DATABASE_URL.${NC}"
        exit 1
    fi
else
    if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${RED}Error: Cannot connect to database. Check connection parameters.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}Database connection successful${NC}"

# Create read-only views
echo -e "${YELLOW}Creating read-only views...${NC}"
if [ -n "${DATABASE_URL:-}" ]; then
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$VIEWS_FILE"
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$VIEWS_FILE"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Read-only views created${NC}"
else
    echo -e "${RED}Failed to create read-only views${NC}"
    exit 1
fi

# Create materialized views
echo -e "${YELLOW}Creating materialized views...${NC}"
if [ -n "${DATABASE_URL:-}" ]; then
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$MATERIALIZED_VIEWS_FILE"
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$MATERIALIZED_VIEWS_FILE"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Materialized views created${NC}"
else
    echo -e "${RED}Failed to create materialized views${NC}"
    exit 1
fi

# Refresh materialized views
echo -e "${YELLOW}Refreshing materialized views...${NC}"
if [ -n "${DATABASE_URL:-}" ]; then
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 --quiet -c "REFRESH MATERIALIZED VIEW public.mv_ingestion_kpis;" || true
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 --quiet -c "REFRESH MATERIALIZED VIEW public.mv_ingestion_monthly;" || true
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 --quiet -c "REFRESH MATERIALIZED VIEW public.mv_ingestion_kpis;" || true
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 --quiet -c "REFRESH MATERIALIZED VIEW public.mv_ingestion_monthly;" || true
fi
echo -e "${GREEN}Materialized views refreshed${NC}"

# Verify views
echo -e "${YELLOW}Verifying views...${NC}"
if [ -n "${DATABASE_URL:-}" ]; then
    VIEW_COUNT=$(psql "$DATABASE_URL" -tc \
        "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public' AND table_name IN ('meeting_summary_view', 'ingestion_run_view', 'error_log_view')")
    MV_COUNT=$(psql "$DATABASE_URL" -tc \
        "SELECT COUNT(*) FROM pg_matviews WHERE schemaname = 'public' AND matviewname IN ('mv_ingestion_kpis', 'mv_ingestion_monthly')")
else
    VIEW_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tc \
        "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public' AND table_name IN ('meeting_summary_view', 'ingestion_run_view', 'error_log_view')")
    MV_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tc \
        "SELECT COUNT(*) FROM pg_matviews WHERE schemaname = 'public' AND matviewname IN ('mv_ingestion_kpis', 'mv_ingestion_monthly')")
fi

if [ "$VIEW_COUNT" -eq 3 ]; then
    echo -e "${GREEN}Views verification passed: All 3 views exist${NC}"
else
    echo -e "${YELLOW}Views verification: Found $VIEW_COUNT views (expected 3)${NC}"
fi

if [ "$MV_COUNT" -eq 2 ]; then
    echo -e "${GREEN}Materialized views verification passed: All 2 materialized views exist${NC}"
else
    echo -e "${YELLOW}Materialized views verification: Found $MV_COUNT materialized views (expected 2)${NC}"
fi

echo ""
echo -e "${GREEN}Dashboard database setup completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Ensure DATABASE_URL is set:"
if [ -n "${DATABASE_URL:-}" ]; then
    echo "   export DATABASE_URL=$DATABASE_URL"
else
    echo "   export DATABASE_URL=postgresql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
fi
echo "2. For local development, set DEV_AUTH_BYPASS=true to bypass authentication:"
echo "   export DEV_AUTH_BYPASS=true"
echo "3. Start the dashboard backend:"
echo "   cd backend && python -m app.main"
echo "4. Schedule materialized view refreshes (recommended every 3-5 minutes):"
echo "   Add a cron job or use the refresh script:"
echo "   ./backend/app/db/refresh_materialized_views.sh"
echo ""
echo -e "${YELLOW}Note: The dashboard views expect the following tables:${NC}"
echo "  - meeting_summary (or adapt views.sql to match your schema)"
echo "  - source"
echo "  - ingestion_run"
echo "  - error_log"
echo ""
echo "If these tables don't exist, you may need to create them or adapt the views."

