# Quickstart Guide: Meeting Summaries Ingestion Pipeline

**Date**: 2025-11-30  
**Feature**: 001-meeting-summaries-ingestion

## Overview

This guide provides step-by-step instructions for setting up and running the meeting summaries ingestion pipeline locally and deploying it to Supabase using GitHub Actions.

---

## Prerequisites

### Local Development

- **Python 3.8+**: Check with `python3 --version`
- **PostgreSQL 12+**: Local PostgreSQL instance or Supabase local development
- **pip**: Python package manager
- **Git**: For cloning repository (if applicable)

### GitHub Actions Deployment

- **GitHub Account**: Access to GitHub repository
- **GitHub Actions**: Enabled in repository settings (enabled by default)
- **Supabase Account**: Access to Supabase project with PostgreSQL database

---

## Local Development Setup

### Step 1: Clone Repository and Navigate to Project

```bash
# If cloning from repository
git clone <repository-url>
cd data-ingestion

# Or navigate to existing project directory
cd /path/to/data-ingestion
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Or install individually:
pip install fastapi asyncpg httpx pydantic python-dotenv click
```

**Expected dependencies** (create `requirements.txt`):
```
fastapi>=0.104.0
asyncpg>=0.29.0
httpx>=0.25.0
pydantic>=2.5.0
python-dotenv>=1.0.0
click>=8.1.0
```

### Step 4: Set Up Database

#### Option A: Local PostgreSQL

```bash
# Create database
createdb meeting_summaries

# Or using psql:
psql -U postgres -c "CREATE DATABASE meeting_summaries;"
```

#### Option B: Supabase Local Development

```bash
# Install Supabase CLI (if not already installed)
npm install -g supabase

# Initialize Supabase (if not already done)
supabase init

# Start local Supabase
supabase start

# Note the database URL from output:
# postgresql://postgres:postgres@localhost:54322/postgres
```

### Step 5: Create Database Schema

```bash
# Run SQL schema creation script
psql -U postgres -d meeting_summaries -f contracts/sql-schema.md

# Or using Python script (if implemented):
python scripts/setup_db.py
```

**Note**: The SQL schema is defined in `contracts/sql-schema.md`. Extract the SQL DDL and execute it against your database.

### Step 6: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Database configuration
DATABASE_URL=postgresql://user:password@localhost:5432/meeting_summaries
# Or for Supabase:
# DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# Optional: Database password (if not in URL)
DB_PASSWORD=your_password_here

# Logging configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Security Note**: Never commit `.env` file to version control. Add `.env` to `.gitignore`.

### Step 7: Run Ingestion

```bash
# Basic usage (uses default URLs from spec)
python -m cli.ingest

# Specify custom URLs
python -m cli.ingest \
  https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2025/meeting-summaries-array.json \
  https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2024/meeting-summaries-array.json \
  https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2023/meeting-summaries-array.json \
  https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2022/meeting-summaries-array.json

# Dry run (validate without inserting)
python -m cli.ingest --dry-run

# Verbose logging
python -m cli.ingest --verbose
```

### Step 8: Verify Data

```bash
# Connect to database
psql -U postgres -d meeting_summaries

# Check workgroups
SELECT COUNT(*) FROM workgroups;

# Check meetings
SELECT COUNT(*) FROM meetings;

# Check agenda items
SELECT COUNT(*) FROM agenda_items;

# Sample query: Meetings by workgroup
SELECT w.name, COUNT(m.id) as meeting_count
FROM workgroups w
LEFT JOIN meetings m ON m.workgroup_id = w.id
GROUP BY w.name
ORDER BY meeting_count DESC;
```

---

## GitHub Actions Deployment to Supabase

### Step 1: Get Supabase Database Credentials

