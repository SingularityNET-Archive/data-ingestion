# Operations Runbook

This runbook provides step-by-step procedures for operating the meeting summaries ingestion pipeline in production.

## Overview

The ingestion pipeline downloads meeting summary JSON data from GitHub URLs, validates structure, and stores it in a PostgreSQL database. The system is designed to be idempotent and can be safely re-run.

## Prerequisites

- Database connection string (`DATABASE_URL`)
- Network access to GitHub raw content URLs
- Python 3.8+ or GitHub Actions workflow runtime
- Database schema deployed and up-to-date

## Regular Operations

### Running Ingestion

**Standard Run:**
```bash
python -m src.cli.ingest
```

**With Custom URLs:**
```bash
python -m src.cli.ingest \
  https://example.com/data1.json \
  https://example.com/data2.json
```

**Dry Run (Validate Without Inserting):**
```bash
python -m src.cli.ingest --dry-run
```

**Verbose Logging:**
```bash
python -m src.cli.ingest --verbose
```

### GitHub Actions Execution

**Workflow is Already Configured:**
The GitHub Actions workflow (`.github/workflows/ingest-meetings.yml`) is pre-configured and ready to use.

**Manual Trigger:**
1. Go to GitHub repository → **Actions** tab
2. Select **Ingest Meeting Summaries** workflow
3. Click **Run workflow** → **Run workflow**

**Scheduled Execution:**
- Workflow runs automatically daily at 2 AM UTC
- No manual intervention needed
- Check **Actions** tab to view execution history

**Configure Secrets:**
1. Go to repository → **Settings** → **Secrets and variables** → **Actions**
2. Add `SUPABASE_DATABASE_URL` secret with your Supabase connection string
3. Workflow will automatically use this secret

## Monitoring Ingestion

### Check Ingestion Status

**View Recent Logs:**
```bash
# If using JSON logs
tail -f logs.json | jq '.'

# If using text logs
tail -f logs.txt
```

**Check Database Record Counts:**
```sql
SELECT 
  (SELECT COUNT(*) FROM workgroups) as workgroups,
  (SELECT COUNT(*) FROM meetings) as meetings,
  (SELECT COUNT(*) FROM agenda_items) as agenda_items,
  (SELECT COUNT(*) FROM action_items) as action_items,
  (SELECT COUNT(*) FROM decision_items) as decision_items,
  (SELECT COUNT(*) FROM discussion_points) as discussion_points;
```

### Verify Data Integrity

**Check for Missing Workgroups:**
```sql
SELECT DISTINCT m.workgroup_id 
FROM meetings m 
LEFT JOIN workgroups w ON m.workgroup_id = w.id 
WHERE w.id IS NULL;
```

**Check for Orphaned Records:**
```sql
-- Orphaned agenda items
SELECT COUNT(*) FROM agenda_items a
LEFT JOIN meetings m ON a.meeting_id = m.id
WHERE m.id IS NULL;

-- Orphaned action items
SELECT COUNT(*) FROM action_items a
LEFT JOIN agenda_items ai ON a.agenda_item_id = ai.id
WHERE ai.id IS NULL;
```

**Verify JSON Preservation:**
```sql
SELECT id, date, raw_json IS NOT NULL as has_raw_json
FROM meetings
LIMIT 10;
```

## Handling Failures

### Source Download Failure

**Symptom:** One or more sources fail to download

**Action:**
1. Check logs for specific error (network, HTTP status, timeout)
2. Verify URL is accessible: `curl -I <failed-url>`
3. Check network connectivity from deployment environment
4. Re-run ingestion (will retry failed sources)

**Recovery:**
- Ingestion continues with remaining sources
- Failed sources can be re-run individually
- No data loss for successfully processed sources

### Validation Failure

**Symptom:** Structure validation fails for a source

**Action:**
1. Review validation errors in logs
2. Inspect JSON structure: `curl <url> | jq '.[0] | keys'`
3. Check if source format has changed
4. Contact data source maintainer if structure changed

