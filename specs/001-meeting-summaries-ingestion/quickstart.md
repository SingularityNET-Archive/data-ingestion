# Quickstart Guide: Meeting Summaries Ingestion Pipeline

**Date**: 2025-11-30  
**Feature**: 001-meeting-summaries-ingestion

## Overview

This guide provides step-by-step instructions for setting up and running the meeting summaries ingestion pipeline locally and deploying it to Supabase as a containerized job.

---

## Prerequisites

### Local Development

- **Python 3.8+**: Check with `python3 --version`
- **PostgreSQL 12+**: Local PostgreSQL instance or Supabase local development
- **pip**: Python package manager
- **Git**: For cloning repository (if applicable)

### Containerized Deployment

- **Docker**: Version 20.10+ (`docker --version`)
- **Docker Compose**: Optional, for local testing (`docker-compose --version`)
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

## Containerized Deployment to Supabase

### Step 1: Build Docker Image

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY cli/ ./cli/

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "-m", "cli.ingest"]
```

Build the image:

```bash
docker build -t meeting-summaries-ingestion:latest .
```

### Step 2: Test Container Locally

```bash
# Run container with environment variables
docker run --rm \
  -e DATABASE_URL="postgresql://user:password@host:5432/database" \
  -e LOG_FORMAT=json \
  meeting-summaries-ingestion:latest

# Or use docker-compose (create docker-compose.yml):
docker-compose up
```

**Example `docker-compose.yml`**:

```yaml
version: '3.8'

services:
  ingestion:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - LOG_FORMAT=json
      - LOG_LEVEL=INFO
    restart: "no"
```

### Step 3: Get Supabase Database Credentials

1. Log in to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Settings** → **Database**
4. Copy the connection string:
   - Format: `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
   - Or use individual values: Host, Port, Database, User, Password

### Step 4: Create Database Schema in Supabase

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

### Step 5: Push Docker Image to Registry

**Option A: Docker Hub**

```bash
# Tag image
docker tag meeting-summaries-ingestion:latest yourusername/meeting-summaries-ingestion:latest

# Push to Docker Hub
docker push yourusername/meeting-summaries-ingestion:latest
```

**Option B: GitHub Container Registry**

```bash
# Tag image
docker tag meeting-summaries-ingestion:latest ghcr.io/yourusername/meeting-summaries-ingestion:latest

# Push to GitHub Container Registry
docker push ghcr.io/yourusername/meeting-summaries-ingestion:latest
```

**Option C: Supabase Storage** (if supported)

Follow Supabase documentation for container image storage.

### Step 6: Deploy to Supabase

**Option A: Supabase Edge Functions** (if supported)

Create `supabase/functions/ingest-meetings/index.ts`:

```typescript
// Note: This is a placeholder - Supabase Edge Functions use Deno
// You may need to adapt the Python ingestion logic or use a different deployment method
```

**Option B: Scheduled Job via Supabase Cron** (if available)

1. Configure Supabase Cron job to run containerized ingestion
2. Set environment variables in Supabase dashboard
3. Schedule job (e.g., daily at 2 AM UTC)

**Option C: External Container Orchestration**

Deploy container to:
- **Google Cloud Run**: Serverless container execution
- **AWS ECS/Fargate**: Container orchestration
- **Azure Container Instances**: Serverless containers
- **Kubernetes**: If you have a cluster

**Example: Google Cloud Run**

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/[PROJECT-ID]/meeting-summaries-ingestion

# Deploy to Cloud Run
gcloud run deploy meeting-summaries-ingestion \
  --image gcr.io/[PROJECT-ID]/meeting-summaries-ingestion \
  --set-env-vars DATABASE_URL="[SUPABASE_CONNECTION_STRING]" \
  --region us-central1
```

### Step 7: Configure Environment Variables

Set environment variables in your deployment platform:

- `DATABASE_URL`: Supabase PostgreSQL connection string
- `LOG_FORMAT`: `json` (for structured logging)
- `LOG_LEVEL`: `INFO` or `DEBUG`

**Security**: Use secrets management (e.g., Supabase Secrets, Cloud Run secrets) for sensitive credentials.

### Step 8: Test Deployment

```bash
# Trigger ingestion manually (if on-demand execution)
# Or wait for scheduled execution

# Verify data in Supabase Dashboard
# Go to Table Editor → Check workgroups, meetings, etc.
```

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

### Container Deployment Issues

**Problem**: Container fails to connect to Supabase database

**Solution**: 
- Verify `DATABASE_URL` environment variable is set correctly
- Check Supabase firewall rules allow connections from your deployment platform
- Ensure database password is correct

**Problem**: Container runs but no data is inserted

**Solution**:
- Check container logs: `docker logs <container-id>`
- Verify schema exists in Supabase database
- Run with `--dry-run` flag to validate data without inserting

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

### Container Deployment

- Use multi-stage Docker builds to reduce image size
- Set appropriate resource limits (CPU, memory)
- Use connection pooling for database connections
- Consider parallel processing for multiple sources (if implemented)

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
- **Docker Documentation**: https://docs.docker.com/
- **Python asyncpg Documentation**: https://magicstack.github.io/asyncpg/
- **Pydantic Documentation**: https://docs.pydantic.dev/

---

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Review troubleshooting section above
3. Consult project documentation in `specs/001-meeting-summaries-ingestion/`



