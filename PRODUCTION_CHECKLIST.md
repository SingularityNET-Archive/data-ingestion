# Production Environment Configuration Checklist

This checklist ensures all required environment variables and configurations are set correctly before deploying to production.

## Required Environment Variables

### Database Configuration

- [ ] **DATABASE_URL** (Required)
  - Format: `postgresql://user:password@host:port/database`
  - Example: `postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres`
  - Must be accessible from the deployment environment
  - Verify connection with: `psql "$DATABASE_URL" -c "SELECT version();"`

- [ ] **DB_PASSWORD** (Optional, if password not in DATABASE_URL)
  - Database password if using separate password configuration
  - Only needed if password is not included in DATABASE_URL

### Logging Configuration

- [ ] **LOG_LEVEL** (Optional, default: `INFO`)
  - Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`
  - Use `DEBUG` for troubleshooting, `INFO` for production
  - Set to `WARNING` or `ERROR` for minimal logging

- [ ] **LOG_FORMAT** (Optional, default: `json`)
  - Valid values: `json`, `text`
  - Use `json` for structured logging (recommended for production)
  - Use `text` for human-readable logs

## Pre-Deployment Verification

### Database Schema

- [ ] Database schema is created and up-to-date
  - Run migration script: `psql "$DATABASE_URL" -f scripts/setup_db.sql`
  - Verify tables exist: `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';`
  - Expected tables: `workgroups`, `meetings`, `agenda_items`, `action_items`, `decision_items`, `discussion_points`

- [ ] Database indexes are created
  - Verify GIN indexes on JSONB columns
  - Verify foreign key indexes

### Network Access

- [ ] GitHub raw content URLs are accessible from deployment environment
  - Test URLs:
    - `https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2025/meeting-summaries-array.json`
    - `https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2024/meeting-summaries-array.json`
    - `https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2023/meeting-summaries-array.json`
    - `https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2022/meeting-summaries-array.json`

### GitHub Actions Configuration

- [ ] GitHub Actions workflow file exists (`.github/workflows/ingest-meetings.yml`)
  - Verify workflow file is present in repository
  - Check workflow syntax is valid

- [ ] GitHub Secrets are configured
  - Go to repository → Settings → Secrets and variables → Actions
  - Verify `SUPABASE_DATABASE_URL` secret is set
  - Secret should contain full Supabase connection string

- [ ] Workflow can be triggered manually
  - Go to Actions tab → Select workflow → Run workflow
  - Verify workflow starts successfully

## Production Deployment Steps

1. **Set Environment Variables**
   ```bash
   export DATABASE_URL="postgresql://user:password@host:port/database"
   export LOG_LEVEL="INFO"
   export LOG_FORMAT="json"
   ```

2. **Verify Database Connection**
   ```bash
   python -m src.cli.ingest --dry-run
   ```

3. **Run Initial Ingestion**
   ```bash
   python -m src.cli.ingest
   ```

4. **Verify Data Integrity**
   ```sql
   SELECT COUNT(*) FROM meetings;
   SELECT COUNT(*) FROM workgroups;
   SELECT COUNT(*) FROM agenda_items;
   ```

## Post-Deployment Verification

- [ ] Ingestion completes without errors
- [ ] All expected records are inserted (verify counts match expected)
- [ ] Logs are properly formatted and accessible
- [ ] Database queries execute efficiently
- [ ] Idempotent re-runs work correctly (no duplicates)

## Troubleshooting

If ingestion fails:

1. Check database connectivity: `psql "$DATABASE_URL" -c "SELECT 1;"`
2. Verify environment variables: `env | grep -E "(DATABASE|LOG_)"`
3. Check logs for detailed error messages
4. Verify network access to GitHub URLs
5. Check database permissions (user must have INSERT, UPDATE, SELECT permissions)

## Security Notes

- Never commit `.env` files to version control
- Use secure password management for production credentials
- Rotate database passwords regularly
- Use SSL/TLS for database connections in production
- Restrict network access to database from known IPs only

