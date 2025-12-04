# Production Troubleshooting Guide

This guide helps diagnose and resolve common issues when running the meeting summaries ingestion pipeline in production.

## Common Issues

### Database Connection Failures

**Symptoms:**
- Error: `Failed to connect to database`
- Error: `connection refused` or `timeout`

**Diagnosis:**
```bash
# Test database connectivity
psql "$DATABASE_URL" -c "SELECT version();"

# Check network connectivity
ping <database-host>
```

**Solutions:**
1. Verify `DATABASE_URL` is correctly formatted: `postgresql://user:password@host:port/database`
2. Check database is accessible from deployment environment (firewall rules, network policies)
3. Verify database credentials are correct
4. Check if database requires SSL/TLS (add `?sslmode=require` to connection string)
5. Verify database user has necessary permissions (INSERT, UPDATE, SELECT, CREATE)

### JSON Download Failures

**Symptoms:**
- Error: `Failed to download JSON from URL`
- Error: `HTTP 404` or `HTTP 403`
- Timeout errors

**Diagnosis:**
```bash
# Test URL accessibility
curl -I https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2025/meeting-summaries-array.json

# Check DNS resolution
nslookup raw.githubusercontent.com
```

**Solutions:**
1. Verify GitHub URLs are accessible from deployment environment
2. Check network firewall rules allow outbound HTTPS connections
3. Verify URLs haven't changed (check GitHub repository)
4. Check for rate limiting (GitHub may throttle requests)
5. Add retry logic or use proxy if behind corporate firewall

### Structure Validation Failures

**Symptoms:**
- Error: `Structure validation failed`
- Error: `Missing required field: workgroup`
- Error: `Invalid JSON structure`

**Diagnosis:**
```bash
# Download and inspect JSON structure
curl https://raw.githubusercontent.com/.../meeting-summaries-array.json | jq '.[0] | keys'

# Check for required fields
curl https://raw.githubusercontent.com/.../meeting-summaries-array.json | jq '.[0] | {workgroup, workgroup_id, meetingInfo, agendaItems, tags, type}'
```

**Solutions:**
1. Verify JSON structure matches expected schema (see `specs/001-meeting-summaries-ingestion/data-model.md`)
2. Check if source JSON format has changed
3. Review validation errors in logs for specific missing fields
4. Use `--skip-validation` flag only for testing (not recommended for production)

### Data Insertion Failures

**Symptoms:**
- Error: `Failed to insert record`
- Error: `Foreign key constraint violation`
- Error: `Duplicate key violation`

**Diagnosis:**
```sql
-- Check for missing workgroups
SELECT DISTINCT workgroup_id FROM meetings WHERE workgroup_id NOT IN (SELECT id FROM workgroups);

-- Check for duplicate records
SELECT id, COUNT(*) FROM meetings GROUP BY id HAVING COUNT(*) > 1;
```

**Solutions:**
1. Verify database schema is up-to-date (run migrations)
2. Check referential integrity (workgroups must exist before meetings)
3. Verify UPSERT functions are working correctly
4. Check for constraint violations in logs
5. Ensure database has sufficient storage space

### Performance Issues

**Symptoms:**
- Ingestion takes longer than 10 minutes
- High database connection usage
- Memory errors

**Diagnosis:**
```bash
# Monitor database connections
psql "$DATABASE_URL" -c "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();"

# Check database performance
psql "$DATABASE_URL" -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

**Solutions:**
1. Verify database indexes are created (especially GIN indexes on JSONB columns)
2. Check database connection pool settings
3. Monitor database resource usage (CPU, memory, disk I/O)
4. Consider batch processing for very large datasets
5. Optimize database queries if needed

### Logging Issues

**Symptoms:**
- No logs appearing
- Logs not in expected format
- Missing error details

**Diagnosis:**
```bash
# Check environment variables
env | grep -E "(LOG_LEVEL|LOG_FORMAT)"

# Test logging
python -m src.cli.ingest --dry-run --verbose
```

**Solutions:**
1. Verify `LOG_LEVEL` is set correctly (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
2. Check `LOG_FORMAT` is set to `json` or `text` as needed
3. Ensure logs are being captured (stdout/stderr redirection)
4. Check log aggregation system configuration (if using)

## Error Recovery Procedures

### Partial Ingestion Recovery

If ingestion fails partway through:

1. **Check what was ingested:**
   ```sql
   SELECT COUNT(*) FROM meetings;
   SELECT COUNT(*) FROM workgroups;
   ```

2. **Re-run ingestion** (idempotent, will update existing records):
   ```bash
   python -m src.cli.ingest
   ```

3. **Verify no duplicates:**
   ```sql
   SELECT id, COUNT(*) FROM meetings GROUP BY id HAVING COUNT(*) > 1;
   ```

### Database Schema Issues

If schema is out of date:

1. **Backup database** (if possible)
2. **Run migrations:**
   ```bash
   psql "$DATABASE_URL" -f scripts/setup_db.sql
   ```
3. **Verify schema:**
   ```sql
   SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
   ```

### Corrupted Data Recovery

If data corruption is suspected:

1. **Check raw JSON is preserved:**
   ```sql
   SELECT id, raw_json FROM meetings LIMIT 1;
   ```

2. **Re-ingest from source** (UPSERT will update records)

3. **Verify data integrity:**
   ```sql
   -- Check for NULL in required fields
   SELECT COUNT(*) FROM meetings WHERE workgroup_id IS NULL;
   SELECT COUNT(*) FROM meetings WHERE date IS NULL;
   ```

## Monitoring Recommendations

### Key Metrics to Monitor

1. **Ingestion Success Rate**
   - Track `sources_processed` vs `sources_failed`
   - Alert if failure rate > 5%

2. **Record Counts**
   - Monitor total records ingested per run
   - Alert if count drops significantly

3. **Processing Time**
   - Track ingestion duration
   - Alert if exceeds 15 minutes (10-minute goal + buffer)

4. **Database Health**
   - Monitor connection pool usage
   - Track query performance
   - Monitor disk space

5. **Error Rates**
   - Track validation errors
   - Monitor database errors
   - Alert on repeated failures

### Log Analysis

Structured JSON logs can be analyzed with tools like:
- `jq` for command-line analysis
- ELK stack (Elasticsearch, Logstash, Kibana)
- Cloud logging services (CloudWatch, Stackdriver, etc.)

Example log queries:
```bash
# Find all errors
jq 'select(.level == "ERROR")' < logs.json

# Find failed sources
jq 'select(.event == "source_processing_failed")' < logs.json

# Count records by source
jq '[.[] | select(.source_url) | .source_url] | group_by(.) | map({url: .[0], count: length})' < logs.json
```

## Getting Help

If issues persist:

1. Check logs for detailed error messages
2. Review `production-checklist.md` for configuration verification
3. Consult `specs/001-meeting-summaries-ingestion/spec.md` for expected behavior
4. Review test cases in `tests/` for examples of correct usage