**Recovery:**
- Failed source is skipped
- Other sources continue processing
- Can use `--skip-validation` for testing (not recommended)

### Database Error

**Symptom:** Database connection or insertion fails

**Action:**
1. Check database connectivity: `psql "$DATABASE_URL" -c "SELECT 1;"`
2. Verify database schema is up-to-date
3. Check database logs for errors
4. Verify user permissions

**Recovery:**
1. Fix database issue
2. Re-run ingestion (idempotent, will update existing records)
3. Verify no duplicates were created

### Partial Ingestion

**Symptom:** Ingestion stops partway through

**Action:**
1. Check logs for error that caused stop
2. Verify how many records were processed
3. Fix underlying issue
4. Re-run ingestion (will continue from where it stopped)

**Recovery:**
- Re-run ingestion (UPSERT ensures no duplicates)
- System processes remaining records
- No manual cleanup needed

## Scheduled Operations

### Daily Ingestion

**Recommended Schedule:** Daily or as new data becomes available

**Procedure:**
1. Set up cron job or scheduled task
2. Run ingestion: `python -m src.cli.ingest`
3. Monitor logs for completion
4. Verify record counts increased

**Cron Example:**
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/data-ingestion && /usr/bin/python3 -m src.cli.ingest >> /var/log/ingestion.log 2>&1
```

### Weekly Verification

**Procedure:**
1. Run dry-run to validate data: `python -m src.cli.ingest --dry-run`
2. Check data integrity queries (see Monitoring section)
3. Review error logs for patterns
4. Verify performance metrics

### Monthly Maintenance

**Procedure:**
1. Review and archive old logs
2. Check database storage usage
3. Verify database indexes are optimal
4. Review and update documentation
5. Test disaster recovery procedures

## Performance Optimization

### Database Optimization

**Check Index Usage:**
```sql
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

**Analyze Query Performance:**
```sql
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

**Vacuum and Analyze:**
```sql
VACUUM ANALYZE meetings;
VACUUM ANALYZE workgroups;
```

### Connection Pool Tuning

If experiencing connection issues, adjust pool settings in `src/db/connection.py`:
- `min_size`: Minimum connections in pool
- `max_size`: Maximum connections in pool
- `max_queries`: Queries per connection before recycling

## Backup and Recovery

### Database Backup

**Create Backup:**
```bash
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d).sql
```

**Restore Backup:**
```bash
psql "$DATABASE_URL" < backup_YYYYMMDD.sql
```

### Data Recovery

**From Raw JSON:**
All original JSON is preserved in `raw_json` columns, allowing full data recovery:
```sql
SELECT raw_json FROM meetings WHERE id = '<meeting-id>';
```

**Re-ingest from Source:**
Simply re-run ingestion - UPSERT ensures data is updated without duplicates.

## Emergency Procedures

### Complete System Failure

1. **Assess Impact:** Check what data was last successfully ingested
2. **Restore Database:** If backup available, restore from backup
3. **Re-run Ingestion:** Process all sources to restore data
4. **Verify Integrity:** Run data integrity checks

### Data Corruption

1. **Identify Corrupted Records:** Query for NULL in required fields
2. **Extract Raw JSON:** Use `raw_json` column to recover original data
3. **Re-ingest:** Re-run ingestion for affected sources
4. **Verify Fix:** Check data integrity queries

### Performance Degradation

1. **Check Database Load:** Monitor CPU, memory, disk I/O
2. **Review Slow Queries:** Use `pg_stat_statements`
3. **Optimize Indexes:** Ensure all indexes are created and used
4. **Scale Resources:** If needed, increase database resources

## Escalation

If issues cannot be resolved using this runbook:

1. Review `TROUBLESHOOTING.md` for detailed diagnosis
2. Check logs for specific error messages
3. Consult `specs/001-meeting-summaries-ingestion/spec.md` for expected behavior
4. Review test cases for examples of correct operation

