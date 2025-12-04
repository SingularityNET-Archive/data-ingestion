#!/bin/bash
# Database setup script for meeting summaries ingestion pipeline
# Creates database, runs migrations, and verifies schema

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
SCHEMA_FILE="${SCHEMA_FILE:-scripts/setup_db.sql}"

echo -e "${GREEN}Meeting Summaries Database Setup${NC}"
echo "=================================="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql command not found. Please install PostgreSQL client tools.${NC}"
    exit 1
fi

# Check if schema file exists
if [ ! -f "$SCHEMA_FILE" ]; then
    echo -e "${RED}Error: Schema file not found: $SCHEMA_FILE${NC}"
    exit 1
fi

# Create database if it doesn't exist
echo -e "${YELLOW}Creating database (if it doesn't exist)...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tc \
    "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | \
    grep -q 1 || \
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c \
    "CREATE DATABASE $DB_NAME"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database '$DB_NAME' ready${NC}"
else
    echo -e "${RED}Failed to create database${NC}"
    exit 1
fi

# Run migrations
echo -e "${YELLOW}Running schema migrations...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SCHEMA_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Schema migration completed${NC}"
else
    echo -e "${RED}Schema migration failed${NC}"
    exit 1
fi

# Verify schema
echo -e "${YELLOW}Verifying schema...${NC}"
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tc \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('workgroups', 'meetings', 'agenda_items', 'action_items', 'decision_items', 'discussion_points')")

if [ "$TABLE_COUNT" -eq 6 ]; then
    echo -e "${GREEN}Schema verification passed: All 6 tables exist${NC}"
else
    echo -e "${RED}Schema verification failed: Expected 6 tables, found $TABLE_COUNT${NC}"
    exit 1
fi

# Check UPSERT functions
FUNCTION_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tc \
    "SELECT COUNT(*) FROM pg_proc WHERE proname LIKE 'upsert_%' AND proname IN ('upsert_workgroup', 'upsert_meeting', 'upsert_agenda_item', 'upsert_action_item', 'upsert_decision_item', 'upsert_discussion_point')")

if [ "$FUNCTION_COUNT" -eq 6 ]; then
    echo -e "${GREEN}UPSERT functions verification passed: All 6 functions exist${NC}"
else
    echo -e "${YELLOW}UPSERT functions verification: Found $FUNCTION_COUNT functions (expected 6)${NC}"
fi

echo ""
echo -e "${GREEN}Database setup completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Set DATABASE_URL environment variable:"
echo "   export DATABASE_URL=postgresql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
echo "2. Run ingestion:"
echo "   python -m src.cli.ingest"










