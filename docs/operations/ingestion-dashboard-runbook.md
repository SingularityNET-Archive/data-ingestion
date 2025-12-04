# Ingestion Dashboard Runbook

**Last Updated**: 2025-12-04  
**Service**: Ingestion Dashboard (Phase 003)

## Overview

The Ingestion Dashboard provides operational visibility into the data ingestion pipeline. It consists of:
- **Backend**: FastAPI service (Python) on port 8000
- **Frontend**: React SPA served via nginx on port 3000
- **Database**: PostgreSQL/Supabase (read-only views)

## Health Checks

### Backend Health
```bash
curl http://localhost:8000/healthz
# Expected: {"status":"ok"}
```

### Frontend Health
```bash
curl http://localhost:3000
# Expected: HTML response (200 OK)
```

### Database Connectivity
```bash
psql $DATABASE_URL -c "SELECT 1;"
# Expected: Returns 1
```

## Common Issues & Solutions

### Issue: Dashboard shows "No data" or empty KPIs

**Symptoms**: Dashboard loads but shows zero values for all KPIs

**Diagnosis**:
1. Check if materialized views exist:
   ```sql
   SELECT matviewname FROM pg_matviews 
   WHERE matviewname IN ('mv_ingestion_kpis', 'mv_ingestion_monthly');
   ```

2. Check if views are populated:
   ```sql
   SELECT * FROM public.mv_ingestion_kpis;
   ```

**Solution**:
1. Create views if missing:
   ```bash
   ./scripts/setup_dashboard_dev_db.sh
   ```

2. Refresh materialized views:
   ```bash
   ./backend/app/db/refresh_materialized_views.sh
   ```

3. Verify base tables have data:
   ```sql
   SELECT COUNT(*) FROM meetings;
   ```

### Issue: "DATABASE_URL not configured" error

**Symptoms**: API returns 500 errors, logs show "DATABASE_URL not configured"

**Solution**:
1. Verify `.env` file exists and contains `DATABASE_URL`
2. Check environment variables are loaded:
   ```bash
   echo $DATABASE_URL
   ```
3. Restart the backend service

### Issue: Materialized views are stale

**Symptoms**: KPIs show outdated data

**Solution**:
1. Manually refresh views:
   ```bash
   ./backend/app/db/refresh_materialized_views.sh
   ```

2. Check refresh schedule (should run every 3-5 minutes):
   ```bash
   crontab -l | grep refresh_materialized_views
   ```

3. If using pg_cron, check scheduled jobs:
   ```sql
   SELECT * FROM cron.job WHERE jobname = 'refresh-dashboard-views';
   ```

### Issue: Frontend can't connect to backend API

**Symptoms**: Frontend shows "Failed to load" errors, network requests fail

**Diagnosis**:
1. Check backend is running:
   ```bash
   curl http://localhost:8000/healthz
   ```

2. Check CORS configuration in `backend/app/main.py`

3. Check browser console for CORS errors

**Solution**:
1. Verify backend is running on port 8000
2. Check `REACT_APP_API_URL` environment variable matches backend URL
3. Verify CORS allows frontend origin (not `*` in production)

### Issue: Authentication failures

**Symptoms**: API returns 401 Unauthorized errors

**Diagnosis**:
1. Check JWT_SECRET is set:
   ```bash
   echo $JWT_SECRET
   ```

2. Verify token is being sent in Authorization header

**Solution**:
1. Ensure `JWT_SECRET` is configured in environment
2. Verify token format: `Authorization: Bearer <token>`
3. Check token hasn't expired
4. For local dev, set `DEV_AUTH_BYPASS=true` (never in production!)

### Issue: Export fails for large datasets

**Symptoms**: Export returns 413 error or times out

**Solution**:
1. Apply additional filters to reduce result set size
2. Implement async export using `export_manager.py` for >10k rows
3. Check export file storage has sufficient space

## Monitoring

### Key Metrics to Monitor

1. **API Response Times**
   - KPI endpoint: < 500ms
   - Meetings list: < 1s
   - Export: < 10s (for <10k rows)

2. **Error Rates**
   - 4xx errors: < 1%
   - 5xx errors: < 0.1%

3. **Database Performance**
   - Materialized view refresh time: < 5s
   - Query execution time: < 100ms (typical queries)

4. **Resource Usage**
   - Backend memory: Monitor for leaks
   - Database connections: Stay within pool limits

### Log Monitoring

Monitor logs for:
- Authentication failures (potential security issues)
- Database connection errors
- Slow queries (>1s)
- Export failures

## Maintenance Tasks

### Daily
- [ ] Check dashboard health endpoints
- [ ] Review error logs for anomalies
- [ ] Verify materialized views are refreshing

### Weekly
- [ ] Review export file storage usage
- [ ] Check for stale export jobs
- [ ] Review security logs

### Monthly
- [ ] Update dependencies (security patches)
- [ ] Review and rotate secrets
- [ ] Performance optimization review

## Backup & Recovery

### Database Views
Views are defined in SQL files and can be recreated:
- `backend/app/db/views.sql`
- `backend/app/db/materialized_views.sql`

### Configuration
- Environment variables should be backed up securely
- `.env.example` documents required variables

### Recovery Procedure
1. Restore database from backup (if needed)
2. Recreate views:
   ```bash
   ./scripts/setup_dashboard_dev_db.sh
   ```
3. Restart services
4. Verify health checks pass

## Escalation

### When to Escalate

- **Critical**: Dashboard completely unavailable (>5 minutes)
- **High**: Data showing as stale (>15 minutes old)
- **Medium**: Intermittent errors affecting >10% of requests
- **Low**: Minor UI issues or non-critical features

### Contact Information

- **On-Call Engineer**: [Contact Info]
- **Database Admin**: [Contact Info]
- **DevOps Team**: [Contact Info]

## Appendix

### Useful Commands

```bash
# Refresh materialized views
./backend/app/db/refresh_materialized_views.sh

# Check view refresh status
psql $DATABASE_URL -c "SELECT matviewname, last_refresh FROM pg_matviews;"

# View recent errors
psql $DATABASE_URL -c "SELECT * FROM error_log_view ORDER BY timestamp DESC LIMIT 10;"

# Check ingestion runs
psql $DATABASE_URL -c "SELECT * FROM ingestion_run_view ORDER BY started_at DESC LIMIT 5;"
```

### Log Locations

- **Backend logs**: stdout/stderr (container logs or systemd journal)
- **Frontend logs**: Browser console
- **Database logs**: PostgreSQL log files

### Configuration Files

- Backend: `backend/app/main.py`, `backend/app/api/*.py`
- Frontend: `frontend/web/src/`
- Database: `backend/app/db/views.sql`, `backend/app/db/materialized_views.sql`
- Deployment: `deploy/dashboard/docker-compose.yml`