1. Log in to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Settings** → **Database**
4. Copy the connection string:
   - Format: `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
   - Or use individual values: Host, Port, Database, User, Password

### Step 2: Create Database Schema in Supabase

**Option A: Using Supabase SQL Editor**

1. Go to **SQL Editor** in Supabase Dashboard
2. Copy SQL DDL from `contracts/sql-schema.md`
3. Execute the SQL script

**Option B: Using psql**

```bash
# Connect to Supabase database
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# Execute schema creation
\i contracts/sql-schema.md
```

### Step 3: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secret:
   - **Name**: `SUPABASE_DATABASE_URL`
   - **Value**: Your Supabase connection string (from Step 1)
   - Format: `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`

### Step 4: Verify GitHub Actions Workflow

The GitHub Actions workflow is already configured in `.github/workflows/ingest-meetings.yml`. It:
- Runs daily at 2 AM UTC (automatically scheduled)
- Can be triggered manually from the Actions tab
- Installs Python dependencies
- Runs the ingestion pipeline
- Uploads logs as artifacts

**Workflow file location**: `.github/workflows/ingest-meetings.yml`

### Step 5: Test Deployment

1. **Trigger workflow manually**:
   - Go to **Actions** tab in GitHub repository
   - Select **Ingest Meeting Summaries** workflow
   - Click **Run workflow** → **Run workflow**

2. **Monitor execution**:
   - Watch the workflow run in real-time
   - Check logs for any errors
   - Download logs artifact if needed

3. **Verify data in Supabase**:
   - Go to Supabase Dashboard → **Table Editor**
   - Check `workgroups`, `meetings`, `agenda_items`, etc.
   - Verify records were inserted correctly

### Step 6: Verify Scheduled Execution

The workflow is configured to run daily at 2 AM UTC. To verify:
1. Wait for the scheduled time, or
2. Check the **Actions** tab the next day to see the automatic run
3. Review logs to ensure ingestion completed successfully

---

## Troubleshooting

### Local Development Issues

**Problem**: `ModuleNotFoundError: No module named 'asyncpg'`

**Solution**: Ensure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Problem**: `psycopg2.OperationalError: connection to server failed`

**Solution**: Check database connection string and ensure PostgreSQL is running:
```bash
# Test connection
psql $DATABASE_URL -c "SELECT version();"
```

**Problem**: `ValidationError: Invalid UUID format`

**Solution**: Check source JSON data. Invalid UUIDs will be logged and skipped. Review logs for details.

### GitHub Actions Deployment Issues

**Problem**: Workflow fails to connect to Supabase database

**Solution**: 
- Verify `SUPABASE_DATABASE_URL` secret is set correctly in GitHub repository settings
- Check the connection string format matches: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
- Ensure database password is correct and URL-encoded if it contains special characters
- Check Supabase firewall rules allow connections from GitHub Actions IPs (usually not restricted)

**Problem**: Workflow runs but no data is inserted

**Solution**:
- Check workflow logs in the Actions tab for detailed error messages
- Verify schema exists in Supabase database (run `scripts/setup_db.sql` if not done)
- Test locally with the same connection string to isolate issues
- Review logs artifact downloaded from workflow run

**Problem**: `Permission denied` errors

**Solution**: Ensure database user has necessary permissions:
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

---

## Performance Optimization

### Local Development

- Process records in batches to avoid memory issues
- Use connection pooling for database operations
- Enable verbose logging only when debugging

### GitHub Actions Deployment

- Workflow automatically uses GitHub-hosted runners (no infrastructure management needed)
- Default timeout is 15 minutes (configurable in workflow file)
- Logs are automatically captured and available as artifacts
- Workflow can be triggered manually or runs on schedule

---

## Next Steps

1. **Monitor ingestion**: Set up logging and monitoring for production deployments
2. **Schedule regular updates**: Configure cron jobs or scheduled tasks for periodic ingestion
3. **Data validation**: Implement additional validation rules as needed
4. **Performance tuning**: Optimize database queries and indexes based on usage patterns
5. **Error alerting**: Set up alerts for ingestion failures

---

## Additional Resources

- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Supabase Documentation**: https://supabase.com/docs
- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Python asyncpg Documentation**: https://magicstack.github.io/asyncpg/
- **Pydantic Documentation**: https://docs.pydantic.dev/

---

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Review troubleshooting section above
3. Consult project documentation in `specs/001-meeting-summaries-ingestion/`



